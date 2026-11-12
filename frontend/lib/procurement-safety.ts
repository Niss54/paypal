/** Only this response proves the evidence gate rejected a capture request. */
export function isEvidenceGateRejection(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const response = error as { status?: number; detail?: { error?: string } };
  return response.status === 403 && response.detail?.error === "EvidenceGateBlocked";
}

/** A successful HTTP response alone does not establish completed capture. */
export function requireCompletedCapture(result: unknown): { capture_id: string; status: string } {
  const response = result as { capture?: { capture_id?: string; status?: string } } | null;
  const capture = response?.capture;
  if (!capture?.capture_id || capture.status !== "COMPLETED") {
    throw new Error("Capture is not confirmed complete. Inspect the payment status before retrying or exporting.");
  }
  return { capture_id: capture.capture_id, status: capture.status };
}
