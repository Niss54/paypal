import Link from "next/link";
import { ArrowRightIcon, Database } from "lucide-react";
import TelemetryPanel from "@/components/TelemetryPanel";
import GraphRiskWidget from "@/components/predictive-watch/GraphRiskWidget";
import LiveVibrationCockpit from "@/components/predictive-watch/LiveVibrationCockpit";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function PredictiveWatchPage() {
  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-4 p-4 sm:p-6">
        <section className="flex flex-col gap-2 border-b border-border/50 pb-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="bg-[#003087] hover:bg-[#00256c] text-white border-0 text-xs font-mono">
              PayPal AI 2026
            </Badge>
            <Badge variant="outline" className="text-xs font-mono border-cyan-500/40 text-cyan-400 bg-cyan-950/20">
              NASA IMS Benchmark
            </Badge>
            <Badge variant="outline" className="text-xs font-mono border-amber-500/40 text-amber-500 bg-amber-500/10">
              ISO 10816 Zone C/D
            </Badge>
          </div>
          <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-1">
            Predictive Telemetry Triggers
          </h1>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
            Stream empirical sensor telemetry (including NASA IMS bearing test rig) and evaluate ISO 10816 Zone C failure thresholds that trigger autonomous PayPal Two-Phase settlements.
          </p>
        </section>

        {/* Architectural Callout: Why GraphRAG over PLC */}
        <div className="p-4 rounded-xl bg-card border border-[#003087]/35 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-[#003087]/20 text-cyan-400 shrink-0 mt-0.5 border border-cyan-500/30">
              <Database className="size-4" />
            </div>
            <div>
              <span className="font-bold text-foreground text-xs flex items-center gap-2">
                <span>Why GraphRAG over a simple SCADA threshold?</span>
                <Badge variant="outline" className="text-[10px] font-mono border-cyan-500/40 text-cyan-400 bg-cyan-950/20">
                  Symptom vs. Expenditure
                </Badge>
              </span>
              <p className="text-muted-foreground text-[11px] mt-1 leading-relaxed">
                Graph retrieval supplies maintenance context for an investigation. The procurement demonstration uses seeded inputs and server-side spending rules; diagnostic text cannot authorize or capture PayPal funds.
              </p>
            </div>
          </div>
          <Link
            href="/procurement"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 bg-[#003087]/20 hover:bg-[#003087]/30 px-3.5 py-2 rounded-lg border border-[#003087]/40 shrink-0 transition-colors shadow-xs"
          >
            <span>View PayPal Procurement Settlement</span>
            <ArrowRightIcon className="size-3.5" />
          </Link>
        </div>

        {/* GraphSAGE Risk Intelligence Advisory Component */}
        <GraphRiskWidget equipmentId="P-101A" deterministicRisk={0.42} currentVibration={5.42} />

        {/* Live Multi-Source Vibration Cockpit (Phone MEMS + NASA IMS Replay + Industrial Synth) */}
        <LiveVibrationCockpit />

        <Card className="min-h-[720px] gap-0 py-0">
          <CardHeader className="border-b py-4">
            <CardTitle>Failure signature simulation</CardTitle>
            <CardDescription>
              Live and simulated signals create durable warnings and human-reviewed work orders.
            </CardDescription>
            <CardAction>
              <Badge variant="warning">Simulation</Badge>
            </CardAction>
          </CardHeader>
          <CardContent className="min-h-0 flex-1 p-0">
            <TelemetryPanel />
          </CardContent>
        </Card>
    </div>
  );
}
