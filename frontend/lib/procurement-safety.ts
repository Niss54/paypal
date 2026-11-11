/** Only this response proves the evidence gate rejected a capture request. */
export function isEvidenceGateRejection(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const response = error as { status?: number; detail?: { error?: string } };
  return response.status === 403 && response.detail?.error === "EvidenceGateBlocked";
}
