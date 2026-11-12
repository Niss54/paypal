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
    detail: "PayPal Orders v2 authorization hold (intent: AUTHORIZE)",
    icon: CreditCardIcon,
  },
  {
    label: "Evidence-Gated Capture",
    value: "Report + Approval",
    detail: "Server checks submitted evidence and separate approval before requesting capture",
    icon: ShieldCheckIcon,
  },
  {
    label: "Repair Scenario",
    value: "Pump P-101A",
    detail: "Seeded pump incident and clearly labelled demonstration measurements",
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
    title: "REVIEW (Incident)",
    detail: "Review a seeded pump incident with a 4.82 mm/s measurement and a scenario-specific threshold.",
    icon: GaugeIcon,
  },
  {
    step: "02",
    title: "DIAGNOSE (GraphRAG)",
    detail: "Ask the investigation assistant a fresh question and inspect its retrieved sources before reviewing the repair.",
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
    detail: "Authorize after buyer approval; request capture after report validation and separate supervisor approval.",
    icon: CreditCardIcon,
  },
];

const enterprisePillars = [
  {
    title: "Authorize, Then Capture",
    badge: "Two-Phase Payment",
    detail: "PayPal authorization can last up to 29 days. Capture is recommended within the first 3-day honor period; later success depends on risk checks and funding.",
    invariant: "Intent: AUTHORIZE · Buyer Approval Required",
  },
  {
    title: "Submitted Evidence Gate",
    badge: "HTTP 403 Block",
    detail: "The application validates report identifiers, a scenario measurement threshold and file integrity. It does not independently authenticate physical sensors.",
    invariant: "Report Integrity · Scope · Measurement",
  },
  {
    title: "Separate Supervisor Approval",
    badge: "Dual Control",
    detail: "A critical repair needs an authenticated supervisor distinct from the requester. An audit snapshot links the report, approval and payment identifiers.",
    invariant: "Requester Cannot Approve Its Own Order",
  },
];

