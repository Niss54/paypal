"use client";

import React, { useEffect, useState } from "react";
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
  RefreshCwIcon,
  RotateCcwIcon,
  ShieldAlertIcon,
  ShieldCheckIcon,
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
import { Input } from "@/components/ui/input";
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
  voidPayPalOrder,
  type AuditLineageStage,
  type MandateEvalResult,
  type OrderAuditLineage,
  type PayPalOrderState,
  type ProcurementIncident,
  type ProcurementMandate,
  type ProcurementQuote,
} from "@/lib/api";

export default function ProcurementPage() {
  const [activeStage, setActiveStage] = useState<1 | 2 | 3 | 4>(1);

  // Data states
  const [incident, setIncident] = useState<ProcurementIncident | null>(null);
  const [quotes, setQuotes] = useState<ProcurementQuote[]>([]);
  const [mandate, setMandate] = useState<ProcurementMandate | null>(null);
  const [selectedQuoteId, setSelectedQuoteId] = useState<string>("Q-2026-001");
  const [mandateEval, setMandateEval] = useState<MandateEvalResult | null>(null);

  // Active Order state
  const [order, setOrder] = useState<PayPalOrderState | null>(null);
  const [evidenceSubmitted, setEvidenceSubmitted] = useState<boolean>(false);
  const [evidenceResult, setEvidenceResult] = useState<any | null>(null);
  const [supervisorSigned, setSupervisorSigned] = useState<boolean>(false);
  const [captureResult, setCaptureResult] = useState<any | null>(null);
  const [auditLineage, setAuditLineage] = useState<OrderAuditLineage | null>(null);

  // UI status
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [gateBlockedMsg, setGateBlockedMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form inputs for completion report
  const [postVibRms, setPostVibRms] = useState<string>("1.25");
  const [technicianId, setTechnicianId] = useState<string>("TECH-CERT-441");
  const [supervisorId, setSupervisorId] = useState<string>("SUP-CHIEF-09");

  // Load initial scenario on mount
  useEffect(() => {
    async function loadInitialData() {
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

        // Evaluate default selected quote
        const ev = await evaluateProcurementQuote("Q-2026-001");
        setMandateEval(ev);
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to initialize procurement data");
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  const handleSelectQuote = async (quoteId: string) => {
    setSelectedQuoteId(quoteId);
    try {
      const ev = await evaluateProcurementQuote(quoteId);
      setMandateEval(ev);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to evaluate quote");
    }
  };

  const handleCreateOrder = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      setGateBlockedMsg(null);
      const newOrder = await createPayPalOrder(selectedQuoteId);
      setOrder(newOrder);
      setSuccessMsg(`PayPal Order created successfully: ${newOrder.paypal_order_id} (intent: AUTHORIZE)`);
      setActiveStage(3);
    } catch (err: any) {
      setErrorMsg(err.message || "Order creation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleAuthorizeOrder = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const updated = await authorizePayPalOrder(order.paypal_order_id);
      setOrder(updated);
      setSuccessMsg(`Order authorized: ${updated.authorization_id}. Funds held under 29-day honor period.`);
    } catch (err: any) {
      setErrorMsg(err.message || "Authorization failed");
    } finally {
      setLoading(false);
    }
  };

  const handleAttemptCapture = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      setGateBlockedMsg(null);
      const res = await capturePayPalOrder(order.paypal_order_id);
      setCaptureResult(res);
      setSuccessMsg("Payment captured successfully! Funds transferred to vendor.");
      // Refresh audit lineage and move to stage 4
      const lineage = await getOrderAuditLineage(order.paypal_order_id);
      setAuditLineage(lineage);
      setActiveStage(4);
    } catch (err: any) {
      if (err.status === 403 || err.message?.includes("No Evidence, No Capture") || err.message?.includes("Dual-Control")) {
        setGateBlockedMsg(err.message || "Evidence Gate blocked capture");
      } else {
        setErrorMsg(err.message || "Capture failed");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitEvidence = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      setGateBlockedMsg(null);
      const payload = {
        evidence_id: `EVD-${order.paypal_order_id}`,
        work_order_id: order.work_order_id,
        quote_id: order.quote_id,
        equipment_tag: order.equipment_tag,
        vendor_id: order.vendor_id,
        service_id: "SRV-BRG-REPLACE",
        technician_id: technicianId,
        checklist_items: [
          `Asset tag ${order.equipment_tag} physically verified`,
          "Disassembly and bearing replacement executed per SOP-MECH-401",
          "Laser shaft alignment verified within tolerance (< 15 um)",
          "Post-replacement vibration baseline test run completed",
        ],
        measurements: {
          vibration_after_mm_s: parseFloat(postVibRms),
          vibration_zone: parseFloat(postVibRms) <= 2.8 ? "Zone A (Good)" : "Zone C (Alert)",
          bearing_temperature_c: 41.2,
        },
        file_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_synthetic: true,
      };

      const res = await submitCompletionEvidence(order.paypal_order_id, payload);
      setEvidenceResult(res);
      setEvidenceSubmitted(true);
      setSuccessMsg("Vendor completion evidence validated: All deterministic criteria passed!");
    } catch (err: any) {
      setErrorMsg(err.message || "Evidence submission failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSupervisorSignOff = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      setGateBlockedMsg(null);
      await supervisorSignOff(
        order.paypal_order_id,
        supervisorId,
        "Verified vibration sensor readings and checklist per Lane B critical asset policy.",
      );
      setSupervisorSigned(true);
      setSuccessMsg(`Dual-control sign-off recorded by supervisor ${supervisorId}.`);
    } catch (err: any) {
      setErrorMsg(err.message || "Supervisor sign-off failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setOrder(null);
    setEvidenceSubmitted(false);
    setEvidenceResult(null);
    setSupervisorSigned(false);
    setCaptureResult(null);
    setAuditLineage(null);
    setErrorMsg(null);
    setGateBlockedMsg(null);
    setSuccessMsg(null);
    setActiveStage(1);
  };

  return (
    <div className="flex-1 space-y-6 p-6 max-w-7xl mx-auto">
      {/* Top Banner / Product Positioning */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Evidence-Gated Industrial Procurement
            </h1>
            <Badge variant="outline" className="border-blue-500/40 text-blue-400 bg-blue-500/10">
              PayPal Orders v2
            </Badge>
            <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 bg-emerald-500/10">
              Sandbox Active
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Autonomous procurement with deterministic spending mandates and signature{" "}
            <span className="font-semibold text-foreground">"No Evidence, No Capture"</span> dual-phase settlement.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleReset} className="gap-1.5 text-xs">
            <RotateCcwIcon className="w-3.5 h-3.5" /> Reset Demo
          </Button>
        </div>
      </div>

      {/* Global Alerts */}
      {errorMsg && (
        <Alert variant="destructive">
          <AlertCircleIcon className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{errorMsg}</AlertDescription>
        </Alert>
      )}

      {successMsg && (
        <Alert className="border-emerald-500/40 bg-emerald-500/10 text-emerald-300">
          <CheckCircle2Icon className="h-4 w-4 text-emerald-400" />
          <AlertTitle>Operation Successful</AlertTitle>
          <AlertDescription>{successMsg}</AlertDescription>
        </Alert>
      )}

      {/* 4-Stage Stepper Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {[
          { num: 1, title: "1. Incident Intelligence", sub: "NASA IMS Bearing Anomaly" },
          { num: 2, title: "2. Procurement & Mandate", sub: "RFQ Quotes & Policy Hard Gates" },
          { num: 3, title: "3. PayPal Authorization & Gate", sub: "No Evidence, No Capture" },
          { num: 4, title: "4. Transaction Lineage", sub: "Causal Audit Ledger" },
        ].map((s) => {
          const isActive = activeStage === s.num;
          const isDone = activeStage > s.num;
          return (
            <button
              key={s.num}
              onClick={() => setActiveStage(s.num as any)}
              className={`p-3 rounded-lg text-left border transition-all ${
                isActive
                  ? "border-primary bg-primary/10 text-foreground ring-1 ring-primary"
                  : isDone
                  ? "border-emerald-500/30 bg-emerald-500/5 text-muted-foreground"
                  : "border-border/40 bg-card/40 text-muted-foreground hover:bg-card/70"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold">{s.title}</span>
                {isDone && <CheckCircle2Icon className="w-3.5 h-3.5 text-emerald-400" />}
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5 truncate">{s.sub}</p>
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* SCREEN 1: INCIDENT INTELLIGENCE */}
      {/* ========================================================================= */}
      {activeStage === 1 && incident && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ActivityIcon className="w-5 h-5 text-red-400" />
                    <CardTitle className="text-lg">Predictive Anomaly Excursion</CardTitle>
                  </div>
                  <Badge variant="destructive" className="bg-red-500/20 text-red-400 border-red-500/30">
                    {incident.status}
                  </Badge>
                </div>
                <CardDescription>
                  High-frequency vibration accelerometry excursion detected on drive-end bearing.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-lg bg-muted/40 border border-border/40">
                  <div>
                    <span className="text-xs text-muted-foreground">Asset Tag</span>
                    <p className="text-base font-semibold text-foreground">{incident.equipment_tag}</p>
                    <span className="text-[10px] text-muted-foreground">{incident.equipment_name}</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Measured Velocity RMS</span>
                    <p className="text-base font-bold text-red-400">{incident.measured_value_mm_s} mm/s</p>
                    <span className="text-[10px] text-muted-foreground">Baseline: {incident.normal_baseline_mm_s} mm/s</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">ISO 10816 Alarm Limit</span>
                    <p className="text-base font-semibold text-amber-400">{incident.alarm_threshold_mm_s} mm/s</p>
                    <span className="text-[10px] text-muted-foreground">Zone C/D Excursion</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Criticality</span>
                    <p className="text-base font-semibold text-purple-400">Critical Asset</p>
                    <span className="text-[10px] text-muted-foreground">Lane B Exception Policy</span>
                  </div>
                </div>

                <div className="p-3.5 rounded-lg border border-border/50 bg-card/60">
                  <div className="flex items-center gap-2 mb-1.5">
                    <Badge variant="outline" className="text-xs border-amber-500/30 text-amber-400 bg-amber-500/10">
                      Grounded Empirical Source
                    </Badge>
                    <span className="text-xs text-muted-foreground">{incident.anomaly_source}</span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Envelope spectrum analysis indicates inner/outer race spalling with 48-72h failure horizon.
                    NASA IMS accelerometer signal replayed with zero synthetic fabrication of telemetry signals.
                  </p>
                </div>
              </CardContent>

              <CardFooter className="flex justify-between border-t border-border/40 pt-4">
                <span className="text-xs text-muted-foreground">Work Order: {incident.work_order_id}</span>
                <Button onClick={() => setActiveStage(2)} className="gap-1.5">
                  Proceed to RFQ Quotes & Mandate <ArrowRightIcon className="w-4 h-4" />
                </Button>
              </CardFooter>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <FileTextIcon className="w-4 h-4 text-primary" /> Work Order Draft
                </CardTitle>
                <CardDescription>Synthesized from telemetry & GraphRAG diagnosis</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-3 rounded border border-border/40 bg-muted/20 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">WO Number:</span>
                    <span className="font-mono font-medium">{incident.work_order_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Component:</span>
                    <span className="font-medium">{incident.component}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Required Action:</span>
                    <span className="font-medium text-amber-400">Emergency Replacement</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Dual-Signature:</span>
                    <Badge variant="outline" className="text-[10px] text-purple-400 border-purple-400/30">
                      Required (Lane B)
                    </Badge>
                  </div>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  Recommended action: Immediate dispatch of certified rotating equipment specialist, SKF 22210 bearing
                  replacement, laser alignment, and vibration re-verification.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SCREEN 2: PROCUREMENT & MANDATE */}
      {/* ========================================================================= */}
      {activeStage === 2 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Candidate RFQ Quotations</CardTitle>
                  <Badge variant="outline" className="text-xs border-blue-500/30 text-blue-400">
                    3 Quotations Evaluated
                  </Badge>
                </div>
                <CardDescription>
                  Hard gates applied first: Budget cap, allowlisted vendor, currency, and emergency SLA window.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                {quotes.map((q) => {
                  const isSelected = selectedQuoteId === q.quote_id;
                  const isAllowed = q.scoring.hard_gates_passed;
                  return (
                    <div
                      key={q.quote_id}
                      onClick={() => handleSelectQuote(q.quote_id)}
                      className={`p-4 rounded-lg border transition-all cursor-pointer ${
                        isSelected
                          ? "border-primary bg-primary/5 ring-1 ring-primary"
                          : "border-border/50 hover:bg-muted/30"
                      }`}
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-foreground text-sm">{q.vendor_name}</h3>
                            <Badge variant="outline" className="text-[10px] font-mono">
                              {q.vendor_id}
                            </Badge>
                            <span className="text-[10px] text-amber-400 font-mono">{q.synthetic_label}</span>
                            {q.is_direct_paypal_sandbox_merchant && (
                              <Badge className="bg-blue-600/20 text-blue-400 text-[10px] border-blue-500/30">
                                PayPal Sandbox Receiver
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">{q.scope_description}</p>
                        </div>

                        <div className="flex items-center gap-4 text-right">
                          <div>
                            <span className="text-lg font-bold text-foreground">
                              ${q.amount} <span className="text-xs font-normal text-muted-foreground">{q.currency}</span>
                            </span>
                            <div className="text-[11px] text-muted-foreground">SLA: {q.sla_hours}h</div>
                          </div>
                          <div>
                            {isAllowed ? (
                              <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-xs">
                                Hard Gates PASS
                              </Badge>
                            ) : (
                              <Badge variant="destructive" className="bg-red-500/20 text-red-400 border-red-500/30 text-xs">
                                BLOCKED
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>

                      {!isAllowed && q.scoring.gate_failure_reason && (
                        <div className="mt-2 text-[11px] text-red-400 bg-red-500/5 p-2 rounded border border-red-500/20">
                          Gate Failure: {q.scoring.gate_failure_reason}
                        </div>
                      )}
                    </div>
                  );
                })}
              </CardContent>

              <CardFooter className="flex justify-between border-t border-border/40 pt-4">
                <Button variant="outline" onClick={() => setActiveStage(1)}>
                  Back
                </Button>
                <Button
                  onClick={handleCreateOrder}
                  disabled={loading || !mandateEval || mandateEval.decision === "BLOCKED"}
                  className="gap-2"
                >
                  <CreditCardIcon className="w-4 h-4" /> Create PayPal Order (intent: AUTHORIZE)
                </Button>
              </CardFooter>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <ShieldCheckIcon className="w-4 h-4 text-emerald-400" /> Spending Mandate Snapshot
                </CardTitle>
                <CardDescription>Deterministic server-owned boundary</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                {mandate && (
                  <div className="space-y-2 p-3 rounded bg-muted/20 border border-border/40">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Mandate ID:</span>
                      <span className="font-mono">{mandate.mandate_id} (v{mandate.version})</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Budget Cap:</span>
                      <span className="font-bold text-foreground">${mandate.max_amount} {mandate.currency_code}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Allowlisted Vendors:</span>
                      <span>{mandate.allowed_vendor_ids.join(", ")}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Risk Routing:</span>
                      <span className="text-purple-400 font-semibold">Lane B (Critical Asset)</span>
                    </div>
                  </div>
                )}

                {mandateEval && (
                  <div className="p-3 rounded border border-border/50 bg-card/60 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground">Policy Evaluation:</span>
                      <Badge
                        className={
                          mandateEval.decision === "ALLOWED"
                            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                            : "bg-red-500/20 text-red-400 border-red-500/30"
                        }
                      >
                        {mandateEval.decision}
                      </Badge>
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      {mandateEval.reason_codes.join("; ") || "All mandate conditions satisfied"}
                    </div>
                    <div className="text-[10px] font-mono text-muted-foreground truncate">
                      Audit Hash: {mandateEval.audit_hash}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SCREEN 3: PAYPAL AUTHORIZATION & EVIDENCE GATE */}
      {/* ========================================================================= */}
      {activeStage === 3 && (
        <div className="space-y-6">
          {/* Order Header Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <CreditCardIcon className="w-5 h-5 text-blue-400" />
                    <CardTitle className="text-lg">PayPal Orders v2 Authorization</CardTitle>
                    <Badge variant="outline" className="border-blue-500/40 text-blue-400">
                      {order?.status || "ORDER_CREATED"}
                    </Badge>
                  </div>
                  <CardDescription>
                    Two-phase lifecycle: Funds are held under authorization, releasing only upon verified repair proof.
                  </CardDescription>
                </div>

                <div className="text-right">
                  <div className="text-xl font-bold font-mono text-foreground">
                    ${order?.amount_value || "450.00"} {order?.currency_code || "USD"}
                  </div>
                  <div className="text-xs text-muted-foreground font-mono">
                    Order ID: {order?.paypal_order_id || "SANDBOX-PENDING"}
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-lg bg-muted/30 border border-border/40 text-xs">
                <div>
                  <span className="text-muted-foreground">Authorization ID</span>
                  <p className="font-mono font-medium text-foreground mt-0.5">
                    {order?.authorization_id || "Awaiting Buyer Authorization"}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Hold Guarantee</span>
                  <p className="font-medium text-foreground mt-0.5">29-day Sandbox honor period</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Settlement Policy</span>
                  <p className="font-semibold text-emerald-400 mt-0.5">No Evidence, No Capture</p>
                </div>
              </div>

              {/* Action buttons for Authorization */}
              {(!order?.authorization_id || order.status === "ORDER_CREATED") && (
                <div className="flex items-center gap-3 p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                  <LockIcon className="w-5 h-5 text-blue-400 shrink-0" />
                  <div className="flex-1 text-xs">
                    <span className="font-semibold text-blue-300">Buyer Approval Simulation:</span> Authorize the
                    allocated $450.00 funds in PayPal Sandbox.
                  </div>
                  <Button size="sm" onClick={handleAuthorizeOrder} disabled={loading} className="gap-1.5">
                    Authorize Order <ArrowRightIcon className="w-3.5 h-3.5" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Interactive Evidence Gate Test Bench */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: The "No Evidence, No Capture" Test Trigger */}
            <Card className="border-amber-500/30 bg-amber-500/5">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <ShieldAlertIcon className="w-5 h-5 text-amber-400" />
                  <CardTitle className="text-base text-foreground">Evidence Gate Verification</CardTitle>
                </div>
                <CardDescription>
                  Live test of the core architectural invariant. Capturing without validated evidence must fail with HTTP 403.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4 text-xs">
                <p className="text-muted-foreground leading-relaxed">
                  Click the button below to attempt a premature PayPal Capture call before vendor evidence is submitted and verified.
                </p>

                <Button
                  variant="outline"
                  onClick={handleAttemptCapture}
                  disabled={loading || order?.status === "CAPTURED"}
                  className="w-full border-amber-500/40 text-amber-300 hover:bg-amber-500/10 gap-2 font-mono text-xs"
                >
                  <ZapIcon className="w-4 h-4 text-amber-400" /> Attempt Immediate Capture (POST /api/paypal/orders/capture)
                </Button>

                {gateBlockedMsg && (
                  <Alert variant="destructive" className="bg-red-500/10 border-red-500/30 text-red-300 text-xs">
                    <AlertCircleIcon className="h-4 w-4 text-red-400" />
                    <AlertTitle className="font-semibold">Gate Blocked (HTTP 403 Forbidden)</AlertTitle>
                    <AlertDescription className="mt-1 font-mono text-[11px]">{gateBlockedMsg}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Right: Vendor Evidence Submission */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileCheck2Icon className="w-5 h-5 text-emerald-400" />
                    <CardTitle className="text-base">Vendor Repair Evidence</CardTitle>
                  </div>
                  {evidenceSubmitted && (
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-xs">
                      VALIDATED PASS
                    </Badge>
                  )}
                </div>
                <CardDescription>
                  Certified technician submits physical completion report & measurements.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-muted-foreground text-[11px]">Technician ID</label>
                    <Input
                      value={technicianId}
                      onChange={(e) => setTechnicianId(e.target.value)}
                      className="h-8 text-xs font-mono mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-muted-foreground text-[11px]">Post-Repair Vibration RMS (mm/s)</label>
                    <Input
                      value={postVibRms}
                      onChange={(e) => setPostVibRms(e.target.value)}
                      className="h-8 text-xs font-mono mt-1"
                    />
                  </div>
                </div>

                <div className="p-3 rounded bg-muted/20 border border-border/40 space-y-1.5 text-[11px]">
                  <div className="font-semibold text-foreground">Physical Verification Checklist:</div>
                  <div className="text-muted-foreground">✓ Asset tag P-101A verified</div>
                  <div className="text-muted-foreground">✓ SKF 22210 bearing installed per SOP-MECH-401</div>
                  <div className="text-muted-foreground">✓ Laser alignment confirmed (&lt; 15 um)</div>
                  <div className="text-muted-foreground">✓ Post-service vibration reduced below 2.8 mm/s (Zone A)</div>
                </div>

                <Button
                  onClick={handleSubmitEvidence}
                  disabled={loading || evidenceSubmitted || !order?.authorization_id}
                  className="w-full gap-2 text-xs"
                >
                  <FileCheck2Icon className="w-4 h-4" /> Submit & Validate Completion Evidence
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Lane B Dual-Control Supervisor Sign-Off & Final Capture */}
          {evidenceSubmitted && (
            <Card className="border-purple-500/30 bg-purple-500/5">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <UserCheckIcon className="w-5 h-5 text-purple-400" />
                    <CardTitle className="text-base text-foreground">Dual-Control Supervisor Sign-Off (Lane B)</CardTitle>
                  </div>
                  {supervisorSigned && (
                    <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-xs">
                      SUPERVISOR SIGNED
                    </Badge>
                  )}
                </div>
                <CardDescription>
                  Because P-101A is designated as a Critical Asset, human supervisor sign-off is mandatory before release of funds.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4 text-xs">
                {!supervisorSigned ? (
                  <div className="flex flex-col sm:flex-row items-center gap-3 p-3 rounded bg-card/60 border border-border/50">
                    <Input
                      value={supervisorId}
                      onChange={(e) => setSupervisorId(e.target.value)}
                      placeholder="Supervisor ID"
                      className="h-8 text-xs font-mono max-w-xs"
                    />
                    <Button size="sm" onClick={handleSupervisorSignOff} disabled={loading} className="gap-1.5 shrink-0">
                      <UserCheckIcon className="w-3.5 h-3.5" /> Sign-Off as Maintenance Supervisor
                    </Button>
                  </div>
                ) : (
                  <div className="p-3 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                    Supervisor signature confirmed: {supervisorId}. All dual-control prerequisites satisfied!
                  </div>
                )}

                {/* Final Capture Release Button */}
                <div className="pt-2">
                  <Button
                    onClick={handleAttemptCapture}
                    disabled={loading || !supervisorSigned || order?.status === "CAPTURED"}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white gap-2 text-xs font-semibold py-2.5"
                  >
                    <CheckCircle2Icon className="w-4 h-4" /> Execute Evidence-Gated Capture & Release Funds
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* SCREEN 4: TRANSACTION LINEAGE & AUDIT LEDGER */}
      {/* ========================================================================= */}
      {activeStage === 4 && auditLineage && (
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Immutable Transaction Lineage</CardTitle>
                  <CardDescription>
                    End-to-end causal chain from sensor vibration anomaly to PayPal capture settlement.
                  </CardDescription>
                </div>
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                  Status: {auditLineage.status}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="relative border-l-2 border-primary/40 ml-4 pl-6 space-y-6 text-xs">
                {auditLineage.lineage_stages.map((st) => (
                  <div key={st.step} className="relative group">
                    {/* Circle marker */}
                    <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                    </div>

                    <div className="p-3.5 rounded-lg border border-border/40 bg-card/60 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground text-sm">
                          Step {st.step}: {st.title}
                        </span>
                        <Badge variant="outline" className="text-[10px] font-mono">
                          {st.status || "COMPLETED"}
                        </Badge>
                      </div>

                      {st.detail && <p className="text-muted-foreground">{st.detail}</p>}
                      {st.diagnosis && <p className="text-muted-foreground">{st.diagnosis}</p>}
                      {st.order_id && (
                        <p className="font-mono text-[11px] text-blue-400">
                          PayPal Order ID: {st.order_id} ({st.amount})
                        </p>
                      )}
                      {st.authorization_id && (
                        <p className="font-mono text-[11px] text-purple-400">
                          Authorization ID: {st.authorization_id}
                        </p>
                      )}
                      {st.evidence_id && (
                        <p className="font-mono text-[11px] text-emerald-400">
                          Evidence ID: {st.evidence_id} (SHA-256 Verified)
                        </p>
                      )}
                      {st.capture_id && (
                        <p className="font-mono text-[11px] text-emerald-300 font-bold">
                          PayPal Capture ID: {st.capture_id}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>

            <CardFooter className="flex justify-between border-t border-border/40 pt-4">
              <Button variant="outline" onClick={handleReset} className="gap-2 text-xs">
                <RotateCcwIcon className="w-3.5 h-3.5" /> Run Scenario Again
              </Button>
            </CardFooter>
          </Card>
        </div>
      )}
    </div>
  );
}
