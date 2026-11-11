"""SQLAlchemy database engine and session management.

Supports PostgreSQL (AWS RDS) in production with automatic fallback to local
SQLite for zero-friction development and automated testing.
"""
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

REPO_ROOT = Path(__file__).resolve().parents[3]

def get_default_sqlite_path() -> Path:
    """Find the best writable location for SQLite in containerized environments."""
    for candidate in [REPO_ROOT / ".runtime", REPO_ROOT / "data", REPO_ROOT, Path("/tmp")]:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test_file = candidate / ".write_test"
            test_file.touch()
            test_file.unlink()
            return candidate / "kinetix_enterprise.db"
        except Exception:
            continue
    return REPO_ROOT / "kinetix_enterprise.db"

DEFAULT_SQLITE_PATH = get_default_sqlite_path()

def get_database_url() -> str:
    import sys
    if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv):
        return f"sqlite:///{DEFAULT_SQLITE_PATH}"
    url = os.environ.get("DATABASE_URL")
    if not url:
        return f"sqlite:///{DEFAULT_SQLITE_PATH}"
    # Normalize postgres URL scheme if necessary
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # Ensure driver compatibility between psycopg (v3) and psycopg2
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        try:
            import psycopg
        except ImportError:
            try:
                import psycopg2
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            except ImportError:
                pass
    return url

DATABASE_URL = get_database_url()

# SQLite requires check_same_thread=False for FastAPI multithreaded workers
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None):
    """Creates all registered database tables and applies non-destructive SQLite column migrations."""
    import backend.app.db.models  # noqa: F401 - ensure models are registered on Base
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)

    try:
        from sqlalchemy import inspect
        inspector = inspect(eng)
        if inspector.has_table("paypal_order_records"):
            existing_cols = {c["name"] for c in inspector.get_columns("paypal_order_records")}
            with eng.connect() as conn:
                if "requester_user_id" not in existing_cols:
                    conn.execute(text("ALTER TABLE paypal_order_records ADD COLUMN requester_user_id VARCHAR(128) DEFAULT 'kinetix-procurement-agent'"))
                if "approve_url" not in existing_cols:
                    conn.execute(text("ALTER TABLE paypal_order_records ADD COLUMN approve_url VARCHAR(512)"))
                if "is_simulated" not in existing_cols:
                    conn.execute(text("ALTER TABLE paypal_order_records ADD COLUMN is_simulated BOOLEAN DEFAULT 0"))
                if "site_id" not in existing_cols:
                    conn.execute(text("ALTER TABLE paypal_order_records ADD COLUMN site_id VARCHAR(64) DEFAULT 'plant-mumbai-01'"))
                if "organization_id" not in existing_cols:
                    conn.execute(text("ALTER TABLE paypal_order_records ADD COLUMN organization_id VARCHAR(64) DEFAULT 'kinetix-industrial'"))

                if inspector.has_table("completion_evidence_records"):
                    ev_cols = {c["name"] for c in inspector.get_columns("completion_evidence_records")}
                    if "order_id" not in ev_cols:
                        conn.execute(text("ALTER TABLE completion_evidence_records ADD COLUMN order_id VARCHAR(64)"))
                    if "file_content" not in ev_cols:
                        conn.execute(text("ALTER TABLE completion_evidence_records ADD COLUMN file_content TEXT"))
                    if "file_size_bytes" not in ev_cols:
                        conn.execute(text("ALTER TABLE completion_evidence_records ADD COLUMN file_size_bytes INTEGER DEFAULT 0"))
                    if "submitted_by" not in ev_cols:
                        conn.execute(text("ALTER TABLE completion_evidence_records ADD COLUMN submitted_by VARCHAR(128)"))
                    if "provenance_classification" not in ev_cols:
                        conn.execute(text("ALTER TABLE completion_evidence_records ADD COLUMN provenance_classification VARCHAR(64) DEFAULT 'SYNTHETIC_DEMO_FIXTURE'"))

                conn.commit()
    except Exception:
        pass