export default function CommandCenterPage() {
  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-6">
      {/* Flagship Hero Section */}
      <section className="overflow-hidden rounded-2xl bg-card shadow-xs ring-1 ring-foreground/10 border border-[#003087]/30">
        <div className="grid lg:grid-cols-[minmax(0,1.15fr)_minmax(420px,0.85fr)]">
          <div className="flex flex-col justify-center p-6 sm:p-8 lg:p-10">
            <div className="flex items-center gap-3.5 mb-2">
              <img src="/kr.png" alt="KinetixRAG Logo" className="size-12 rounded-xl object-contain drop-shadow bg-background/50 border border-cyan-500/40 p-1 shrink-0" />
              <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-[#003087] hover:bg-[#00256c] text-white border-0 text-xs font-mono flex items-center gap-1.5 py-1 px-2.5">
                <CreditCardIcon className="size-3.5" />
                PayPal AI Hackathon 2026
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-cyan-500/40 text-cyan-400 bg-cyan-950/20">
                Industrial Repair Prototype
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-emerald-500/40 text-emerald-400 bg-emerald-950/20">
                PayPal Orders v2
              </Badge>
              </div>
            </div>

            <h1 className="mt-4 max-w-3xl font-heading text-3xl font-bold tracking-tight sm:text-4xl text-foreground">
              AI-assisted repair procurement with controlled payment release.
              <span className="block mt-1 text-transparent bg-clip-text bg-gradient-to-r from-[#0079C1] via-[#00457C] to-amber-400 dark:from-cyan-400 dark:via-blue-400 dark:to-amber-400">
                &ldquo;No Evidence, No Capture&rdquo;
              </span>
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base sm:leading-7">
              When a critical machine fails, a maintenance team needs to review the repair before releasing payment.
              <strong> KinetixRAG</strong> combines AI investigation with retrieved sources, a seeded repair scenario,
              deterministic spending mandates, and <strong>PayPal Orders v2 Two-Phase Settlement (<code className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded text-foreground">intent: AUTHORIZE</code>)</strong>.
              After buyer approval and authorization, the application blocks capture until submitted repair evidence passes validation and a separate supervisor approves. Sandbox and simulation modes are labelled.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button
                size="lg"
                className="bg-[#003087] hover:bg-[#00256c] text-white font-bold shadow-lg shadow-blue-500/25 border-0 text-sm gap-2"
                nativeButton={false}
                render={<Link href="/procurement" />}
              >
                <CreditCardIcon className="size-4 text-[#0079C1]" />
                Open PayPal Procurement Console
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
                Telemetry Replay
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
          <div className="flex flex-col justify-between gap-5 border-t bg-muted/20 p-6 sm:p-7 lg:border-t-0 lg:border-l border-[#003087]/25 lg:p-8">
            <div className="space-y-2">
              <div className="text-xs font-semibold tracking-wider text-[#0079C1] dark:text-cyan-400 uppercase flex items-center gap-1.5 font-mono">
                <ScaleIcon className="size-3.5 text-cyan-400" />
                The Agentic Commerce Thesis
              </div>
              <h3 className="font-heading text-lg font-bold leading-snug text-foreground">
                Why Repair Procurement Needs a Capture Gate
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed font-sans">
                An AI recommendation is only the start. The application checks purchase policy, submitted completion evidence and approval before requesting PayPal capture.
              </p>
            </div>

            {/* 3 Flagship Pillars with Fixed Badge Height & Clear Hierarchy */}
            <div className="flex flex-col gap-3.5">
              {enterprisePillars.map((p) => (
                <div
                  key={p.title}
                  className="rounded-xl border border-[#003087]/35 bg-[#003087]/10 hover:bg-[#003087]/15 p-4 space-y-2 transition-colors shadow-xs"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-bold font-mono tracking-tight text-blue-400 uppercase">
                      {p.title}
                    </span>
                    <Badge
                      variant="outline"
                      className="text-[10px] h-5 px-2.5 py-0 inline-flex items-center justify-center shrink-0 font-mono font-semibold border-blue-400/50 text-blue-300 bg-blue-950/50 rounded-md"
                    >
                      {p.badge}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground text-xs leading-relaxed font-sans">
                    {p.detail}
                  </p>
                  <div className="pt-1 flex items-center gap-1.5 text-[10px] font-mono text-cyan-400 font-medium">
                    <span className="size-1.5 rounded-full bg-cyan-400 inline-block" />
                    <span>{p.invariant}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Grounding Footer: Invariant Assurance */}
            <div className="pt-3 border-t border-border/40 flex items-center justify-between text-xs font-mono">
              <span className="flex items-center gap-1.5 text-muted-foreground text-[11px]">
                <ShieldCheckIcon className="size-3.5 text-emerald-400" />
                <span>Dual-Phase Settlement Protocol</span>
              </span>
              <span className="text-emerald-400 font-bold text-[11px]">Evidence + Approval</span>
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
              From a reviewed repair scenario to authorization, evidence validation, supervisor approval and capture.
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
              The audit snapshot links scenario inputs, submitted reports, approvals and returned payment identifiers. Hashes do not establish physical truth.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 font-mono text-xs">
            {[
              { step: "1", name: "Sensor Anomaly", desc: "4.82 mm/s RMS on Primary Slurry Pump P-101A" },
              { step: "2", name: "GraphRAG Diagnosis", desc: "Illustrative bearing repair context" },
              { step: "3", name: "Work Order", desc: "WO-2026-IMS-001 with scope SCOPE-BRG-REPLACE-01" },
              { step: "4", name: "Vendor RFQ", desc: "Synthetic supplier quote: $450.00 USD" },
              { step: "5", name: "Spending Mandate", desc: "Cap Check, USD Check, Lane B Dual-Control" },
              { step: "6", name: "PayPal Orders v2 Auth", desc: "29-Day Authorization Hold (intent: AUTHORIZE)" },
              { step: "7", name: "Evidence-Gated Capture", desc: "Submitted report + separate supervisor approval" },
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
                Core Procurement Demo
              </Badge>
              <CreditCardIcon className="size-5 text-[#0079C1]" />
            </div>
            <CardTitle className="mt-2 text-base font-bold text-foreground">PayPal Procurement Cockpit</CardTitle>
            <CardDescription className="text-xs">
              Review the repair scenario, evaluate spending policy, authorize in Sandbox, test the capture rejection and complete evidence review and approval.
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
              <Badge variant="outline" className="text-[10px] font-mono border-cyan-500/40 text-cyan-400">Telemetry Replay</Badge>
              <GaugeIcon className="size-5 text-cyan-400" />
            </div>
            <CardTitle className="mt-2 text-base">Predictive Telemetry</CardTitle>
            <CardDescription className="text-xs">
              Explore telemetry replay and scenario thresholds. This does not certify an operating industrial asset.
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

      {/* PayPal Hackathon Flagship Banner */}
      <div className="p-4 rounded-xl border border-[#003087]/30 bg-[#003087]/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-foreground">
        <div className="flex items-center gap-2.5">
          <CreditCardIcon className="size-5 text-[#0079C1] dark:text-cyan-400 shrink-0" />
          <span>
            <strong className="text-[#003087] dark:text-cyan-300">PayPal AI Hackathon 2026 Core Integration:</strong> KinetixRAG combines AI investigation with PayPal Orders v2 authorization, submitted-report checks, separate supervisor approval and deterministic spending mandates.
          </span>
        </div>
        <Button size="sm" className="text-xs shrink-0 bg-[#003087] hover:bg-[#00246B] text-white font-semibold" nativeButton={false} render={<Link href="/procurement" />}>
          Open PayPal Procurement <ArrowRightIcon className="size-3 ml-1" />
        </Button>
      </div>
    </div>
  );
}
