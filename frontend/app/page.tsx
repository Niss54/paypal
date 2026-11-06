import Link from "next/link";
import {
  ArrowRightIcon,
  CreditCardIcon,
  BrainCircuitIcon,
  FileCheck2Icon,
  GaugeIcon,
  NetworkIcon,
  SearchIcon,
  ShieldCheckIcon,
  ShieldAlertIcon,
  SparklesIcon,
  WorkflowIcon,
  ZapIcon,
  CheckCircle2Icon,
  LockIcon,
  ScaleIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const coverage = [
  {
    label: "Two-Phase Settlement",
    value: "29 Days",
    detail: "PayPal Orders v2 authorized escrow hold (intent: AUTHORIZE)",
    icon: CreditCardIcon,
  },
  {
    label: "Evidence-Gated Capture",
    value: "100% Gated",
    detail: "Strict HTTP 403 blocks capture until physical repair verified",
    icon: ShieldCheckIcon,
  },
  {
    label: "Empirical Telemetry",
    value: "20 kHz RMS",
    detail: "Real NASA IMS Run-to-Failure vibration dataset (ISO 10816)",
    icon: GaugeIcon,
  },
  {
    label: "Cryptographic Lineage",
    value: "07 Stages",
    detail: "Sensor ➔ GraphRAG ➔ WO ➔ Mandate ➔ Auth ➔ Proof ➔ Capture",
    icon: NetworkIcon,
  },
];

const workflow = [
  {
    step: "01",
    title: "SENSE (Empirical IoT)",
    detail: "Accelerometers detect bearing degradation (NASA IMS 4.82 mm/s RMS Zone C/D breach).",
    icon: GaugeIcon,
  },
  {
    step: "02",
    title: "DIAGNOSE (GraphRAG)",
    detail: "Deterministic hybrid retrieval isolates inner race wear & drafts Work Order WO-2026-IMS-001.",
    icon: BrainCircuitIcon,
  },
  {
    step: "03",
    title: "GOVERN (Spending Mandate)",
    detail: "Server enforces strict $500 cap, USD currency gate, vendor allowlist, and Lane B dual-control.",
    icon: WorkflowIcon,
  },
  {
    step: "04",
    title: "SETTLE (PayPal Orders v2)",
    detail: "Two-phase settlement: 29-day authorization hold + evidence-gated capture upon physical verification.",
    icon: CreditCardIcon,
  },
];

const enterprisePillars = [
  {
    title: "29-Day Authorized Hold (Zero Upfront Loss)",
    detail: "Blockchains force immediate irrevocable settlement. PayPal Orders v2 holds buyer funds safely in authorized status for up to 29 days without capital lockup.",
    badge: "PayPal Orders v2",
  },
  {
    title: "Physical Evidence Gate (HTTP 403 Block)",
    detail: "Non-negotiable server invariant (NO_EVIDENCE_NO_CAPTURE) strictly rejects capture requests until post-repair vibration drops below the ISO 4.5 mm/s threshold.",
    badge: "Safety Invariant",
  },
  {
    title: "Enterprise GAAP & Dispute Arbitration",
    detail: "Enterprises cannot hold volatile crypto on balance sheets. PayPal guarantees USD fiat stability, SAP ERP GL reconciliation, and commercial dispute protection.",
    badge: "Enterprise Ready",
  },
];

export default function CommandCenterPage() {
  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-6">
      {/* Flagship Hero Section */}
      <section className="overflow-hidden rounded-2xl bg-card shadow-xs ring-1 ring-foreground/10 border border-[#003087]/30">
        <div className="grid lg:grid-cols-[minmax(0,1.25fr)_minmax(380px,0.75fr)]">
          <div className="flex flex-col justify-center p-6 sm:p-8 lg:p-10">
            <div className="flex items-center gap-3.5 mb-2">
              <img src="/kr.png" alt="KinetixRAG Logo" className="size-12 rounded-xl object-contain drop-shadow bg-background/50 border border-cyan-500/40 p-1 shrink-0" />
              <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-[#003087] hover:bg-[#00256c] text-white border-0 text-xs font-mono flex items-center gap-1.5 py-1 px-2.5">
                <CreditCardIcon className="size-3.5" />
                PayPal AI Hackathon 2026
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-amber-500/40 text-amber-500 bg-amber-500/10">
                Best Use of Agentic Commerce
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-cyan-500/40 text-cyan-400 bg-cyan-950/20">
                NASA IMS Bearing Telemetry
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-emerald-500/40 text-emerald-400 bg-emerald-950/20">
                PayPal Orders v2
              </Badge>
              </div>
            </div>

            <h1 className="mt-4 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-4xl text-foreground">
              Industrial machines holding autonomous PayPal spending mandates.
              <span className="block mt-1 text-transparent bg-clip-text bg-gradient-to-r from-[#0079C1] via-[#00457C] to-amber-400 dark:from-cyan-400 dark:via-blue-400 dark:to-amber-400">
                &ldquo;No Evidence, No Capture&rdquo; — Two-Phase Settlement Prevents Spend Leakage.
              </span>
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base sm:leading-7">
              When industrial IoT sensors detect imminent equipment failure, autonomous AI agents cannot make blind upfront payments.
              <strong> KinetixRAG</strong> combines empirical NASA IMS vibration telemetry, GraphRAG root-cause diagnosis,
              deterministic spending mandates, and <strong>PayPal Orders v2 Two-Phase Settlement (<code className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded text-foreground">intent: AUTHORIZE</code>)</strong>.
              Contractor payment is placed on a 29-day authorized escrow hold and strictly blocked (HTTP 403) until post-repair vibration telemetry verifies physical asset restoration.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button
                size="lg"
                className="bg-[#003087] hover:bg-[#00256c] text-white font-bold shadow-lg shadow-blue-500/25 border-0 text-sm gap-2"
                nativeButton={false}
                render={<Link href="/procurement" />}
              >
                <CreditCardIcon className="size-4 text-[#0079C1]" />
                Launch 1-Click PayPal Procurement Console
                <ArrowRightIcon className="size-4" />
              </Button>

              <Button
                size="lg"
                variant="outline"
                className="border-amber-500/40 hover:bg-amber-500/10 text-amber-500 font-medium text-sm gap-1.5"
                nativeButton={false}
                render={<Link href="/procurement" />}
              >
                <SparklesIcon className="size-4" />
                Judge Fast-Track Demo
              </Button>

              <Button
                size="lg"
                variant="outline"
                className="border-cyan-500/40 hover:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 font-medium text-sm"
                nativeButton={false}
                render={<Link href="/predictive-watch" />}
              >
                <GaugeIcon className="size-4" />
                NASA Telemetry Triggers
              </Button>

              <Button
                size="lg"
                variant="outline"
                className="text-muted-foreground hover:text-foreground text-sm"
                nativeButton={false}
                render={<Link href="/investigate" />}
              >
                GraphRAG Evidence
              </Button>
            </div>
          </div>

          {/* Side Thesis Card: Why PayPal Wins Over Crypto */}
          <div className="flex flex-col justify-between gap-6 border-t bg-muted/20 p-6 lg:border-t-0 lg:border-l lg:p-8">
            <div>
              <div className="text-xs font-semibold tracking-wider text-[#0079C1] dark:text-cyan-400 uppercase flex items-center gap-1.5 font-mono">
                <ScaleIcon className="size-3.5" />
                The Agentic Commerce Thesis
              </div>
              <p className="mt-3 font-heading text-base font-semibold leading-6 text-foreground">
                Why Enterprise AI Requires PayPal Orders v2 Rather Than Crypto Smart Contracts
              </p>
            </div>

            <div className="grid gap-3 font-mono text-xs">
              {enterprisePillars.map((p) => (
                <div key={p.title} className="rounded-xl border border-[#003087]/30 bg-[#003087]/5 p-3.5 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-blue-400 font-bold uppercase tracking-wider">
                      {p.title}
                    </span>
                    <Badge variant="outline" className="text-[9px] border-blue-500/30 text-blue-300">
                      {p.badge}
                    </Badge>
                  </div>
                  <div className="text-muted-foreground text-[11px] leading-snug font-sans">
                    {p.detail}
                  </div>
                </div>
              ))}
            </div>

            <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/30 p-2.5 flex items-center gap-2 text-xs text-emerald-400">
              <CheckCircle2Icon className="size-4 shrink-0 text-emerald-400" />
              <span><strong>385 Backend Tests & 65 Frontend Tests</strong> passing 100% green against live sandbox APIs.</span>
            </div>
          </div>
        </div>
      </section>

      {/* Coverage & Architecture Pillars */}
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Platform coverage">
        {coverage.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.label} size="sm" className="border-border/60 hover:border-primary/40 transition-colors">
              <CardHeader>
                <CardTitle className="text-muted-foreground text-xs uppercase tracking-wider font-semibold">
                  {item.label}
                </CardTitle>
                <CardAction>
                  <div className="grid size-9 place-items-center rounded-lg bg-[#003087]/15 text-[#0079C1] dark:text-cyan-400">
                    <Icon className="size-4" />
                  </div>
                </CardAction>
              </CardHeader>
              <CardContent>
                <div className="data-mono text-2xl font-bold tracking-tight text-foreground">{item.value}</div>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.detail}</p>
              </CardContent>
            </Card>
          );
        })}
      </section>

      {/* 4-Step Autonomous Execution Flow */}
      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
        <Card className="border-border/60">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CreditCardIcon className="size-4 text-[#0079C1]" />
              <CardTitle>How KinetixRAG Safely Executes PayPal Agentic Commerce</CardTitle>
            </div>
            <CardDescription>
              From high-frequency NASA IMS accelerometry spikes to evidence-gated settlement under non-negotiable enterprise mandates.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {workflow.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.step} className="flex gap-4 rounded-xl border border-border/60 bg-card/60 p-4 hover:border-[#003087]/50 transition-colors">
                  <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-[#003087]/15 text-[#0079C1] dark:text-cyan-400">
                    <Icon className="size-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="data-mono text-xs font-bold text-amber-500">{item.step}</span>
                      <h3 className="font-semibold text-sm text-foreground">{item.title}</h3>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.detail}</p>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* 7-Stage Causal Lineage Foundation */}
        <Card className="border-border/60">
          <CardHeader>
            <div className="flex items-center gap-2">
              <NetworkIcon className="size-4 text-cyan-400" />
              <CardTitle>7-Stage Causal Audit Lineage</CardTitle>
            </div>
            <CardDescription>
              Every dollar captured in PayPal is cryptographically bound to physical sensor evidence in Neo4j.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 font-mono text-xs">
            {[
              { step: "1", name: "Sensor Anomaly", desc: "4.82 mm/s RMS on Primary Slurry Pump P-101A" },
              { step: "2", name: "GraphRAG Diagnosis", desc: "Inner Race Bearing Wear (ISO 10816 Zone C/D)" },
              { step: "3", name: "Work Order", desc: "WO-2026-IMS-001 with scope SCOPE-BRG-REPLACE-01" },
              { step: "4", name: "Vendor RFQ", desc: "Apex Rotating Equipment bid: $450.00 USD" },
              { step: "5", name: "Spending Mandate", desc: "Cap Check, USD Check, Lane B Dual-Control" },
              { step: "6", name: "PayPal Orders v2 Auth", desc: "29-Day Escrow Hold (intent: AUTHORIZE)" },
              { step: "7", name: "Evidence-Gated Capture", desc: "Post-repair 2.15 mm/s + Supervisor sign-off" },
            ].map((s) => (
              <div key={s.step} className="flex items-center gap-2.5 p-1.5 rounded-lg bg-muted/30 border border-border/40">
                <span className="grid size-5 shrink-0 place-items-center rounded bg-[#003087]/20 text-[#0079C1] dark:text-cyan-400 font-bold text-[10px]">
                  {s.step}
                </span>
                <span className="font-semibold text-foreground text-xs">{s.name}:</span>
                <span className="text-muted-foreground text-[11px] truncate">{s.desc}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      {/* Deep-Dive Workspaces Grid */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {/* Card 1: FLAGSHIP PAYPAL PROCUREMENT */}
        <Card className="border-[#003087]/50 bg-[#003087]/10 hover:border-[#003087] transition-colors flex flex-col justify-between shadow-md">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge className="bg-[#003087] text-white text-[10px] font-mono border-0">
                Flagship Track Demo
              </Badge>
              <CreditCardIcon className="size-5 text-[#0079C1]" />
            </div>
            <CardTitle className="mt-2 text-base font-bold text-foreground">PayPal Procurement Cockpit</CardTitle>
            <CardDescription className="text-xs">
              Execute 1-click autonomous procurement: NASA sensor anomaly, spending mandate check, PayPal authorization, HTTP 403 early capture block, and gated settlement.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button size="sm" className="w-full bg-[#003087] hover:bg-[#00256c] text-white font-bold" nativeButton={false} render={<Link href="/procurement" />}>
              Open Procurement Console <ArrowRightIcon className="size-3.5 ml-1" />
            </Button>
          </CardContent>
        </Card>

        {/* Card 2: NASA IMS TELEMETRY */}
        <Card className="border-cyan-500/30 bg-cyan-500/5 hover:border-cyan-500 transition-colors flex flex-col justify-between">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-[10px] font-mono border-cyan-500/40 text-cyan-400">NASA IMS Rig</Badge>
              <GaugeIcon className="size-5 text-cyan-400" />
            </div>
            <CardTitle className="mt-2 text-base">Predictive Telemetry</CardTitle>
            <CardDescription className="text-xs">
              Simulate sensor drift and evaluate the NASA IMS bearing benchmark against ISO 10816 failure thresholds.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button size="sm" variant="outline" className="w-full border-cyan-500/40 hover:bg-cyan-500/10 text-cyan-400" nativeButton={false} render={<Link href="/predictive-watch" />}>
              Open Telemetry <ArrowRightIcon className="size-3.5 ml-1" />
            </Button>
          </CardContent>
        </Card>

        {/* Card 3: SPENDING MANDATES */}
        <Card className="border-amber-500/30 bg-amber-500/5 hover:border-amber-500 transition-colors flex flex-col justify-between">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-[10px] font-mono border-amber-500/40 text-amber-500">Governance</Badge>
              <WorkflowIcon className="size-5 text-amber-500" />
            </div>
            <CardTitle className="mt-2 text-base">Spending Mandates & Policy</CardTitle>
            <CardDescription className="text-xs">
              Review hardcoded server-side policies: $500 cap, USD currency gate, vendor allowlist, Lane B dual-control routing, and prompt injection isolation.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button size="sm" variant="outline" className="w-full border-amber-500/40 hover:bg-amber-500/10 text-amber-500" nativeButton={false} render={<Link href="/operations" />}>
              Inspect Governance <ArrowRightIcon className="size-3.5 ml-1" />
            </Button>
          </CardContent>
        </Card>

        {/* Card 4: GRAPHRAG CAUSAL LEDGER */}
        <Card className="border-border/60 hover:border-primary/60 transition-colors flex flex-col justify-between">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-[10px] font-mono">Evidence Engine</Badge>
              <SearchIcon className="size-5 text-primary" />
            </div>
            <CardTitle className="mt-2 text-base">GraphRAG Causal Ledger</CardTitle>
            <CardDescription className="text-xs">
              Inspect multi-agent reasoning, compliance verification, and Neo4j citation graph trails justifying every machine expenditure.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <Button size="sm" variant="outline" className="w-full" nativeButton={false} render={<Link href="/investigate" />}>
              Open Investigation <ArrowRightIcon className="size-3.5 ml-1" />
            </Button>
          </CardContent>
        </Card>
      </section>

      {/* Modular Multi-Rail Footnote */}
      <div className="p-3.5 rounded-xl border border-border/40 bg-muted/15 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <ZapIcon className="size-4 text-amber-500 shrink-0" />
          <span>
            <strong>Modular Multi-Rail Architecture:</strong> In addition to PayPal Orders v2, KinetixRAG supports micro-settlement adapters (such as Bitcoin Lightning NWC / BOLT-11) for specialized edge machines.
          </span>
        </div>
        <Button size="sm" variant="ghost" className="text-xs shrink-0 text-amber-500 hover:text-amber-400" nativeButton={false} render={<Link href="/machine-money" />}>
          View Modular Workspace <ArrowRightIcon className="size-3 ml-1" />
        </Button>
      </div>
    </div>
  );
}
