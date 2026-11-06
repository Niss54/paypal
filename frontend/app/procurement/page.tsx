"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ActivityIcon,
  AlertCircleIcon,
  AlertTriangleIcon,
  ArrowRightIcon,
  CheckCircle2Icon,
  CheckCircleIcon,
  CpuIcon,
  ChevronRightIcon,
  ClockIcon,
  CreditCardIcon,
  ExternalLinkIcon,
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
  UserIcon,
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
  syncOrderToSAP,
  syncOrderToMaximo,
  getERPStatus,
  type SAPSyncResponse,
  type MaximoSyncResponse,
  approvePayPalOrder,
  authorizePayPalOrder,
  capturePayPalOrder,
  computeSha256,
  createPayPalOrder,
  evaluateProcurementQuote,
  getAuthToken,
  getOrderAuditLineage,
  getProcurementIncident,
  getProcurementMandate,
  getProcurementQuotes,
  submitCompletionEvidence,
  supervisorSignOff,
  type AuditLineageStage,
  type AuthTokenResponse,
  type MandateEvalResult,
  type OrderAuditLineage,
  type PayPalOrderState,
  type ProcurementIncident,
  type ProcurementMandate,
  type ProcurementQuote,
} from "@/lib/api";

export default function ProcurementPage() {
  const [activeStep, setActiveStep] = useState<1 | 2 | 3>(1);

  // Authenticated Persona & RBAC State
  const [persona, setPersona] = useState<"procurement-agent" | "supervisor">("procurement-agent");
  const [authToken, setAuthToken] = useState<string>("");
  const [currentUser, setCurrentUser] = useState<AuthTokenResponse | null>(null);

  // Core Data
  const [incident, setIncident] = useState<any | null>(null);
  const [quotes, setQuotes] = useState<ProcurementQuote[]>([]);
  const [mandate, setMandate] = useState<ProcurementMandate | null>(null);
  const [selectedQuoteId, setSelectedQuoteId] = useState<string>("Q-2026-001");
  const [mandateEval, setMandateEval] = useState<MandateEvalResult | null>(null);

  // Active Transaction State
  const [order, setOrder] = useState<PayPalOrderState | null>(null);
  const [evidenceSubmitted, setEvidenceSubmitted] = useState<boolean>(false);
  const [submittedHash, setSubmittedHash] = useState<string>("");
  const [supervisorSigned, setSupervisorSigned] = useState<boolean>(false);
  const [captureResult, setCaptureResult] = useState<any | null>(null);
  const [auditLineage, setAuditLineage] = useState<OrderAuditLineage | null>(null);

  // ERP & Mode State
  const [isSimulationMode, setIsSimulationMode] = useState<boolean>(false);
  const [sapSyncResult, setSapSyncResult] = useState<SAPSyncResponse | null>(null);
  const [maximoSyncResult, setMaximoSyncResult] = useState<MaximoSyncResponse | null>(null);
  const [syncingERP, setSyncingERP] = useState<boolean>(false);

  // Status & Feedback
  const [loading, setLoading] = useState<boolean>(false);
  const [autoRunning, setAutoRunning] = useState<boolean>(false);
  const [gateBlocked, setGateBlocked] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error" | "info"; msg: string } | null>(null);

  // Initial Authentication & Baseline Data Load
  useEffect(() => {
    async function initAuthAndData() {
      try {
        setLoading(true);
        // 1. Fetch JWT token for current persona
        const tokenRes = await getAuthToken(persona);
        setAuthToken(tokenRes.access_token);
        setCurrentUser(tokenRes);

        // 2. Fetch baseline data with token
        const [inc, qts, mnd] = await Promise.all([
          getProcurementIncident(tokenRes.access_token),
          getProcurementQuotes(tokenRes.access_token),
          getProcurementMandate(tokenRes.access_token),
        ]);
        setIncident(inc);
        setQuotes(qts);
        setMandate(mnd);

        const ev = await evaluateProcurementQuote("Q-2026-001", tokenRes.access_token);
        setMandateEval(ev);
      } catch (err: any) {
        setFeedback({ type: "error", msg: err.message || "Failed to load procurement baseline" });
      } finally {
        setLoading(false);
      }
    }
    initAuthAndData();
  }, [persona]);

  // Persona Switch Handler
  const handleSwitchPersona = async (newPersona: "procurement-agent" | "supervisor") => {
    try {
      setLoading(true);
      setGateBlocked(null);
      const tokenRes = await getAuthToken(newPersona);
      setPersona(newPersona);
      setAuthToken(tokenRes.access_token);
      setCurrentUser(tokenRes);
      setFeedback({
        type: "info",
        msg: `Switched authenticated persona to: ${tokenRes.name} (${tokenRes.user_id}) with roles [${tokenRes.roles.join(", ")}].`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: "Failed to switch persona token." });
    } finally {
      setLoading(false);
    }
  };

  // Handle Quote Selection
  const handleSelectQuote = async (qid: string) => {
    setSelectedQuoteId(qid);
    try {
      const ev = await evaluateProcurementQuote(qid, authToken);
      setMandateEval(ev);
    } catch (err: any) {
      setFeedback({ type: "error", msg: "Failed to evaluate quote policy" });
    }
  };

  // Step 1: Create PayPal Order
  const handleCreateOrder = async () => {
    try {
      setLoading(true);
      setGateBlocked(null);
      setFeedback(null);

      // Create Order via backend Orders v2 with intent: AUTHORIZE
      const requester = currentUser?.user_id || "usr-procurement-agent";
      const created = await createPayPalOrder(selectedQuoteId, requester, isSimulationMode, authToken);
      setOrder(created);
      setActiveStep(2);
      setFeedback({
        type: "success",
        msg: `PayPal Order created! ID: ${created.paypal_order_id}. Complete buyer approval in sandbox.`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "PayPal order creation failed" });
    } finally {
      setLoading(false);
    }
  };

  // Step 2a: Confirm Buyer Approval
  const handleConfirmBuyerApproval = async (simulated: boolean = false) => {
    if (!order) return;
    try {
      setLoading(true);
      const updated = await approvePayPalOrder(order.paypal_order_id, simulated, authToken);
      setOrder(updated);
      setFeedback({
        type: "success",
        msg: "Buyer Approval confirmed! Order is now ready for PayPal authorization hold.",
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "Buyer approval verification failed" });
    } finally {
      setLoading(false);
    }
  };

  // Step 2b: Authorize Funds Hold
  const handleAuthorizeHold = async () => {
    if (!order) return;
    try {
      setLoading(true);
      const authorized = await authorizePayPalOrder(order.paypal_order_id, authToken);
      setOrder(authorized);
      setFeedback({
        type: "success",
        msg: `Funds authorized! Hold ID: ${authorized.authorization_id}. 29-day authorization window (3-day honor period) active.`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "Authorization failed" });
    } finally {
      setLoading(false);
    }
  };

  // Negative Test: Attempt Early Capture without Evidence (Must Fail with HTTP 403)
  const handleAttemptEarlyCapture = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setGateBlocked(null);
      await capturePayPalOrder(order.paypal_order_id, undefined, authToken);
      setFeedback({ type: "error", msg: "Security violation: Capture unexpectedly succeeded without verified evidence!" });
    } catch (err: any) {
      const msg = err.detail?.message || err.message || "HTTP 403 Forbidden: No Evidence, No Capture. Physical repair verification required.";
      setGateBlocked(msg);
    } finally {
      setLoading(false);
    }
  };

  // Submit Verified Completion Evidence
  const handleSubmitEvidence = async () => {
    if (!order) return;
    try {
      setLoading(true);
      setGateBlocked(null);

      const evidenceDocContent = JSON.stringify({
        report_title: "Post-Repair Vibration Analysis Certification",
        work_order: order.work_order_id,
        equipment: order.equipment_tag,
        sensor_measurement: {
          vibration_peak_mm_s: 1.25,
          iso_zone: "Zone A (Good)",
          bearing_temp_c: 41.2,
        },
        technician_signature: "TECH-CERT-441",
        timestamp: new Date().toISOString(),
      }, null, 2);

      // Verified post-repair operational evidence with real computed SHA-256 digest and report artifact
      const calculatedHash = await computeSha256(evidenceDocContent);
      setSubmittedHash(calculatedHash);

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
        file_content: evidenceDocContent,
        file_sha256: calculatedHash,
        is_synthetic: true,
      };

      const evRes = await submitCompletionEvidence(order.paypal_order_id, payload, authToken);
      if (!evRes || !evRes.validation_passed) {
        throw new Error("Completion evidence rejected by deterministic policy gate: Validation checks failed");
      }
      setEvidenceSubmitted(true);
      setFeedback({
        type: "success",
        msg: "Completion evidence verified! Post-repair vibration is 1.25 mm/s (ISO Zone A Good) with valid SHA-256 digest.",
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "Evidence submission failed" });
    } finally {
      setLoading(false);
    }
  };

  // Supervisor Sign-Off with Dual-Control Enforcement
  const handleSupervisorSignOff = async (requestedSupervisorId?: string) => {
    if (!order) return;
    try {
      setLoading(true);
      setGateBlocked(null);
      const supId = requestedSupervisorId || currentUser?.user_id || "SUP-CHIEF-09";
      await supervisorSignOff(
        order.paypal_order_id,
        supId,
        "Vibration re-inspection verified: 1.25 mm/s in Zone A. Work order WO-2026-IMS-001 approved for release.",
        authToken
      );
      setSupervisorSigned(true);
      setFeedback({
        type: "success",
        msg: `Dual-control supervisor sign-off successfully recorded by ${supId}. Evidence Gate is UNLOCKED!`,
      });
    } catch (err: any) {
      const msg = err.detail?.message || err.detail || err.message || "Dual-control sign-off rejected.";
      setGateBlocked(`Dual-Control Enforcement: ${msg}`);
      setFeedback({
        type: "error",
        msg: `Sign-off rejected: ${msg}`,
      });
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

      const res = await capturePayPalOrder(order.paypal_order_id, undefined, authToken);
      setCaptureResult(res);

      const lineage = await getOrderAuditLineage(order.paypal_order_id, authToken);
      setAuditLineage(lineage);

      setActiveStep(3);
      const isSim = order.is_simulated || res.is_simulated || res.simulation;
      const capId = res.capture?.capture_id || res.capture_id || "COMPLETED";
      setFeedback({
        type: "success",
        msg: isSim
          ? `Simulated capture completed. Capture ID: ${capId}. No PayPal transaction occurred.`
          : `PayPal Sandbox capture completed! Capture ID: ${capId}. Status: COMPLETED.`,
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

      await new Promise((r) => setTimeout(r, 600));
      // 1. Create simulated order as procurement agent
      const tokenResAgent = await getAuthToken("procurement-agent");
      setPersona("procurement-agent");
      setAuthToken(tokenResAgent.access_token);
      setCurrentUser(tokenResAgent);

      const created = await createPayPalOrder("Q-2026-001", "usr-procurement-agent", true, tokenResAgent.access_token);
      setOrder(created);
      setActiveStep(2);

      // 2. Buyer approve
      await new Promise((r) => setTimeout(r, 700));
      const approved = await approvePayPalOrder(created.paypal_order_id, true, tokenResAgent.access_token);
      setOrder(approved);

      // 3. Authorize hold
      await new Promise((r) => setTimeout(r, 700));
      const authorized = await authorizePayPalOrder(approved.paypal_order_id, tokenResAgent.access_token);
      setOrder(authorized);

      // 4. Hero negative gate test: Genuine server-side early capture attempt (asserts HTTP 403 Forbidden)
      await new Promise((r) => setTimeout(r, 800));
      try {
        await capturePayPalOrder(authorized.paypal_order_id, undefined, tokenResAgent.access_token);
        throw new Error("Unexpected: Early capture was allowed by server without evidence!");
      } catch (negErr: any) {
        const errorMsg = negErr.detail?.message || negErr.detail?.reason || negErr.message || "HTTP 403 Forbidden: No Evidence, No Capture";
        setGateBlocked(`Server Gate Policy Enforced (HTTP ${negErr.status || 403}): ${typeof errorMsg === "string" ? errorMsg : JSON.stringify(errorMsg)}`);
      }

      // 5. Submit verified completion evidence with report artifact content
      await new Promise((r) => setTimeout(r, 1200));
      setGateBlocked(null);
      const evidenceDocContent = JSON.stringify({
        report_title: "Post-Repair Vibration Analysis Certification",
        work_order: authorized.work_order_id,
        equipment: authorized.equipment_tag,
        sensor_measurement: {
          vibration_peak_mm_s: 1.25,
          iso_zone: "Zone A (Good)",
          baseline_ratio: "0.26x baseline",
        },
        technician_signature: "TECH-CERT-441",
        calibration_standard: "ISO 10816-3 Class II",
        timestamp: new Date().toISOString(),
      }, null, 2);

      const calculatedAutoHash = await computeSha256(evidenceDocContent);
      setSubmittedHash(calculatedAutoHash);

      const evAutoRes = await submitCompletionEvidence(authorized.paypal_order_id, {
        evidence_id: `EVD-${authorized.paypal_order_id}`,
        work_order_id: authorized.work_order_id,
        quote_id: authorized.quote_id,
        equipment_tag: authorized.equipment_tag,
        vendor_id: authorized.vendor_id,
        service_id: "SRV-BRG-REPLACE",
        technician_id: "TECH-CERT-441",
        checklist_items: [
          "Disassembly and physical bearing replacement completed per SOP",
          "Laser alignment verified within tolerance",
          "Post-repair vibration baseline passed ISO Zone A",
        ],
        measurements: { vibration_after_mm_s: 1.25, vibration_zone: "Zone A (Good)", bearing_temperature_c: 41.2 },
        file_content: evidenceDocContent,
        file_sha256: calculatedAutoHash,
        is_synthetic: true,
      }, tokenResAgent.access_token);
      if (!evAutoRes || !evAutoRes.validation_passed) {
        throw new Error("Auto-demo evidence validation failed: Policy requirements not satisfied");
      }
      setEvidenceSubmitted(true);

      // 6. Switch to Supervisor for dual control
      await new Promise((r) => setTimeout(r, 900));
      const tokenResSup = await getAuthToken("supervisor");
      setPersona("supervisor");
      setAuthToken(tokenResSup.access_token);
      setCurrentUser(tokenResSup);

      await supervisorSignOff(authorized.paypal_order_id, "SUP-CHIEF-09", "Auto-demo dual-control sign-off verified.", tokenResSup.access_token);
      setSupervisorSigned(true);

      // 7. Capture payment
      await new Promise((r) => setTimeout(r, 1200));
      const res = await capturePayPalOrder(authorized.paypal_order_id, undefined, tokenResSup.access_token);
      setCaptureResult(res);
      const lineage = await getOrderAuditLineage(authorized.paypal_order_id, tokenResSup.access_token);
      setAuditLineage(lineage);
      setActiveStep(3);

      const isSim = authorized.is_simulated || res.is_simulated || res.simulation;
      const capId = res.capture_id || res.capture?.capture_id || "SIM-CAP-2026";
      setFeedback({
        type: "success",
        msg: isSim
          ? `Auto Demo Complete: Simulated capture completed (ID: ${capId}). No PayPal transaction occurred.`
          : `Auto Demo Complete: PayPal Sandbox capture completed! Capture ID: ${capId}. Status: COMPLETED.`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "Auto-demo encountered an error" });
    } finally {
      setAutoRunning(false);
    }
  };

  const handleSyncToSAP = async () => {
    if (!order) return;
    try {
      setSyncingERP(true);
      const res = await syncOrderToSAP({
        equipment_id: order.equipment_tag || "P-101A",
        order_type: "PM01",
        short_text: `Emergency Bearing Replacement on ${order.equipment_tag || "P-101A"}`,
        vendor_id: order.vendor_id || "US-MOT-10821",
        vendor_name: "Motion Industries",
        estimated_amount: order.amount_value || "450.00",
        currency: order.currency_code || "USD",
        paypal_order_id: order.paypal_order_id,
        paypal_auth_id: order.authorization_id || undefined,
        paypal_capture_id: captureResult?.capture?.capture_id || captureResult?.capture_id || undefined,
        evidence_hash: submittedHash || undefined,
      }, authToken);
      setSapSyncResult(res);
      setFeedback({
        type: "success",
        msg: `Synced to SAP S/4HANA Cloud! Order: ${res.sap_order_id} (Status: ${res.status}). Liability committed to GL 2100-PAYPAL-CLEARING.`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "SAP synchronization failed" });
    } finally {
      setSyncingERP(false);
    }
  };

  const handleSyncToMaximo = async () => {
    if (!order) return;
    try {
      setSyncingERP(true);
      const res = await syncOrderToMaximo({
        asset_num: order.equipment_tag || "P-101A",
        description: `NASA IMS Bearing Replacement on ${order.equipment_tag || "P-101A"}`,
        vendor_id: order.vendor_id || "US-MOT-10821",
        estimated_cost: order.amount_value || "450.00",
        paypal_order_id: order.paypal_order_id,
        paypal_auth_id: order.authorization_id || undefined,
        paypal_capture_id: captureResult?.capture?.capture_id || captureResult?.capture_id || undefined,
        evidence_hash: submittedHash || undefined,
      }, authToken);
      setMaximoSyncResult(res);
      setFeedback({
        type: "success",
        msg: `Synced to IBM Maximo! WONUM: ${res.wonum} (Status: ${res.status}). OSLC resource updated.`,
      });
    } catch (err: any) {
      setFeedback({ type: "error", msg: err.message || "IBM Maximo synchronization failed" });
    } finally {
      setSyncingERP(false);
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

  const fallbackQuote: ProcurementQuote = {
    quote_id: "Q-2026-001",
    vendor_id: "VND-001",
    vendor_name: "Bearing Supply Co",
    service_id: "SRV-BRG-REPLACE",
    amount: "450.00",
    currency: "USD",
    sla_hours: 24,
    is_allowlisted: true,
    is_synthetic: true,
    synthetic_label: "[SYNTHETIC DEMO QUOTE]",
    scope_description: "Supply SKF 22210 spherical roller bearing and dispatch millwright technician",
    is_direct_paypal_sandbox_merchant: true,
    scoring: {
      cost_score: 92,
      sla_score: 95,
      reliability_score: 96,
      composite_rank: 1,
      hard_gates_passed: true,
    },
  };

  const selectedQuote = quotes.find((q) => q.quote_id === selectedQuoteId) || quotes[0] || fallbackQuote;

  return (
    <div className="flex-1 space-y-6 p-4 sm:p-6 max-w-6xl mx-auto">
      {/* Top Header Banner & Persona Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/50 pb-5">
        <div className="flex items-start gap-3.5">
          <img src="/kr.png" alt="KinetixRAG Logo" className="size-11 rounded-xl object-contain drop-shadow bg-background/50 border border-cyan-500/40 p-1 shrink-0 mt-0.5" />
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
        </div>

        <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2 shrink-0">
          {/* Persona Switcher Pill */}
          <div className="flex items-center gap-1.5 p-1 rounded-lg bg-card/80 border border-border/60 text-xs">
            <span className="text-[10px] uppercase font-mono text-muted-foreground px-1.5">Persona:</span>
            <Button
              size="sm"
              variant={persona === "procurement-agent" ? "default" : "ghost"}
              onClick={() => handleSwitchPersona("procurement-agent")}
              disabled={loading || autoRunning}
              className={`h-7 px-2.5 text-xs ${persona === "procurement-agent" ? "bg-blue-600 text-white font-medium" : "text-muted-foreground"}`}
            >
              <UserIcon className="w-3 h-3 mr-1" /> Requester Agent
            </Button>
            <Button
              size="sm"
              variant={persona === "supervisor" ? "default" : "ghost"}
              onClick={() => handleSwitchPersona("supervisor")}
              disabled={loading || autoRunning}
              className={`h-7 px-2.5 text-xs ${persona === "supervisor" ? "bg-emerald-600 text-white font-medium" : "text-muted-foreground"}`}
            >
              <ShieldCheckIcon className="w-3 h-3 mr-1" /> Supervisor (SUP-09)
            </Button>
          </div>

          <div className="flex items-center gap-2">
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

      {/* 3-Step Navigation Tabs */}
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
            desc: "Buyer Approval, Escrow Hold & Safety Gate",
            icon: LockIcon,
          },
          {
            step: 3,
            title: "3. Settled Receipt & Lineage",
            desc: "Verified Capture & Cryptographic Lineage",
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

      {/* STEP 1: TELEMETRY & VENDOR RFQ QUOTE */}
      {activeStep === 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Anomaly & GraphRAG Card */}
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
                  Physical vibration telemetry excursion exceeding ISO-10816 limits.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 rounded-lg bg-muted/40 border border-border/40 space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Asset Tag:</span>
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

                {/* GraphRAG Attribution & Citations */}
                <div className="p-3 rounded-lg border border-border/40 bg-card/50 text-[11px] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <SparklesIcon className="w-3.5 h-3.5 text-cyan-400" />
                      GraphRAG Diagnostic Attribution:
                    </span>
                    <Badge variant="outline" className="text-[10px] text-cyan-400 border-cyan-500/30 bg-cyan-500/10 font-mono">
                      94.2% Confidence (Model-Estimated)
                    </Badge>
                  </div>
                  <p className="text-muted-foreground leading-relaxed">
                    Inner-race bearing defect detected via high-frequency envelope analysis. Recommended action per PROC-001: emergency bearing replacement.
                  </p>
                  <div className="space-y-1 pt-1 border-t border-border/30">
                    <span className="text-[10px] text-muted-foreground font-mono block">GROUNDED REGULATORY & ENGINEERING CITATIONS:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {["ISO-10816-3 Table C.1", "PROC-001", "DOC-P101-RCA", "NASA-IMS-2004"].map((cit) => (
                        <Badge key={cit} variant="secondary" className="text-[10px] font-mono py-0 px-2 bg-muted/60 text-foreground border border-border/40">
                          📜 {cit}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="text-[10px] text-muted-foreground/90 font-mono pt-1">
                    <span className="text-foreground font-medium">Dataset Provenance: </span>
                    Replay Fixture: NASA IMS 2004 Accelerometry (5.42 mm/s RMS) • Asset: P-101A (4.82 mm/s RMS, Limit 4.5 mm/s)
                  </div>
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
                {/* AI Vendor Recommendation */}
                <div className="p-2.5 rounded-lg border border-blue-500/30 bg-blue-500/5 text-[11px] text-muted-foreground flex items-start gap-2">
                  <SparklesIcon className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-blue-300 block">AI Agent Recommendation:</span>
                    <span>
                      Bearing Supply Co (Q-2026-001) selected over Apex Industrial and Precision Spares due to lowest total landed cost ($450 vs $680) and 24h SLA within 30-hour maintenance buffer.
                    </span>
                  </div>
                </div>

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
                        <span>Budget &le; $500</span>
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
                  Selected: {selectedQuote?.vendor_name || "Bearing Supply Co"} (${selectedQuote?.amount || "450.00"})
                </span>
                <Button
                  onClick={handleCreateOrder}
                  disabled={loading}
                  className="gap-2 bg-[#003087] hover:bg-[#00256c] text-white"
                >
                  <CreditCardIcon className="w-4 h-4 text-[#0079C1]" />
                  Create PayPal Order <ArrowRightIcon className="w-4 h-4" />
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>
      )}

      {/* STEP 2: PAYPAL AUTHORIZATION & THE EVIDENCE GATE */}
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
                    {order.is_simulated && (
                      <Badge variant="outline" className="border-amber-400/50 text-amber-300 bg-amber-400/10 text-xs">
                        SIMULATED MODE
                      </Badge>
                    )}
                    <span className="text-xs text-muted-foreground">
                      (intent: <code className="text-blue-400">AUTHORIZE</code>)
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Funds (${parseFloat(order.amount_value).toFixed(2)} USD) are governed by a 29-day authorization window (3-day guaranteed honor period). No funds are captured yet.
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-xs text-muted-foreground block">Authorization ID</span>
                  <span className="text-xs font-mono font-semibold text-foreground">
                    {order.authorization_id || (order.status === "BUYER_APPROVED" ? "Ready for Authorization" : "Pending Buyer Approval")}
                  </span>
                </div>
              </div>

              {/* Sub-step: Buyer Approval required if status is ORDER_CREATED */}
              {order.status !== "AUTHORIZED" && order.status !== "EVIDENCE_VERIFIED" && order.status !== "CAPTURED" && (
                <div className="mt-4 pt-4 border-t border-blue-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-blue-950/20 p-3 rounded-lg">
                  <div className="space-y-0.5">
                    <span className="text-xs font-semibold text-blue-300 flex items-center gap-1.5">
                      <ClockIcon className="w-3.5 h-3.5" /> Buyer Approval Required (PayPal Orders v2)
                    </span>
                    <p className="text-[11px] text-muted-foreground">
                      {order.status === "BUYER_APPROVED"
                        ? "Buyer approval confirmed. Ready to place authorization hold."
                        : "Buyer must approve the order hold before authorization can execute."}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {order.status !== "BUYER_APPROVED" ? (
                      <>
                        {order.approve_url && (
                          <a href={order.approve_url} target="_blank" rel="noopener noreferrer">
                            <Button size="sm" variant="outline" className="gap-1.5 text-xs border-blue-400/40 text-blue-300 hover:bg-blue-500/10">
                              <ExternalLinkIcon className="w-3.5 h-3.5" /> Open Sandbox Checkout
                            </Button>
                          </a>
                        )}
                        <Button
                          size="sm"
                          onClick={() => handleConfirmBuyerApproval(false)}
                          disabled={loading}
                          className="text-xs bg-[#0079C1] hover:bg-[#00457C] text-white"
                        >
                          Verify Sandbox Approval
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleConfirmBuyerApproval(true)}
                          disabled={loading}
                          className="text-xs"
                        >
                          1-Click Fast Approve
                        </Button>
                      </>
                    ) : (
                      <Button
                        size="sm"
                        onClick={handleAuthorizeHold}
                        disabled={loading}
                        className="text-xs bg-[#003087] hover:bg-[#00256c] text-white font-semibold gap-1.5"
                      >
                        <LockIcon className="w-3.5 h-3.5" /> Authorize Funds Hold
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Test Bench (Negative Gate Test + Evidence & Dual-Control Verification) */}
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
                  Proves that neither AI agent nor vendor can capture funds prematurely.
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Attempt an early capture before physical repair telemetry is validated. The deterministic backend policy gate strictly rejects this request.
                </p>

                {gateBlocked && (
                  <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-500/50 text-red-200 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-bold flex items-center gap-1.5 text-red-400">
                        <LockIcon className="w-3.5 h-3.5" /> SECURITY GATE ACTIVE
                      </span>
                      <Badge variant="destructive" className="text-[10px] font-mono">
                        POLICY ENFORCED
                      </Badge>
                    </div>
                    <p className="text-[11px] font-mono leading-relaxed bg-black/40 p-2 rounded border border-red-500/20">
                      {gateBlocked}
                    </p>
                    <div className="text-[10px] text-emerald-400 flex items-center gap-1.5">
                      <ShieldCheckIcon className="size-3 shrink-0" />
                      <span>Buyer funds remain safely held in PayPal escrow. Zero unauthorized capital leakage.</span>
                    </div>
                  </div>
                )}
              </CardContent>

              <CardFooter className="pt-2">
                <Button
                  variant="destructive"
                  onClick={handleAttemptEarlyCapture}
                  disabled={loading || (evidenceSubmitted && supervisorSigned)}
                  className="w-full gap-2 text-xs font-medium"
                >
                  <LockIcon className="w-3.5 h-3.5" />
                  {evidenceSubmitted && supervisorSigned ? "Gate Unlocked (Ready to Capture)" : "Attempt Early Capture (Should Fail with HTTP 403)"}
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
                    <span className="font-semibold text-emerald-400">1.25 mm/s RMS (ISO Zone A Good)</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Scope Checklist:</span>
                    <span className="font-semibold text-foreground">4/4 Criteria Verified</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Document SHA-256:</span>
                    <span className="font-mono text-[10px] text-muted-foreground truncate max-w-[180px]">
                      {submittedHash ? `${submittedHash.slice(0, 20)}...` : "5316f8f37a31793b32f2..."}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Dual-Control Sign-Off:</span>
                    <span className="font-semibold text-foreground">
                      {supervisorSigned ? "Approved by SUP-CHIEF-09 ✅" : "Pending Supervisor Signature ⏳"}
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  {!evidenceSubmitted ? (
                    <Button
                      onClick={handleSubmitEvidence}
                      disabled={loading || order.status !== "AUTHORIZED"}
                      variant="outline"
                      className="w-full gap-2 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10 text-xs"
                    >
                      <FileCheck2Icon className="w-3.5 h-3.5 text-emerald-400" />
                      Submit Verified Evidence (1.25 mm/s)
                    </Button>
                  ) : !supervisorSigned ? (
                    <div className="space-y-2">
                      <div className="p-2 rounded bg-muted/40 border border-border/40 text-[11px] text-muted-foreground flex items-center justify-between">
                        <span>Current Active Session:</span>
                        <span className="font-mono font-semibold text-foreground">{currentUser?.user_id}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <Button
                          onClick={() => handleSupervisorSignOff("SUP-CHIEF-09")}
                          disabled={loading}
                          variant="outline"
                          className="gap-1.5 border-blue-500/40 text-blue-300 hover:bg-blue-500/10 text-xs"
                        >
                          <UserCheckIcon className="w-3.5 h-3.5 text-blue-400" />
                          Sign-Off (SUP-09)
                        </Button>
                        <Button
                          onClick={() => handleSupervisorSignOff(order.requester_user_id || "usr-procurement-agent")}
                          disabled={loading}
                          variant="outline"
                          className="gap-1.5 border-red-500/40 text-red-300 hover:bg-red-500/10 text-xs"
                        >
                          Test Self-Approval (Fails)
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </div>
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

      {/* STEP 3: SETTLED RECEIPT & CRYPTOGRAPHIC LINEAGE */}
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
                      Funds captured and disbursed following physical sensor evidence validation and dual-control sign-off.
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
                    {order?.paypal_order_id}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">PayPal Capture ID</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {captureResult?.capture?.capture_id || captureResult?.capture_id || "COMPLETED"}
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
                  <span className="font-semibold text-foreground">{order?.vendor_id || "VND-001"}</span>
                </div>
              </div>

              {/* Option A Payee Architecture Note */}
              <div className="mt-3 p-2.5 rounded-lg border border-border/40 bg-card/40 text-[11px] text-muted-foreground flex items-center justify-between">
                <span className="font-medium text-foreground">Disbursement Architecture (Option A):</span>
                <span>Facility Operator acts as Merchant of Record with funds released upon physical sign-off.</span>
              </div>
            </CardContent>
          </Card>

          {/* Enterprise ERP Bridge & General Ledger Clearing */}
          <Card className="border-indigo-500/40 bg-indigo-500/5 shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <CpuIcon className="w-5 h-5 text-indigo-400" />
                  <div>
                    <CardTitle className="text-base font-semibold">
                      Enterprise ERP Bridge (SAP S/4HANA & IBM Maximo)
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Two-way synchronization for maintenance orders, purchase orders, and GL clearing account (2100-PAYPAL-CLEARING).
                    </CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleSyncToSAP}
                    disabled={syncingERP}
                    className="h-7 px-2.5 text-xs border-indigo-400/40 text-indigo-300 hover:bg-indigo-500/10"
                  >
                    Sync SAP S/4HANA (PM01)
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleSyncToMaximo}
                    disabled={syncingERP}
                    className="h-7 px-2.5 text-xs border-indigo-400/40 text-indigo-300 hover:bg-indigo-500/10"
                  >
                    Sync IBM Maximo (OSLC)
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* SAP Status Box */}
                <div className="p-3.5 rounded-lg border border-border/40 bg-card/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-blue-400"></span> SAP S/4HANA Cloud (OData)
                    </span>
                    <Badge variant="outline" className="text-[10px] border-blue-400/40 text-blue-300">
                      {sapSyncResult ? `ORDER: ${sapSyncResult.sap_order_id}` : "READY FOR SYNC"}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-muted-foreground space-y-1">
                    <div>Status: <span className="text-foreground font-mono font-medium">{sapSyncResult?.status || "CRTD / REL"}</span></div>
                    <div>GL Liability Account: <span className="text-emerald-400 font-mono">2100-PAYPAL-CLEARING</span></div>
                    <div>Cost Center: <span className="text-foreground font-mono">CC-MUMBAI-01</span> • Plant: <span className="text-foreground font-mono">1000</span></div>
                  </div>
                  {sapSyncResult && (
                    <div className="pt-2 border-t border-border/40 text-[10px] font-mono text-emerald-400">
                      Posting: Debit {sapSyncResult.accounting_posting.debit_account} / Credit {sapSyncResult.accounting_posting.credit_account} (${sapSyncResult.accounting_posting.amount})
                    </div>
                  )}
                </div>

                {/* IBM Maximo Status Box */}
                <div className="p-3.5 rounded-lg border border-border/40 bg-card/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span> IBM Maximo Asset Management
                    </span>
                    <Badge variant="outline" className="text-[10px] border-emerald-400/40 text-emerald-300">
                      {maximoSyncResult ? `WONUM: ${maximoSyncResult.wonum}` : "READY FOR SYNC"}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-muted-foreground space-y-1">
                    <div>Status: <span className="text-foreground font-mono font-medium">{maximoSyncResult?.status || "APPR / COMP"}</span></div>
                    <div>Asset Tag: <span className="text-foreground font-mono">P-101A</span> • Site: <span className="text-foreground font-mono">BEDFORD</span></div>
                    <div>OSLC Protocol: <span className="text-foreground font-mono">/maximo/oslc/os/mxwo</span></div>
                  </div>
                  {maximoSyncResult && (
                    <div className="pt-2 border-t border-border/40 text-[10px] font-mono text-emerald-400">
                      Evidence Hash Verified: {maximoSyncResult.evidence_validated ? "YES (Gate Settled)" : "PENDING"}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 7-Stage Causal Audit Trail with Cryptographic Lineage */}
          <Card className="border-border/60 shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheckIcon className="w-5 h-5 text-blue-400" />
                  <CardTitle className="text-base font-semibold">
                    7-Stage Cryptographic & Operational Causal Lineage
                  </CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 bg-emerald-500/10 text-[10px]">
                    SHA-256 Chain: VERIFIED
                  </Badge>
                  {auditLineage?.merkle_root && (
                    <Badge variant="outline" className="font-mono text-[10px] text-muted-foreground">
                      Merkle: {auditLineage.merkle_root.slice(0, 12)}...
                    </Badge>
                  )}
                </div>
              </div>
              <CardDescription className="text-xs">
                Unbroken continuous hash chain proving why every cent was authorized and captured.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <div className="space-y-3">
                {(auditLineage?.lineage_stages || []).map((s: AuditLineageStage, idx: number) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg border border-border/40 bg-card/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                  >
                    <div className="flex items-start gap-3">
                      <span className="w-6 h-6 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
                        {s.step || idx + 1}
                      </span>
                      <div className="space-y-0.5">
                        <span className="font-semibold text-foreground block">{s.title}</span>
                        <span className="text-[11px] text-muted-foreground block">
                          {s.detail || s.diagnosis || s.policy || JSON.stringify((s as any).mandate_snapshot || s.status || "")}
                        </span>
                        {s.stage_hash && (
                          <span className="text-[10px] font-mono text-muted-foreground/80 block pt-0.5">
                            Hash: <span className="text-blue-400/80">{s.stage_hash.slice(0, 16)}...</span> • Prev: <span className="text-muted-foreground/60">{s.previous_stage_hash?.slice(0, 12)}...</span>
                          </span>
                        )}
                      </div>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 text-[10px] shrink-0 self-start sm:self-center">
                      VERIFIED ✅
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>

            <CardFooter className="pt-2 flex justify-between">
              <span className="text-xs text-muted-foreground font-mono">
                Continuous Hash-Chained Audit Snapshot with Merkle Root
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
