import { describe, expect, it } from "vitest";
import { isEvidenceGateRejection, requireCompletedCapture } from "./procurement-safety";

describe("capture demonstration evidence", () => {
  it("recognizes only a server evidence-gate rejection", () => {
    expect(isEvidenceGateRejection({ status: 403, detail: { error: "EvidenceGateBlocked" } })).toBe(true);
  });
  it.each([
    new Error("Failed to fetch"),
    new Error("Unexpected: capture succeeded"),
    { status: 500, detail: { error: "EvidenceGateBlocked" } },
    { status: 403, detail: { error: "InsufficientRole" } },
    { status: 401 },
    null,
  ])("does not present an unrelated failure as a successful gate test", (error) => {
    expect(isEvidenceGateRejection(error)).toBe(false);
  });
});

describe("capture confirmation", () => {
  it.each([null, {}, { capture: { status: "COMPLETED" } }, { capture: { capture_id: "CAP-1", status: "PENDING" } }])("rejects an unconfirmed result", result => {
    expect(() => requireCompletedCapture(result)).toThrow("not confirmed complete");
  });
  it("retains the returned capture identifier", () => {
    expect(requireCompletedCapture({ capture: { capture_id: "CAP-1", status: "COMPLETED" } }).capture_id).toBe("CAP-1");
  });
});
