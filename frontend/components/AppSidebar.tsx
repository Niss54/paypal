"use client";

import {
  ChartNoAxesCombinedIcon,
  ClipboardListIcon,
  CreditCardIcon,
  GitCompareArrowsIcon,
  GaugeIcon,
  LayoutDashboardIcon,
  SearchIcon,
  SlidersIcon,
  UserRoundSearchIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator,
  useSidebar,
} from "@/components/ui/sidebar";
import type { ReadinessResponse } from "@/lib/api";

const paypalHackathonItems = [
  {
    label: "PayPal Procurement",
    icon: CreditCardIcon,
    href: "/procurement",
    badge: "v2",
    badgeClass: "bg-[#003087] text-white border-blue-400/40 font-bold",
    highlight: true,
  },
  {
    label: "Command Center",
    icon: LayoutDashboardIcon,
    href: "/",
  },
  {
    label: "Predictive Watch (NASA)",
    icon: GaugeIcon,
    href: "/predictive-watch",
  },
  {
    label: "Spending Mandates",
    icon: SlidersIcon,
    href: "/operations",
  },
];

const evidenceRagItems = [
  { label: "Investigate GraphRAG", icon: SearchIcon, href: "/investigate" },
  { label: "Funded Work Orders", icon: ClipboardListIcon, href: "/work-orders" },
  { label: "Knowledge Risk", icon: UserRoundSearchIcon, href: "/knowledge-risk" },
  { label: "RAG Comparison", icon: GitCompareArrowsIcon, href: "/comparison" },
  { label: "Evaluation", icon: ChartNoAxesCombinedIcon, href: "/evaluation" },
];

export default function AppSidebar({ readiness }: { readiness: ReadinessResponse | null }) {
  const { isMobile, setOpenMobile } = useSidebar();
  const pathname = usePathname();

  function closeMobileSidebar() {
    if (isMobile) setOpenMobile(false);
  }

  return (
    <Sidebar collapsible="icon" variant="sidebar">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              tooltip="KinetixRAG Industrial Platform"
              render={<Link href="/" onClick={closeMobileSidebar} />}
            >
              <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-background/60 border border-cyan-500/40 p-0.5 shadow-sm overflow-hidden">
                <img src="/kr.png" alt="KinetixRAG Logo" className="size-full object-contain" />
              </div>
              <div className="flex min-w-0 flex-col items-start group-data-[collapsible=icon]:hidden">
                <span className="font-heading text-base font-semibold tracking-tight">KinetixRAG</span>
                <span className="truncate text-xs text-[#0079C1] dark:text-cyan-400 font-mono">PayPal AI 2026</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        {/* PayPal AI Hackathon Flagship Group */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[11px] font-semibold text-[#0079C1] dark:text-cyan-400 uppercase tracking-wider font-mono">
            PayPal AI Hackathon 2026
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {paypalHackathonItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(`${item.href}/`));
                return (
                  <SidebarMenuItem key={item.label}>
                    <SidebarMenuButton
                      isActive={isActive}
                      tooltip={item.label}
                      className={item.highlight ? "font-semibold text-foreground bg-[#003087]/15 border border-[#003087]/30 whitespace-nowrap flex-nowrap" : "whitespace-nowrap flex-nowrap"}
                      render={<Link href={item.href} onClick={closeMobileSidebar} />}
                    >
                      <Icon className={item.highlight ? "text-[#0079C1] dark:text-cyan-400 shrink-0" : "shrink-0"} />
                      <span className="flex-1 whitespace-nowrap truncate">{item.label}</span>
                      {item.badge && (
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border shrink-0 group-data-[collapsible=icon]:hidden ${item.badgeClass}`}>
                          {item.badge}
                        </span>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Evidence & Justification (GraphRAG) Group */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Evidence & Governance (RAG)
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {evidenceRagItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(`${item.href}/`));
                return (
                  <SidebarMenuItem key={item.label}>
                    <SidebarMenuButton
                      isActive={isActive}
                      tooltip={item.label}
                      render={<Link href={item.href} onClick={closeMobileSidebar} />}
                    >
                      <Icon className="shrink-0" />
                      <span className="whitespace-nowrap truncate">{item.label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarSeparator />
        <div className="flex items-center gap-2 px-2 py-1.5 group-data-[collapsible=icon]:justify-center">
          <span
            className={
              readiness?.ready
                ? "size-2 shrink-0 rounded-full bg-success shadow-[0_0_0_3px_color-mix(in_oklch,var(--success)_14%,transparent)]"
                : readiness === null
                  ? "size-2 shrink-0 rounded-full bg-warning"
                  : "size-2 shrink-0 rounded-full bg-destructive"
            }
          />
          <div className="min-w-0 group-data-[collapsible=icon]:hidden">
            <div className="text-xs font-medium truncate">
              {readiness === null
                ? "Checking systems"
                : readiness.ready
                  ? "Systems operational"
                  : "Systems degraded"}
            </div>
            <div className="text-xs text-muted-foreground truncate">
              {readiness?.ready ? "Dependencies ready" : "Open health status for details"}
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between px-2.5 pt-2 pb-1 text-[10px] text-muted-foreground/80 group-data-[collapsible=icon]:hidden font-mono border-t border-border/40 overflow-hidden">
          <div className="flex items-center gap-1.5 min-w-0 truncate">
            <img src="/kr.png" alt="KR" className="size-3.5 shrink-0 object-contain" />
            <span className="truncate">KinetixRAG</span>
          </div>
          <span className="text-[#0079C1] dark:text-cyan-400 font-bold shrink-0">PayPal AI 2026</span>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
