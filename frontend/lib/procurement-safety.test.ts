import { describe, expect, it } from "vitest";
import { isEvidenceGateRejection } from "./procurement-safety";

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
