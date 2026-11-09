"""Bounded document-upload endpoint backed by the asynchronous ingest queue."""

import os

from fastapi import APIRouter, HTTPException, Query, Request
try:
    from redis import Redis
    from rq import Queue
except ImportError:
    Redis = None  # type: ignore
    Queue = None  # type: ignore

from ingestion.workers.storage import get_object_store, safe_filename

router = APIRouter()

MAX_UPLOAD_BYTES = int(os.environ.get("INGEST_MAX_UPLOAD_BYTES", 50 * 1024 * 1024))


@router.post("/ingestion/documents", status_code=202)
async def enqueue_document(
    request: Request,
    filename: str = Query(min_length=1, max_length=200),
) -> dict:
    if Redis is None or Queue is None:
        raise HTTPException(
            status_code=503,
            detail={"error": "service_unavailable", "detail": "Ingestion queue dependencies (redis/rq) not installed in this environment."},
        )
    content = await request.body()
    if not content:
        raise HTTPException(
            status_code=422,
            detail={"error": "empty_document", "detail": "Document body is empty."},
        )
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "document_too_large",
                "detail": f"Document exceeds the {MAX_UPLOAD_BYTES}-byte limit.",
            },
        )
    try:
        from ingestion.workers.tasks import process_object

        store = get_object_store()
        reference = store.put_bytes(content, safe_filename(filename))
        queue = Queue(
            "kinetix-ingest",
            connection=Redis.from_url(
                os.environ.get("REDIS_URL", "redis://localhost:6379")
            ),
        )
        job = queue.enqueue(
            process_object,
            reference.to_dict(),
            job_id=f"ingest-{reference.sha256}",
        )
        return {
            "status": "queued",
            "job_id": job.id,
            "sha256": reference.sha256,
            "filename": reference.filename,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "ingestion_queue_failed", "detail": str(exc)},
        ) from exc
