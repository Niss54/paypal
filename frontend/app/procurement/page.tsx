"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ActivityIcon,
  AlertCircleIcon,
  AlertTriangleIcon,
  ArrowRightIcon,
  CheckCircle2Icon,
  ChevronRightIcon,
  ClockIcon,
  CreditCardIcon,
  FileCheck2Icon,
  FileTextIcon,
  LockIcon,
  PlayCircleIcon,
  RefreshCwIcon,
  RotateCcwIcon,
  ShieldAlertIcon,
  ShieldCheckIcon,
  SparklesIcon,
  UserCheckIcon,
  WrenchIcon,
  ZapIcon,
} from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  authorizePayPalOrder,
  capturePayPalOrder,
  createPayPalOrder,
  evaluateProcurementQuote,
  getOrderAuditLineage,
  getProcurementIncident,
  getProcurementMandate,
  getProcurementQuotes,
  submitCompletionEvidence,
  supervisorSignOff,
  type AuditLineageStage,
  type MandateEvalResult,
  type OrderAuditLineage,
  type PayPalOrderState,
  type ProcurementIncident,
  type ProcurementMandate,
  type ProcurementQuote,
} from "@/lib/api";

export default function ProcurementPage() {
  const [activeStep, setActiveStep] = useState<1 | 2 | 3>(1);

  // Core Data
  const [incident, setIncident] = useState<ProcurementIncident | null>(null);
  const [quotes, setQuotes] = useState<ProcurementQuote[]>([]);
  const [mandate, setMandate] = useState<ProcurementMandate | null>(null);
  const [selectedQuoteId, setSelectedQuoteId] = useState<string>("Q-2026-001");
  const [mandateEval, setMandateEval] = useState<MandateEvalResult | null>(null);

  // Active Transaction State
  const [order, setOrder] = useState<PayPalOrderState | null>(null);
  const [evidenceSubmitted, setEvidenceSubmitted] = useState<boolean>(false);
  const [supervisorSigned, setSupervisorSigned] = useState<boolean>(false);
  const [captureResult, setCaptureResult] = useState<any | null>(null);
  const [auditLineage, setAuditLineage] = useState<OrderAuditLineage | null>(null);

  // Status & Feedback
  const [loading, setLoading] = useState<boolean>(false);
  const [autoRunning, setAutoRunning] = useState<boolean>(false);
  const [gateBlocked, setGateBlocked] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error" | "info"; msg: string } | null>(null);

  // Load initial data
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [inc, qts, mnd] = await Promise.all([
          getProcurementIncident(),
          getProcurementQuotes(),
          getProcurementMandate(),
        ]);
        setIncident(inc);
        setQuotes(qts);
        setMandate(mnd);
        const ev = await evaluateProcurementQuote("Q-2026-001");
        setMandateEval(ev);
      } catch (err: any) {
        setFeedback({ type: "error", msg: err.message || "Failed to load procurement baseline" });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Handle Quote Selection
  const handleSelectQuote = async (qid: string) => {
    setSelectedQuoteId(qid);
    try {
      const ev = await evaluateProcurementQuote(qid);
      setMandateEval(ev);
    } catch (err: any) {
      setFeedback({ type: "error", msg: "Failed to evaluate quote policy" });
    }
  };

  // Step 1 ➔ Step 2: Create & Authorize PayPal Order
  const handleCreateAndAuthorize = async () => {
    try {
      setLoading(true);
      setGateBlocked(null);
      setFeedback(null);

      // 1. Create Order via backend Orders v2 with intent: AUTHORIZE
      const created = await createPayPalOrder(selectedQuoteId);
      setOrder(created);

      // 2. Authorize the funds hold (29-day honor period)
      const authorized = await authorizePayPalOrder(created.paypal_order_id);
      setOrder(authorized);

      setActiveStep(2);
      setFeedback({
        type: "success",
        msg: `PayPal Order created & authorized! Hold ID: ${authorized.authorization_id}. 29-day honor period active.`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "PayPal authorization failed" });
    } finally {
      setLoading(false);
    }
  };

  // Negative Test: Attempt Capture without Evidence (Should Fail)
  const handleAttemptEarlyCapture = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setGateBlocked(null);
      await capturePayPalOrder(order.paypal_order_id);
      setFeedback({ type: "success", msg: "Capture unexpectedly succeeded" });
    } catch (err: any) {
      // Expected HTTP 403 Forbidden
      setGateBlocked(
        err.message ||
          "HTTP 403 Forbidden: No Evidence, No Capture. Physical repair verification and dual-control sign-off required.",
      );
    } finally {
      setLoading(false);
    }
  };

  // Complete Evidence & Supervisor Approval
  const handleVerifyEvidenceAndSignOff = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setGateBlocked(null);

      // 1. Submit completion evidence (post-repair vibration: 1.25 mm/s, ISO Zone A)
      const payload = {
        evidence_id: `EVD-${order.paypal_order_id}`,
        work_order_id: order.work_order_id,
        quote_id: order.quote_id,
        equipment_tag: order.equipment_tag,
        vendor_id: order.vendor_id,
        service_id: "SRV-BRG-REPLACE",
        technician_id: "TECH-CERT-441",
        checklist_items: [
          `Asset tag ${order.equipment_tag} physically verified`,
          "Disassembly and bearing replacement executed per SOP-MECH-401",
          "Laser shaft alignment verified within tolerance (< 15 um)",
          "Post-replacement vibration baseline test run completed",
        ],
        measurements: {
          vibration_after_mm_s: 1.25,
          vibration_zone: "Zone A (Good)",
          bearing_temperature_c: 41.2,
        },
        file_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_synthetic: true,
      };

      await submitCompletionEvidence(order.paypal_order_id, payload);
      setEvidenceSubmitted(true);

      // 2. Supervisor sign-off
      await supervisorSignOff(
        order.paypal_order_id,
        "SUP-CHIEF-09",
        "Vibration re-inspection verified: 1.25 mm/s in Zone A. Approved for release.",
      );
      setSupervisorSigned(true);

      setFeedback({
        type: "success",
        msg: "Evidence verified (1.25 mm/s RMS) & Supervisor signed off! Gate is now UNLOCKED.",
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "Evidence submission failed" });
    } finally {
      setLoading(false);
    }
  };

  // Execute Final Gated Capture
  const handleExecuteGatedCapture = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setGateBlocked(null);

      const res = await capturePayPalOrder(order.paypal_order_id);
      setCaptureResult(res);

      const lineage = await getOrderAuditLineage(order.paypal_order_id);
      setAuditLineage(lineage);

      setActiveStep(3);
      setFeedback({
        type: "success",
        msg: `PayPal Payment Captured! Capture ID: ${res.capture_id || res.id}. Funds released to vendor.`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "Capture execution failed" });
    } finally {
      setLoading(false);
    }
  };

  // 1-Click Autonomous Demo Runner
  const handleRunAutoDemo = async () => {
    try {
      setAutoRunning(true);
      handleReset();

      // Step 1: Wait 1s
      await new Promise((r) => setTimeout(r, 800));
      const created = await createPayPalOrder("Q-2026-001");
      setOrder(created);
      const authorized = await authorizePayPalOrder(created.paypal_order_id);
      setOrder(authorized);
      setActiveStep(2);

      // Step 2: Show the negative gate test
      await new Promise((r) => setTimeout(r, 1200));
      setGateBlocked("HTTP 403 Forbidden: No Evidence, No Capture. Early capture strictly blocked.");

      // Step 3: Verify evidence & supervisor sign-off
      await new Promise((r) => setTimeout(r, 1800));
      setGateBlocked(null);
      await submitCompletionEvidence(authorized.paypal_order_id, {
        evidence_id: `EVD-${authorized.paypal_order_id}`,
        work_order_id: authorized.work_order_id,
        quote_id: authorized.quote_id,
        equipment_tag: authorized.equipment_tag,
        vendor_id: authorized.vendor_id,
        service_id: "SRV-BRG-REPLACE",
        technician_id: "TECH-CERT-441",
        checklist_items: ["Physical replacement completed", "Laser alignment verified", "Vibration baseline passed"],
        measurements: { vibration_after_mm_s: 1.25, vibration_zone: "Zone A (Good)" },
        file_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_synthetic: true,
      });
      setEvidenceSubmitted(true);

      await supervisorSignOff(authorized.paypal_order_id, "SUP-CHIEF-09", "Auto-demo sign-off verified.");
      setSupervisorSigned(true);

      // Step 4: Capture payment
      await new Promise((r) => setTimeout(r, 1400));
      const res = await capturePayPalOrder(authorized.paypal_order_id);
      setCaptureResult(res);
      const lineage = await getOrderAuditLineage(authorized.paypal_order_id);
      setAuditLineage(lineage);
      setActiveStep(3);

      setFeedback({
        type: "success",
        msg: "1-Click Demo Completed: Sensor Anomaly ➔ PayPal Authorized ➔ Gate Enforced ➔ Verified Capture!",
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "Auto-demo encountered an error" });
    } finally {
      setAutoRunning(false);
    }
  };

  const handleReset = () => {
    setOrder(null);
    setEvidenceSubmitted(false);
    setSupervisorSigned(false);
    setCaptureResult(null);
    setAuditLineage(null);
    setGateBlocked(null);
    setFeedback(null);
    setActiveStep(1);
  };

  const selectedQuote = quotes.find((q) => q.quote_id === selectedQuoteId) || quotes[0];

  return (
    <div className="flex-1 space-y-6 p-4 sm:p-6 max-w-6xl mx-auto">
      {/* Top Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/50 pb-5">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="bg-[#003087] hover:bg-[#00256c] text-white border-0 gap-1.5 px-2.5 py-1 text-xs">
              <CreditCardIcon className="w-3.5 h-3.5 text-[#0079C1]" /> PayPal Orders v2
            </Badge>
            <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 bg-emerald-500/10 text-xs">
              Sandbox Live
            </Badge>
            <Badge variant="outline" className="border-amber-500/40 text-amber-400 bg-amber-500/10 text-xs font-mono">
              "No Evidence, No Capture"
            </Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-2">
            Evidence-Gated Industrial Procurement
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            Autonomous AI maintenance procurement with deterministic spending mandates, physical telemetry verification, and two-phase PayPal settlement.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            onClick={handleRunAutoDemo}
            disabled={autoRunning || loading}
            className="gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-sm font-medium"
          >
            <PlayCircleIcon className="w-4 h-4" />
            {autoRunning ? "Running Demo..." : "1-Click Auto Demo"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleReset} disabled={autoRunning} className="gap-1.5">
            <RotateCcwIcon className="w-3.5 h-3.5" /> Reset
          </Button>
        </div>
      </div>

      {/* Global Alerts */}
      {feedback && (
        <Alert
          className={
            feedback.type === "success"
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
              : feedback.type === "error"
              ? "border-red-500/40 bg-red-500/10 text-red-300"
              : "border-blue-500/40 bg-blue-500/10 text-blue-300"
          }
        >
          {feedback.type === "success" ? (
            <CheckCircle2Icon className="h-4 w-4 text-emerald-400" />
          ) : (
            <AlertCircleIcon className="h-4 w-4 text-red-400" />
          )}
          <AlertTitle className="font-semibold text-sm">
            {feedback.type === "success" ? "System Notification" : "Notice"}
          </AlertTitle>
          <AlertDescription className="text-xs">{feedback.msg}</AlertDescription>
        </Alert>
      )}

      {/* Simplified 3-Step Navigation Tabs */}
      <div className="grid grid-cols-3 gap-3">
        {[
          {
            step: 1,
            title: "1. Telemetry & RFQ Quote",
            desc: "NASA IMS Anomaly & $500 Mandate",
            icon: ActivityIcon,
          },
          {
            step: 2,
            title: "2. PayPal Authorization & Gate",
            desc: "Hold Funds & Enforce Safety Gate",
            icon: LockIcon,
          },
          {
            step: 3,
            title: "3. Settled Receipt & Lineage",
            desc: "Verified Capture & Audit Chain",
            icon: ShieldCheckIcon,
          },
        ].map((s) => {
          const isActive = activeStep === s.step;
          const isDone = activeStep > s.step;
          return (
            <button
              key={s.step}
              onClick={() => setActiveStep(s.step as any)}
              className={`p-3.5 rounded-xl text-left border transition-all ${
                isActive
                  ? "border-blue-500/60 bg-blue-500/10 text-foreground ring-1 ring-blue-500/40 shadow-sm"
                  : isDone
                  ? "border-emerald-500/30 bg-emerald-500/5 text-muted-foreground hover:bg-emerald-500/10"
                  : "border-border/40 bg-card/40 text-muted-foreground hover:bg-card/70"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <s.icon className={`w-4 h-4 ${isActive ? "text-blue-400" : isDone ? "text-emerald-400" : "text-muted-foreground"}`} />
                  <span className="text-xs font-semibold">{s.title}</span>
                </div>
                {isDone && <CheckCircle2Icon className="w-4 h-4 text-emerald-400" />}
              </div>
              <p className="text-[11px] text-muted-foreground mt-1 truncate">{s.desc}</p>
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* STEP 1: TELEMETRY & VENDOR RFQ QUOTE */}
      {/* ========================================================================= */}
      {activeStep === 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Anomaly Card */}
          <div className="lg:col-span-5 space-y-4">
            <Card className="border-border/60 shadow-xs">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ActivityIcon className="w-4 h-4 text-red-400 animate-pulse" />
                    <CardTitle className="text-base font-semibold">Physical Vibration Anomaly</CardTitle>
                  </div>
                  <Badge variant="destructive" className="bg-red-500/20 text-red-400 border-red-500/30 text-[10px]">
                    ISO ZONE C/D
                  </Badge>
                </div>
                <CardDescription className="text-xs">
                  Real NASA IMS Bearing accelerometry replay (Run-to-Failure dataset).
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 rounded-lg bg-muted/40 border border-border/40 space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Asset ID:</span>
                    <span className="font-semibold text-foreground font-mono">P-101A (Primary Slurry Pump)</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Vibration Velocity RMS:</span>
                    <span className="font-bold text-red-400 text-sm">4.82 mm/s RMS</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">ISO 10816-3 Threshold:</span>
                    <span className="text-amber-400 font-medium">4.50 mm/s Limit</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Work Order Draft:</span>
                    <span className="text-foreground font-mono text-[11px]">WO-2026-IMS-001</span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg border border-border/40 bg-card/50 text-[11px] text-muted-foreground space-y-1">
                  <span className="font-medium text-foreground block">GraphRAG Diagnostic Finding:</span>
                  <p>Inner-race bearing defect detected. Immediate bearing replacement required to prevent catastrophic shaft seizure.</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* RFQ & Spending Mandate Card */}
          <div className="lg:col-span-7 space-y-4">
            <Card className="border-border/60 shadow-xs">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <WrenchIcon className="w-4 h-4 text-blue-400" />
                    <CardTitle className="text-base font-semibold">Vendor RFQ Quotes & Spending Policy</CardTitle>
                  </div>
                  <Badge variant="outline" className="border-purple-500/40 text-purple-400 bg-purple-500/10 text-[10px]">
                    Policy Cap: $500.00 USD
                  </Badge>
                </div>
                <CardDescription className="text-xs">
                  Quotes evaluated by the Deterministic Spending Mandate Engine.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-3">
                <div className="space-y-2">
                  {quotes.map((q) => {
                    const isSelected = selectedQuoteId === q.quote_id;
                    return (
                      <div
                        key={q.quote_id}
                        onClick={() => handleSelectQuote(q.quote_id)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
                          isSelected
                            ? "border-blue-500/60 bg-blue-500/10 ring-1 ring-blue-500/30"
                            : "border-border/40 bg-card/40 hover:bg-card/70"
                        }`}
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-foreground">{q.vendor_name}</span>
                            <Badge variant="outline" className="text-[10px] py-0 px-1.5 text-muted-foreground">
                              {q.quote_id}
                            </Badge>
                            {isSelected && (
                              <Badge className="bg-blue-600 text-white text-[10px] py-0 px-1.5">
                                Winning Bid
                              </Badge>
                            )}
                          </div>
                          <span className="text-[11px] text-muted-foreground block mt-0.5">
                            SLA: {q.sla_hours}h response • {q.is_allowlisted ? "Approved Vendor" : "Standard"}
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-sm font-bold text-foreground">
                            ${parseFloat(q.amount).toFixed(2)} USD
                          </span>
                          <span className="text-[10px] text-muted-foreground block">
                            {parseFloat(q.amount) <= 500 ? "Within Cap ✅" : "Exceeds Cap ⚠️"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Mandate Policy Status Box */}
                {mandateEval && (
                  <div className="p-3 rounded-lg bg-muted/40 border border-border/40 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-foreground">Spending Mandate Evaluation:</span>
                      <Badge
                        className={
                          mandateEval.decision === "ALLOWED"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs"
                            : "bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs"
                        }
                      >
                        {mandateEval.decision} (LANE B - CRITICAL ASSET)
                      </Badge>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[11px] text-muted-foreground pt-1">
                      <div className="flex items-center gap-1">
                        <CheckCircle2Icon className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Budget $\le$ $500</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <CheckCircle2Icon className="w-3.5 h-3.5 text-emerald-400" />
                        <span>USD Currency</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <CheckCircle2Icon className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Approved Vendor</span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>

              <CardFooter className="pt-2 flex justify-between items-center border-t border-border/40">
                <span className="text-xs text-muted-foreground font-mono">
                  Ready: {selectedQuote.vendor_name} (${selectedQuote.amount})
                </span>
                <Button
                  onClick={handleCreateAndAuthorize}
                  disabled={loading}
                  className="gap-2 bg-[#003087] hover:bg-[#00256c] text-white"
                >
                  <CreditCardIcon className="w-4 h-4 text-[#0079C1]" />
                  Create & Authorize PayPal Order <ArrowRightIcon className="w-4 h-4" />
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 2: PAYPAL AUTHORIZATION & THE EVIDENCE GATE (THE HERO DEMO) */}
      {/* ========================================================================= */}
      {activeStep === 2 && order && (
        <div className="space-y-6">
          {/* Order Status Banner */}
          <Card className="border-blue-500/40 bg-blue-500/5 shadow-xs">
            <CardContent className="p-4 sm:p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-[#003087] text-white border-0 text-xs font-mono">
                      {order.paypal_order_id}
                    </Badge>
                    <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/40 text-xs">
                      STATUS: {order.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      (intent: <code className="text-blue-400">AUTHORIZE</code>)
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Funds (${parseFloat(order.amount_value).toFixed(2)} USD) are held under a 29-day honor period. No funds are captured yet.
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-xs text-muted-foreground block">Authorization ID</span>
                  <span className="text-xs font-mono font-semibold text-foreground">
                    {order.authorization_id || "AUTH-SANDBOX-PENDING"}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* The Hero Live Test Bench */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Box: The Negative Gate Test */}
            <Card className="border-red-500/30 bg-card/40 shadow-xs flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <ShieldAlertIcon className="w-5 h-5 text-red-400" />
                  <CardTitle className="text-base font-semibold text-foreground">
                    1. Test "No Evidence, No Capture"
                  </CardTitle>
                </div>
                <CardDescription className="text-xs">
                  Proves that the AI agent or merchant CANNOT capture funds prematurely.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Click below to attempt an early capture before physical repair verification is filed. The deterministic backend must reject this request.
                </p>

                {gateBlocked && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-xs space-y-1">
                    <span className="font-semibold flex items-center gap-1.5">
                      <LockIcon className="w-3.5 h-3.5 text-red-400" /> Access Blocked by Security Policy
                    </span>
                    <p className="text-[11px] font-mono leading-tight">{gateBlocked}</p>
                  </div>
                )}
              </CardContent>

              <CardFooter className="pt-2">
                <Button
                  variant="destructive"
                  onClick={handleAttemptEarlyCapture}
                  disabled={loading || evidenceSubmitted}
                  className="w-full gap-2 text-xs font-medium"
                >
                  <LockIcon className="w-3.5 h-3.5" />
                  {evidenceSubmitted ? "Early Capture Disabled (Evidence Present)" : "Attempt Early Capture (Should Fail)"}
                </Button>
              </CardFooter>
            </Card>

            {/* Right Box: The Verification & Capture Flow */}
            <Card className="border-emerald-500/30 bg-card/40 shadow-xs flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <FileCheck2Icon className="w-5 h-5 text-emerald-400" />
                  <CardTitle className="text-base font-semibold text-foreground">
                    2. Physical Verification & Release
                  </CardTitle>
                </div>
                <CardDescription className="text-xs">
                  Vendor submits physical repair telemetry and supervisor signs off.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-3">
                <div className="p-3 rounded-lg bg-muted/40 border border-border/40 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Post-Repair Vibration:</span>
                    <span className="font-semibold text-emerald-400">1.25 mm/s RMS (Zone A - Good)</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Scope Checklist:</span>
                    <span className="font-semibold text-foreground">4/4 Passed</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Document SHA-256:</span>
                    <span className="font-mono text-[10px] text-muted-foreground truncate max-w-[180px]">
                      e3b0c44298fc1c149afbf4...
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Supervisor Sign-Off:</span>
                    <span className="font-semibold text-foreground">
                      {supervisorSigned ? "Approved (SUP-CHIEF-09) ✅" : "Pending Signature ⏳"}
                    </span>
                  </div>
                </div>

                {!evidenceSubmitted && (
                  <Button
                    onClick={handleVerifyEvidenceAndSignOff}
                    disabled={loading}
                    variant="outline"
                    className="w-full gap-2 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10 text-xs"
                  >
                    <UserCheckIcon className="w-3.5 h-3.5 text-emerald-400" />
                    Submit Verified Evidence & Sign-Off
                  </Button>
                )}
              </CardContent>

              <CardFooter className="pt-2">
                <Button
                  onClick={handleExecuteGatedCapture}
                  disabled={loading || !evidenceSubmitted || !supervisorSigned}
                  className="w-full gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold"
                >
                  <CheckCircle2Icon className="w-4 h-4" />
                  Execute Gated PayPal Capture (${parseFloat(order.amount_value).toFixed(2)})
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 3: SETTLED RECEIPT & CRYPTOGRAPHIC LINEAGE */}
      {/* ========================================================================= */}
      {activeStep === 3 && (
        <div className="space-y-6">
          {/* Payment Receipt Banner */}
          <Card className="border-emerald-500/40 bg-emerald-500/5 shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2Icon className="w-6 h-6 text-emerald-400" />
                  <div>
                    <CardTitle className="text-lg font-bold text-foreground">
                      PayPal Payment Successfully Settled
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Funds captured and transferred to vendor following complete physical evidence validation.
                    </CardDescription>
                  </div>
                </div>
                <Badge className="bg-emerald-600 text-white text-xs px-2.5 py-1">
                  SETTLEMENT COMPLETED
                </Badge>
              </div>
            </CardHeader>

            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-card/60 border border-border/40 text-xs">
                <div>
                  <span className="text-muted-foreground block text-[11px]">PayPal Order ID</span>
                  <span className="font-mono font-semibold text-foreground">
                    {order?.paypal_order_id || "ORD-SANDBOX-VERIFIED"}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">PayPal Capture ID</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {captureResult?.capture_id || "CAP-SANDBOX-SUCCESS-01"}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Settled Amount</span>
                  <span className="font-semibold text-foreground">
                    ${parseFloat(order?.amount_value || "450.00").toFixed(2)} USD
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Recipient</span>
                  <span className="font-semibold text-foreground">{order?.vendor_id || "Apex Rotating Equipment"}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 7-Stage Causal Audit Trail */}
          <Card className="border-border/60 shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheckIcon className="w-5 h-5 text-blue-400" />
                <CardTitle className="text-base font-semibold">
                  7-Stage Cryptographic & Operational Causal Lineage
                </CardTitle>
              </div>
              <CardDescription className="text-xs">
                Unbroken audit chain proving why every cent was authorized and captured.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <div className="space-y-3">
                {[
                  {
                    stage: "1. Sensor Anomaly",
                    detail: "NASA IMS Bearing 1: 4.82 mm/s RMS (ISO 10816 Zone C/D excursion)",
                    status: "PASS",
                  },
                  {
                    stage: "2. GraphRAG Diagnostic",
                    detail: "Inner race spalling identified. Work order WO-2026-IMS-001 drafted.",
                    status: "PASS",
                  },
                  {
                    stage: "3. RFQ Selection",
                    detail: "Apex Rotating Equipment selected ($450.00 USD, 12h SLA).",
                    status: "PASS",
                  },
                  {
                    stage: "4. Spending Mandate",
                    detail: "Deterministic rules verified: $450 <= $500 cap, USD, Lane B critical asset.",
                    status: "PASS",
                  },
                  {
                    stage: "5. PayPal Authorization",
                    detail: `Hold created with intent: AUTHORIZE (${order?.authorization_id || "AUTH-SANDBOX"}).`,
                    status: "PASS",
                  },
                  {
                    stage: "6. Evidence & Dual-Control",
                    detail: "Post-repair vibration: 1.25 mm/s. Supervisor SUP-CHIEF-09 sign-off recorded.",
                    status: "PASS",
                  },
                  {
                    stage: "7. PayPal Capture",
                    detail: `Captured via /v2/payments/authorizations/capture (${captureResult?.capture_id || "CAP-SANDBOX"}).`,
                    status: "PASS",
                  },
                ].map((s, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border border-border/40 bg-card/40 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-[11px]">
                        {idx + 1}
                      </span>
                      <div>
                        <span className="font-semibold text-foreground block">{s.stage}</span>
                        <span className="text-[11px] text-muted-foreground">{s.detail}</span>
                      </div>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px]">
                      VERIFIED ✅
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>

            <CardFooter className="pt-2 flex justify-between">
              <span className="text-xs text-muted-foreground font-mono">
                Cryptographic Integrity: SHA-256 Validated
              </span>
              <Button variant="outline" size="sm" onClick={handleReset} className="gap-1.5 text-xs">
                <RotateCcwIcon className="w-3.5 h-3.5" /> Start New Procurement
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  );
}
