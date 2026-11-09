"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import AppSidebar from "@/components/AppSidebar";
import DashboardHeader from "@/components/DashboardHeader";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { getReadiness, type ReadinessResponse } from "@/lib/api";

const routeTitles: Array<[prefix: string, title: string]> = [
  ["/work-orders/", "Work Order"],
  ["/work-orders", "Work Orders"],
  ["/predictive-watch", "Predictive Watch"],
  ["/operations", "Operations & Governance"],
  ["/procurement", "Evidence-Gated Industrial Procurement (PayPal)"],
  ["/machine-money", "Machine Money"],
  ["/knowledge-risk", "Knowledge Risk"],
  ["/comparison", "RAG Comparison"],
  ["/evaluation", "Evaluation"],
  ["/investigate", "Investigate"],
  ["/", "Command Center"],
];

export function getWorkspaceTitle(pathname: string) {
  return routeTitles.find(([prefix]) =>
    prefix === "/" ? pathname === "/" : pathname.startsWith(prefix),
  )?.[1] ?? "Workspace";
}

export default function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);

  useEffect(() => {
    let active = true;
    let timerId: any = null;

    async function check() {
      try {
        const next = await getReadiness();
        if (active) {
          setReadiness(next);
          // Relax polling interval when connected and healthy (25 seconds)
          timerId = setTimeout(check, 25_000);
        }
      } catch {
        if (active) {
          setReadiness({
            status: "degraded",
            ready: false,
            dependencies: {
              backend: { status: "down", detail: "Connecting to Render Cloud backend (~30s spin-up)..." },
            },
          });
          // Rapid retry when disconnected or waking up from Render free-tier sleep (every 4 seconds)
          timerId = setTimeout(check, 4_000);
        }
      }
    }

    void check();
    return () => {
      active = false;
      if (timerId) clearTimeout(timerId);
    };
  }, []);

  return (
    <SidebarProvider defaultOpen>
      <AppSidebar readiness={readiness} />
      <SidebarInset className="h-svh min-w-0 overflow-hidden">
        {readiness?.dependencies?.backend?.status === "down" && (
          <div className="bg-amber-500/15 border-b border-amber-500/30 px-3 py-1 text-center text-xs text-amber-300 font-mono flex items-center justify-center gap-2 shrink-0">
            <span className="size-1.5 rounded-full bg-amber-400 animate-ping" />
            <span>Connecting to Render Cloud Backend (https://paypal-y2jk.onrender.com). If inactive, cold spin-up takes ~30s. Auto-reconnecting...</span>
          </div>
        )}
        <DashboardHeader title={getWorkspaceTitle(pathname)} readiness={readiness} />
        <ScrollArea className="min-h-0 flex-1">
          <div className="kinetix-grid min-h-full">{children}</div>
        </ScrollArea>
      </SidebarInset>
    </SidebarProvider>
  );
}
