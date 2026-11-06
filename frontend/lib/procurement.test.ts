import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  evaluateProcurementQuote,
  createPayPalOrder,
  approvePayPalOrder,
  authorizePayPalOrder,
  submitCompletionEvidence,
  capturePayPalOrder,
  computeSha256,
} from "./api";

describe("PayPal Autonomous MRO Procurement API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("computes deterministic SHA-256 digest for evidence artifacts", async () => {
    const reportText = JSON.stringify({
      report_title: "Post-Repair Vibration Analysis Certification",
      work_order: "WO-2026-IMS-001",
      sensor_measurement: {
        vibration_peak_mm_s: 1.25,
        iso_zone: "Zone A (Good)",
      },
    });

    const hash = await computeSha256(reportText);
    expect(hash).toHaveLength(64);
    expect(typeof hash).toBe("string");

    // Deterministic verify
    const hash2 = await computeSha256(reportText);
    expect(hash2).toBe(hash);
  });

  it("evaluates quote under Autonomous Lane A (< $500 routine spares)", async () => {
    const mockEval = {
      decision: "ALLOWED",
      risk_lane: "LANE_A_ROUTINE",
      requires_supervisor_signoff: false,
      reason_codes: [],
      audit_hash: "mock-sha256-hash",
      quote: { quote_id: "Q-2026-001", amount: "450.00" },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockEval,
    } as any);

    const result = await evaluateProcurementQuote("Q-2026-001", "mock-token", "LANE_A");

    expect(result.decision).toBe("ALLOWED");
    expect(result.risk_lane).toBe("LANE_A_ROUTINE");
    expect(result.requires_supervisor_signoff).toBe(false);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/procurement/evaluate-quote"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ quote_id: "Q-2026-001", policy_lane: "LANE_A" }),
      })
    );
  });

  it("evaluates quote under Regulated Lane B (critical dual-control)", async () => {
    const mockEval = {
      decision: "ALLOWED",
      risk_lane: "LANE_B_EXCEPTION",
      requires_supervisor_signoff: true,
      reason_codes: ["POL-CRITICAL-ASSET: 'P-101A' requires human supervisor dual-signature"],
      audit_hash: "mock-sha256-hash-lane-b",
      quote: { quote_id: "Q-2026-001", amount: "450.00" },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockEval,
    } as any);

    const result = await evaluateProcurementQuote("Q-2026-001", "mock-token", "LANE_B");

    expect(result.decision).toBe("ALLOWED");
    expect(result.risk_lane).toBe("LANE_B_EXCEPTION");
    expect(result.requires_supervisor_signoff).toBe(true);
  });

  it("creates a PayPal order with Lane A autonomous policy", async () => {
    const mockOrder = {
      paypal_order_id: "SIM-ORD-2026-001",
      work_order_id: "WO-2026-IMS-001",
      status: "SIMULATED_ORDER_CREATED",
      amount_value: "450.00",
      currency_code: "USD",
      is_simulated: true,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockOrder,
    } as any);

    const order = await createPayPalOrder(
      "Q-2026-001",
      "usr-procurement-agent",
      true,
      "mock-token",
      "LANE_A"
    );

    expect(order.paypal_order_id).toBe("SIM-ORD-2026-001");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/paypal/orders"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          quote_id: "Q-2026-001",
          actor: "usr-procurement-agent",
          is_simulation: true,
          policy_lane: "LANE_A",
        }),
      })
    );
  });

  it("enforces fail-closed error handling when capture is blocked by No Evidence gate", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({
        detail: {
          error: "EvidenceGateBlocked",
          message: "No Evidence, No Capture: Service completion evidence is missing",
          policy: "No Evidence, No Capture",
        },
      }),
    } as any);

    await expect(capturePayPalOrder("SIM-ORD-001", undefined, "token")).rejects.toThrow();
  });
});
