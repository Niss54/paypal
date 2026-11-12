"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Flame,
  Info,
  Layers,
  RotateCcw,
  ShieldAlert,
  Smartphone,
  Sparkles,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function MobileSensorPage() {
  const [active, setActive] = useState<boolean>(false);
  const [permissionGranted, setPermissionGranted] = useState<boolean | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [ax, setAx] = useState<number>(0);
  const [ay, setAy] = useState<number>(0);
  const [az, setAz] = useState<number>(0);
  const [mag, setMag] = useState<number>(0);
  const [equivMms, setEquivMms] = useState<number>(1.25);
  const [maxPeak, setMaxPeak] = useState<number>(1.25);
  const [peakBreached, setPeakBreached] = useState<boolean>(false);
  const [syncStatus, setSyncStatus] = useState<"connected" | "syncing" | "idle">("idle");

  const baselineRef = useRef<{ x: number; y: number; z: number }>({ x: 0, y: 0, z: 9.81 });
  const lastPostRef = useRef<number>(0);
  const maxPeakRef = useRef<number>(1.25);

  const sendTelemetry = useCallback(async (payload: { ax: number; ay: number; az: number; rms: number; peak: number; breached: boolean }) => {
    try {
      setSyncStatus("syncing");
      await fetch("/api/sensor-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setSyncStatus("connected");
    } catch (_) {
      setSyncStatus("idle");
    }
  }, []);

  const handleMotion = useCallback((event: DeviceMotionEvent) => {
    let curX = 0;
    let curY = 0;
    let curZ = 0;

    if (event.acceleration && event.acceleration.x !== null) {
      curX = event.acceleration.x || 0;
      curY = event.acceleration.y || 0;
      curZ = event.acceleration.z || 0;
    } else if (event.accelerationIncludingGravity && event.accelerationIncludingGravity.x !== null) {
      const gx = event.accelerationIncludingGravity.x || 0;
      const gy = event.accelerationIncludingGravity.y || 0;
      const gz = event.accelerationIncludingGravity.z || 0;

      baselineRef.current.x = 0.95 * baselineRef.current.x + 0.05 * gx;
      baselineRef.current.y = 0.95 * baselineRef.current.y + 0.05 * gy;
      baselineRef.current.z = 0.95 * baselineRef.current.z + 0.05 * gz;

      curX = gx - baselineRef.current.x;
      curY = gy - baselineRef.current.y;
      curZ = gz - baselineRef.current.z;
    }

    const currentMag = Math.sqrt(curX * curX + curY * curY + curZ * curZ);
    const equiv = Math.min(25.0, Number((1.25 + currentMag * 0.95).toFixed(2)));

    setAx(Number(curX.toFixed(2)));
    setAy(Number(curY.toFixed(2)));
    setAz(Number(curZ.toFixed(2)));
    setMag(Number(currentMag.toFixed(2)));
    setEquivMms(equiv);

    if (equiv > maxPeakRef.current) {
      maxPeakRef.current = equiv;
      setMaxPeak(equiv);
    }

    const isBreach = equiv >= 4.50;
    if (isBreach) {
      setPeakBreached(true);
      if (typeof navigator !== "undefined" && navigator.vibrate) {
        try {
          navigator.vibrate([80, 40, 80]);
        } catch (_) {}
      }
    }

    // Stream telemetry to Neon cloud ledger every ~180ms or instantly on breach
    const now = Date.now();
    if (isBreach || now - lastPostRef.current > 180) {
      lastPostRef.current = now;
      sendTelemetry({
        ax: Number(curX.toFixed(2)),
        ay: Number(curY.toFixed(2)),
        az: Number(curZ.toFixed(2)),
        rms: equiv,
        peak: maxPeakRef.current,
        breached: isBreach,
      });
    }
  }, [sendTelemetry]);

  const activateSensor = async () => {
    setErrorMsg(null);
    if (typeof window === "undefined") return;

    if (
      typeof (DeviceMotionEvent as any) !== "undefined" &&
      typeof (DeviceMotionEvent as any).requestPermission === "function"
    ) {
      try {
        const res = await (DeviceMotionEvent as any).requestPermission();
        if (res === "granted") {
          setPermissionGranted(true);
          setActive(true);
          window.addEventListener("devicemotion", handleMotion, { passive: true });
        } else {
          setPermissionGranted(false);
          setErrorMsg("Permission denied by iOS.");
        }
      } catch (err: any) {
        setPermissionGranted(false);
        setErrorMsg(err?.message || "Could not request permission.");
      }
    } else if ("ondevicemotion" in window) {
      setPermissionGranted(true);
      setActive(true);
      window.addEventListener("devicemotion", handleMotion, { passive: true });
    } else {
      setPermissionGranted(false);
      setErrorMsg("DeviceMotionEvent is not supported on this browser.");
    }
  };

  useEffect(() => {
    // Try auto-activating on non-iOS
    if (
      typeof window !== "undefined" &&
      !(
        typeof (DeviceMotionEvent as any) !== "undefined" &&
        typeof (DeviceMotionEvent as any).requestPermission === "function"
      )
    ) {
      activateSensor();
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("devicemotion", handleMotion);
      }
    };
  }, [handleMotion]);

  const simulateShake = (force: number = 6.0) => {
    const rx = Number((Math.random() * force - force / 2).toFixed(2));
    const ry = Number((Math.random() * force - force / 2).toFixed(2));
    const rz = Number((force * 0.8 + Math.random()).toFixed(2));
    const m = Math.sqrt(rx * rx + ry * ry + rz * rz);
    const eq = Math.min(25.0, Number((1.25 + m * 0.95).toFixed(2)));

    setAx(rx);
    setAy(ry);
    setAz(rz);
    setMag(Number(m.toFixed(2)));
    setEquivMms(eq);

    if (eq > maxPeakRef.current) {
      maxPeakRef.current = eq;
      setMaxPeak(eq);
    }

    const isBreach = eq >= 4.5;
    if (isBreach) {
      setPeakBreached(true);
      if (typeof navigator !== "undefined" && navigator.vibrate) {
        try {
          navigator.vibrate([100, 50, 100]);
        } catch (_) {}
      }
    }

    sendTelemetry({
      ax: rx,
      ay: ry,
      az: rz,
      rms: eq,
      peak: maxPeakRef.current,
      breached: isBreach,
    });
  };

  const isAlarm = equivMms >= 4.5 || maxPeak >= 4.5;

  return (
    <div className={`min-h-screen p-4 sm:p-6 flex flex-col justify-between transition-colors duration-300 ${isAlarm ? "bg-red-950/40 text-red-100" : "bg-background text-foreground"}`}>
      {/* Top Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Badge className="bg-[#003087] text-white border-0 text-[10px] font-mono">
            PAYPAL AI 2026 SENSOR
          </Badge>
          <Badge variant="outline" className="border-emerald-500/50 bg-emerald-500/10 text-emerald-300 text-[10px] font-mono flex items-center gap-1.5 animate-pulse">
            <span className="size-1.5 rounded-full bg-emerald-400"></span>
            {syncStatus === "syncing" || syncStatus === "connected" ? "LIVE STREAM ACTIVE ➔ LAPTOP" : active ? "MEMS ACTIVE" : "TAP TO ACTIVATE"}
          </Badge>
        </div>
        <div className="flex items-center justify-between">
          <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight flex items-center gap-2">
            <Smartphone className="size-5 text-cyan-400" />
            <span>Industrial Sensor Transmitter</span>
          </h1>
          <Badge variant="outline" className="text-[10px] font-mono border-cyan-500/30 text-cyan-400 bg-cyan-950/20">
            P-101A CM PUMP
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          Hold this phone and shake it. Vibration telemetry streams live into the laptop oscilloscope via Neon Cloud and trips the ISO 10816 Zone C failure threshold.
        </p>
      </div>

      {/* Main Center Gauge */}
      <div className="my-auto py-6 flex flex-col items-center justify-center space-y-6">
        {/* Large Radial Ring Display */}
        <div className="relative size-56 sm:size-64 rounded-full border-4 flex flex-col items-center justify-center p-6 text-center transition-all duration-200"
          style={{
            borderColor: isAlarm ? "#ef4444" : equivMms > 2.5 ? "#06b6d4" : "#10b981",
            boxShadow: isAlarm ? "0 0 40px rgba(239, 68, 68, 0.4)" : "0 0 25px rgba(16, 185, 129, 0.15)",
          }}
        >
          <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
            Vibration Velocity RMS
          </span>
          <div className="text-5xl sm:text-6xl font-black font-mono tracking-tight my-1">
            <span className={isAlarm ? "text-red-400 animate-pulse" : "text-emerald-400"}>
              {equivMms.toFixed(2)}
            </span>
          </div>
          <span className="text-xs font-mono text-muted-foreground">mm/s RMS</span>

          <div className="mt-2 flex flex-col items-center gap-1">
            <Badge variant="outline" className={`text-[10px] font-mono ${isAlarm ? "bg-red-500/20 text-red-300 border-red-500/40" : "bg-muted text-muted-foreground"}`}>
              {isAlarm ? "🚨 ZONE C / D EXCURSION" : "ZONE A: NOMINAL"}
            </Badge>
            <span className="text-[10px] font-mono text-cyan-400 font-semibold">
              Peak: {maxPeak.toFixed(2)} mm/s
            </span>
          </div>
        </div>

        {/* 3-Axis MEMS Raw Numbers */}
        <div className="grid grid-cols-3 gap-3 w-full max-w-xs text-center">
          <div className="p-2.5 rounded-lg bg-card/60 border border-cyan-500/30">
            <span className="text-[10px] font-bold text-cyan-400 block">AXIS X</span>
            <span className="text-base font-extrabold font-mono">{ax >= 0 ? `+${ax}` : ax}</span>
            <span className="text-[9px] text-muted-foreground font-mono block">m/s²</span>
          </div>
          <div className="p-2.5 rounded-lg bg-card/60 border border-pink-500/30">
            <span className="text-[10px] font-bold text-pink-400 block">AXIS Y</span>
            <span className="text-base font-extrabold font-mono">{ay >= 0 ? `+${ay}` : ay}</span>
            <span className="text-[9px] text-muted-foreground font-mono block">m/s²</span>
          </div>
          <div className="p-2.5 rounded-lg bg-card/60 border border-blue-500/30">
            <span className="text-[10px] font-bold text-blue-400 block">AXIS Z</span>
            <span className="text-base font-extrabold font-mono">{az >= 0 ? `+${az}` : az}</span>
            <span className="text-[9px] text-muted-foreground font-mono block">m/s²</span>
          </div>
        </div>

        {/* Activation Button for iOS Safari */}
        {!active && (
          <Button
            size="lg"
            onClick={activateSensor}
            className="w-full max-w-xs bg-emerald-600 hover:bg-emerald-500 text-white font-bold h-12 shadow-lg"
          >
            <Zap className="size-4 mr-2" />
            Enable Motion Sensor
          </Button>
        )}

        {/* Test Shake Button */}
        <div className="flex gap-2 w-full max-w-xs">
          <Button
            size="sm"
            onClick={() => simulateShake(6.5)}
            className="flex-1 h-9 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold"
          >
            <Zap className="size-3.5 mr-1" />
            Test Shake Breach
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => simulateShake(0.5)}
            className="h-9 px-3 text-xs border-border/60 text-muted-foreground"
          >
            <RotateCcw className="size-3.5 mr-1" />
            Reset
          </Button>
        </div>
      </div>

      {/* Bottom Alert / Navigation Card */}
      <div className="space-y-3">
        {isAlarm && (
          <div className="p-3.5 rounded-xl border border-red-500/50 bg-red-950/40 text-xs space-y-2 animate-in fade-in">
            <div className="flex items-center gap-2 text-red-300 font-bold">
              <ShieldAlert className="size-4 text-red-400" />
              <span>ISO 10816 Zone C Violation (4.50 mm/s Limit Exceeded)</span>
            </div>
            <p className="text-[11px] text-red-200/80 leading-relaxed">
              Physical shake telemetry successfully triggered Kinetix autonomous procurement incident (WO-2026-IMS-001).
            </p>
            <Link
              href="/procurement"
              className="flex items-center justify-center gap-1.5 w-full py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-bold text-xs"
            >
              <span>View PayPal Procurement Draft ($450.00)</span>
              <ArrowRight className="size-3.5" />
            </Link>
          </div>
        )}

        <div className="flex items-center justify-between text-xs pt-2 border-t border-border/30">
          <Link href="/predictive-watch" className="text-cyan-400 hover:text-cyan-300 font-medium">
            ← Predictive Watch Cockpit
          </Link>
          <Link href="/procurement" className="text-cyan-400 hover:text-cyan-300 font-medium">
            PayPal Procurement →
          </Link>
        </div>
      </div>
    </div>
  );
}
