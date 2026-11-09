"use client";

import { useEffect, useState } from "react";
import { AlertTriangleIcon, RefreshCwIcon } from "lucide-react";

import KnowledgeRiskView from "@/components/knowledge-risk/KnowledgeRiskView";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { getKnowledgeRisk, type KnowledgeRiskResponse } from "@/lib/api";

const horizons = [2, 5, 10, 15];

export default function KnowledgeRiskPage() {
  const [horizon, setHorizon] = useState(5);
  const [data, setData] = useState<KnowledgeRiskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;

    getKnowledgeRisk(horizon)
      .then((result) => {
        if (active) setData(result);
      })
      .catch((reason) => {
        if (active) setError(reason instanceof Error ? reason.message : "Knowledge risk is unavailable.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [horizon, reloadKey]);

  function changeHorizon(value: string | null) {
    if (value === null) return;
    setLoading(true);
    setError(null);
    setHorizon(Number(value));
  }

  function retry() {
    setLoading(true);
    setError(null);
    setReloadKey((value) => value + 1);
  }

  return (
    <div className="dashboard-enter mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-6">
        <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between border-b border-border/50 pb-5">
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-[#003087] hover:bg-[#00256c] text-white border-0 text-xs font-mono">
                PayPal AI 2026
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-amber-500/40 text-amber-500 bg-amber-500/10">
                Workforce Continuity
              </Badge>
              <Badge variant="outline" className="text-xs font-mono border-cyan-500/40 text-cyan-400 bg-cyan-950/20">
                Institutional Memory Graph
              </Badge>
            </div>
            <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-foreground mt-1">
              Knowledge-Retirement Risk
            </h1>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground">
              Identify operational knowledge concentrated in people nearing retirement, the assets that depend on
              them, and where successor coverage is still missing.
            </p>
          </div>

          <Select
            value={String(horizon)}
            onValueChange={changeHorizon}
          >
            <SelectTrigger aria-label="Retirement horizon">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {horizons.map((years) => (
                  <SelectItem key={years} value={String(years)}>
                    Next {years} years
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </section>

        {error ? (
          <Alert variant="destructive">
            <AlertTriangleIcon />
            <AlertTitle>Knowledge-risk data is unavailable</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
            <Button
              variant="outline"
              size="sm"
              onClick={retry}
            >
              <RefreshCwIcon data-icon="inline-start" />
              Retry
            </Button>
          </Alert>
        ) : loading ? (
          <div className="grid gap-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {Array.from({ length: 4 }, (_, index) => (
                <Skeleton key={index} className="h-28 rounded-xl" />
              ))}
            </div>
            <Skeleton className="h-96 rounded-xl" />
          </div>
        ) : data ? (
          <KnowledgeRiskView data={data} />
        ) : null}
    </div>
  );
}
