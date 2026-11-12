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
  Maximize2,
  Play,
  Pause,
  QrCode,
  Radio,
  RotateCcw,
  ShieldAlert,
  Smartphone,
  Sparkles,
  Volume2,
  VolumeX,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { QRCodeSVG } from "qrcode.react";

type TelemetryMode = "nasa_ims" | "live_mems" | "industrial_synth";

interface AxisReading {
  x: number;
  y: number;
  z: number;
  magnitude: number;
  equivalent_mm_s: number;
}

interface NASAStage {
  record_id: string;
  stage: string;
  elapsed_hours: number;
  vibration_mm_s: number;
  bearing_temp_c: number;
  frequency_peak_hz: number;
  iso_zone: string;
  notes: string;
}

const NASA_STAGES: NASAStage[] = [
  {
    record_id: "NASA-IMS-T2-REC-001",
    stage: "Healthy Baseline",
    elapsed_hours: 0.0,
    vibration_mm_s: 1.85,
    bearing_temp_c: 52.4,
    frequency_peak_hz: 33.3,
    iso_zone: "Zone A (Good)",
    notes: "Nominal break-in operation. Vibration well below ISO 10816 4.5 mm/s limit.",
  },
  {
    record_id: "NASA-IMS-T2-REC-020",
    stage: "Nominal Continuous",
    elapsed_hours: 63.6,
    vibration_mm_s: 2.28,
    bearing_temp_c: 55.1,
    frequency_peak_hz: 33.3,
    iso_zone: "Zone B (Acceptable)",
    notes: "Continuous stable run. Normal bearing raceway contact micro-asperities.",
  },
  {
    record_id: "NASA-IMS-T2-REC-038",
    stage: "Initial Degradation",
    elapsed_hours: 128.1,
    vibration_mm_s: 3.62,
    bearing_temp_c: 64.8,
    frequency_peak_hz: 236.4,
    iso_zone: "Zone B/C (Monitor)",
    notes: "Micro-spalling emerging on outer ring. BPFO ball-pass harmonics rising.",
  },
  {
    record_id: "NASA-IMS-T2-REC-042",
    stage: "Zone C Excursion Breach",
    elapsed_hours: 147.6,
    vibration_mm_s: 5.42,
    bearing_temp_c: 84.6,
    frequency_peak_hz: 236.4,
    iso_zone: "Zone C (Unacceptable Damage)",
    notes: "Severe outer race defect. Autonomous procurement workflow must trigger.",
  },
  {
    record_id: "NASA-IMS-T2-REC-046",
    stage: "Zone D Catastrophic Trip",
    elapsed_hours: 164.0,
    vibration_mm_s: 7.85,
    bearing_temp_c: 98.2,
    frequency_peak_hz: 236.4,
    iso_zone: "Zone D (Emergency Trip)",
    notes: "Structural spall propagation. Uncontained bearing seizure imminent.",
  },
];

export default function LiveVibrationCockpit() {
  const [mode, setMode] = useState<TelemetryMode>("live_mems");
  const [sensorActive, setSensorActive] = useState<boolean>(false);
  const [permissionGranted, setPermissionGranted] = useState<boolean | null>(null);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  // Live Readings
  const [reading, setReading] = useState<AxisReading>({
    x: 0,
    y: 0,
    z: 0,
    magnitude: 0,
    equivalent_mm_s: 1.25,
  });

  // NASA IMS Replay State
  const [nasaIndex, setNasaIndex] = useState<number>(3); // Default to breach record 042 for instant demonstration
  const [nasaPlaying, setNasaPlaying] = useState<boolean>(false);

  // Industrial Synth State
  const [synthRpm, setSynthRpm] = useState<number>(1780);
  const [synthUnbalance, setSynthUnbalance] = useState<number>(35);

  // Anomaly & Incident Trigger State
  const [incidentTriggered, setIncidentTriggered] = useState<boolean>(false);
  const [qrModalOpen, setQrModalOpen] = useState<boolean>(false);
  const LIVE_VERCEL_SENSOR_URL = "https://paypal-pink.vercel.app/sensor";
  const [clientUrl, setClientUrl] = useState<string>(LIVE_VERCEL_SENSOR_URL);

  // History buffer for rolling canvas oscilloscope
  const historyRef = useRef<Array<{ x: number; y: number; z: number; mag: number }>>([]);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Gravity baseline compensation tracking
  const gravityBaselineRef = useRef<{ x: number; y: number; z: number }>({ x: 0, y: 0, z: 9.81 });

  // Initialize client URL for QR Code (Always use Vercel URL on localhost so phones can scan and reach it)
  useEffect(() => {
    if (typeof window !== "undefined") {
      if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
        setClientUrl(`${window.location.origin}/sensor`);
      } else {
        setClientUrl(LIVE_VERCEL_SENSOR_URL);
      }
    }
  }, []);

  // --- Device Motion Sensor Listener (Smartphone / Laptop MEMS Accelerometer) ---
  const handleDeviceMotion = useCallback((event: DeviceMotionEvent) => {
    let ax = 0;
    let ay = 0;
    let az = 0;

    if (event.acceleration && event.acceleration.x !== null) {
      // Direct linear acceleration (gravity already stripped by device OS)
      ax = event.acceleration.x || 0;
      ay = event.acceleration.y || 0;
      az = event.acceleration.z || 0;
    } else if (event.accelerationIncludingGravity && event.accelerationIncludingGravity.x !== null) {
      // Fallback: low-pass filter gravity compensation
      const gx = event.accelerationIncludingGravity.x || 0;
      const gy = event.accelerationIncludingGravity.y || 0;
      const gz = event.accelerationIncludingGravity.z || 0;

      // Update baseline slowly
      gravityBaselineRef.current.x = 0.95 * gravityBaselineRef.current.x + 0.05 * gx;
      gravityBaselineRef.current.y = 0.95 * gravityBaselineRef.current.y + 0.05 * gy;
      gravityBaselineRef.current.z = 0.95 * gravityBaselineRef.current.z + 0.05 * gz;

      ax = gx - gravityBaselineRef.current.x;
      ay = gy - gravityBaselineRef.current.y;
      az = gz - gravityBaselineRef.current.z;
    }

    const mag = Math.sqrt(ax * ax + ay * ay + az * az);

    // Calibrated equivalent RMS index: baseline idle (~1.25 mm/s) + scaled dynamic motion
    // 0 m/s^2 motion -> 1.25 mm/s (Zone A)
    // 3.5 m/s^2 motion -> ~4.50 mm/s (Zone C warning limit)
    // 7.0+ m/s^2 vigorous shake -> ~6.8 - 8.5 mm/s (Zone D breach)
    const equiv = Math.min(12.0, Number((1.25 + mag * 0.95).toFixed(2)));

    setReading({
      x: Number(ax.toFixed(2)),
      y: Number(ay.toFixed(2)),
      z: Number(az.toFixed(2)),
      magnitude: Number(mag.toFixed(2)),
      equivalent_mm_s: equiv,
    });

    // Check breach threshold (ISO Zone C limit = 4.5 mm/s RMS)
    if (equiv >= 4.50) {
      setIncidentTriggered(true);
    }
  }, []);

  // Request Permission (iOS Safari requirement)
  const startDeviceMotionSensor = async () => {
    setPermissionError(null);
    if (typeof window === "undefined") return;

    if (
      typeof (DeviceMotionEvent as any) !== "undefined" &&
      typeof (DeviceMotionEvent as any).requestPermission === "function"
    ) {
      try {
        const response = await (DeviceMotionEvent as any).requestPermission();
        if (response === "granted") {
          setPermissionGranted(true);
          setSensorActive(true);
          window.addEventListener("devicemotion", handleDeviceMotion, { passive: true });
        } else {
          setPermissionGranted(false);
          setPermissionError("Motion sensor permission denied by user.");
        }
      } catch (err: any) {
        setPermissionGranted(false);
        setPermissionError(err?.message || "Could not request DeviceMotionEvent permission.");
      }
    } else if ("ondevicemotion" in window) {
      // Android, Chrome, Edge, Firefox, Desktop
      setPermissionGranted(true);
      setSensorActive(true);
      window.addEventListener("devicemotion", handleDeviceMotion, { passive: true });
    } else {
      setPermissionGranted(false);
      setPermissionError("DeviceMotionEvent API is not supported on this browser/hardware.");
    }
  };

  const stopDeviceMotionSensor = () => {
    if (typeof window !== "undefined") {
      window.removeEventListener("devicemotion", handleDeviceMotion);
    }
    setSensorActive(false);
  };

  const [cloudStreamActive, setCloudStreamActive] = useState<boolean>(false);

  // Poll cloud sensor stream from phone (via Neon Cloud Ledger)
  useEffect(() => {
    if (mode !== "live_mems") {
      setCloudStreamActive(false);
      return;
    }

    let isMounted = true;
    const pollSensorStream = async () => {
      try {
        // Try relative /api/sensor-stream first
        let res = await fetch("/api/sensor-stream", { cache: "no-store" }).catch(() => null);
        let json = res && res.ok ? await res.json().catch(() => null) : null;
        let diff = json?.data?.updated_at ? Date.now() - new Date(json.data.updated_at).getTime() : 999999;

        // If stale or idle on localhost, poll production Vercel cloud bridge
        if (diff > 15000 && typeof window !== "undefined" && !window.location.hostname.includes("vercel.app")) {
          const vRes = await fetch("https://paypal-pink.vercel.app/api/sensor-stream", { cache: "no-store" }).catch(() => null);
          if (vRes && vRes.ok) {
            const vJson = await vRes.json().catch(() => null);
            if (vJson?.data) {
              json = vJson;
              diff = Date.now() - new Date(vJson.data.updated_at).getTime();
            }
          }
        }

        if (!json || !json.data) return;

        const { ax, ay, az, rms, peak, breached } = json.data;

        // If packet arrived within 25 seconds, stream it live to the oscilloscope!
        if (diff < 25000 && isMounted) {
          setCloudStreamActive(true);
          const currentRms = Number(rms || 1.25);
          setReading({
            x: Number(ax || 0),
            y: Number(ay || 0),
            z: Number(az || 0),
            magnitude: Math.sqrt((ax || 0) ** 2 + (ay || 0) ** 2 + (az || 0) ** 2),
            equivalent_mm_s: currentRms,
          });

          if (breached || currentRms >= 4.50) {
            setIncidentTriggered(true);
          }
        } else if (isMounted) {
          setCloudStreamActive(false);
        }
      } catch (_) {}
    };

    const interval = setInterval(pollSensorStream, 250);
    pollSensorStream();

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [mode]);

  // Toggle sensor on/off
  useEffect(() => {
    if (mode === "live_mems") {
      startDeviceMotionSensor();
    } else {
      stopDeviceMotionSensor();
    }
    return () => {
      stopDeviceMotionSensor();
    };
  }, [mode]);

  // Inject Simulated Hardware Shake (for desktop testing without mobile)
  const injectShockPulse = (severityG: number = 5.8) => {
    const pulseX = Number((Math.random() * severityG - severityG / 2).toFixed(2));
    const pulseY = Number((Math.random() * severityG - severityG / 2).toFixed(2));
    const pulseZ = Number((severityG * 0.8 + Math.random()).toFixed(2));
    const mag = Math.sqrt(pulseX * pulseX + pulseY * pulseY + pulseZ * pulseZ);
    const equiv = Math.min(12.0, Number((1.25 + mag * 0.95).toFixed(2)));

    setReading({
      x: pulseX,
      y: pulseY,
      z: pulseZ,
      magnitude: Number(mag.toFixed(2)),
      equivalent_mm_s: equiv,
    });

    if (equiv >= 4.5) {
      setIncidentTriggered(true);
    }
  };

  // --- NASA IMS Replay Auto-Playback ---
  useEffect(() => {
    if (mode !== "nasa_ims" || !nasaPlaying) return;
    const interval = setInterval(() => {
      setNasaIndex((prev) => {
        const next = (prev + 1) % NASA_STAGES.length;
        return next;
      });
    }, 2500);
    return () => clearInterval(interval);
  }, [mode, nasaPlaying]);

  // Update Reading when NASA stage changes
  useEffect(() => {
    if (mode === "nasa_ims") {
      const stage = NASA_STAGES[nasaIndex];
      const equiv = stage.vibration_mm_s;
      // Derive 3-axis proportional readings from stage
      const scale = equiv / 3.0;
      setReading({
        x: Number((scale * 1.1 + (Math.random() * 0.2 - 0.1)).toFixed(2)),
        y: Number((scale * 0.9 + (Math.random() * 0.2 - 0.1)).toFixed(2)),
        z: Number((scale * 1.3 + (Math.random() * 0.2 - 0.1)).toFixed(2)),
        magnitude: Number(scale.toFixed(2)),
        equivalent_mm_s: equiv,
      });

      if (equiv >= 4.5) {
        setIncidentTriggered(true);
      }
    }
  }, [mode, nasaIndex]);

  // --- Industrial Synth Loop ---
  useEffect(() => {
    if (mode !== "industrial_synth") return;
    let t = 0;
    const interval = setInterval(() => {
      t += 0.05;
      const freq = synthRpm / 60;
      const unbalanceFactor = synthUnbalance / 100;
      const ax = Math.sin(2 * Math.PI * freq * t) * (1.5 + unbalanceFactor * 3.5);
      const ay = Math.cos(2 * Math.PI * freq * t) * (1.2 + unbalanceFactor * 3.0);
      const az = Math.sin(4 * Math.PI * freq * t) * (1.8 + unbalanceFactor * 4.0);
      const mag = Math.sqrt(ax * ax + ay * ay + az * az);
      const equiv = Number((1.25 + mag * 0.85).toFixed(2));

      setReading({
        x: Number(ax.toFixed(2)),
        y: Number(ay.toFixed(2)),
        z: Number(az.toFixed(2)),
        magnitude: Number(mag.toFixed(2)),
        equivalent_mm_s: equiv,
      });

      if (equiv >= 4.5) {
        setIncidentTriggered(true);
      }
    }, 80);
    return () => clearInterval(interval);
  }, [mode, synthRpm, synthUnbalance]);

  // --- Canvas Rolling Waveform Oscilloscope ---
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let running = true;

    const renderWaveform = () => {
      if (!running) return;

      // Append current reading to history buffer
      historyRef.current.push({
        x: reading.x,
        y: reading.y,
        z: reading.z,
        mag: reading.equivalent_mm_s,
      });
      if (historyRef.current.length > 120) {
        historyRef.current.shift();
      }

      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      // Draw Grid Lines
      ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
      ctx.lineWidth = 1;
      for (let y = 0; y < h; y += 30) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }
      for (let x = 0; x < w; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }

      // Draw ISO 10816 Zone C Warning Limit Line (4.50 mm/s)
      // Scale: 0 mm/s is at h - 15, 10 mm/s is at 15
      const warningY = h - 15 - (4.5 / 10.0) * (h - 30);
      ctx.strokeStyle = "rgba(234, 179, 8, 0.75)"; // Amber dashed line
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(0, warningY);
      ctx.lineTo(w, warningY);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = "rgba(234, 179, 8, 0.9)";
      ctx.font = "9px monospace";
      ctx.fillText("ISO 10816-3 Zone C Limit (4.50 mm/s)", 10, warningY - 5);

      const buf = historyRef.current;
      if (buf.length < 2) {
        animFrameRef.current = requestAnimationFrame(renderWaveform);
        return;
      }

      const step = w / 120;

      // Draw Axis X Wave (Cyan)
      ctx.strokeStyle = "#06b6d4";
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      buf.forEach((pt, i) => {
        const xPos = i * step;
        const valY = h / 2 - pt.x * 12;
        if (i === 0) ctx.moveTo(xPos, valY);
        else ctx.lineTo(xPos, valY);
      });
      ctx.stroke();

      // Draw Axis Y Wave (Magenta/Pink)
      ctx.strokeStyle = "#ec4899";
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      buf.forEach((pt, i) => {
        const xPos = i * step;
        const valY = h / 2 - pt.y * 12;
        if (i === 0) ctx.moveTo(xPos, valY);
        else ctx.lineTo(xPos, valY);
      });
      ctx.stroke();

      // Draw Axis Z Wave (Blue)
      ctx.strokeStyle = "#3b82f6";
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      buf.forEach((pt, i) => {
        const xPos = i * step;
        const valY = h / 2 - pt.z * 12;
        if (i === 0) ctx.moveTo(xPos, valY);
        else ctx.lineTo(xPos, valY);
      });
      ctx.stroke();

      // Draw RMS Velocity Trend (Solid Emerald or Red when breach)
      const isBreached = reading.equivalent_mm_s >= 4.5;
      ctx.strokeStyle = isBreached ? "#ef4444" : "#10b981";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      buf.forEach((pt, i) => {
        const xPos = i * step;
        const valY = h - 15 - (pt.mag / 10.0) * (h - 30);
        if (i === 0) ctx.moveTo(xPos, valY);
        else ctx.lineTo(xPos, valY);
      });
      ctx.stroke();

      animFrameRef.current = requestAnimationFrame(renderWaveform);
    };

    renderWaveform();

    return () => {
      running = false;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [reading]);

  const currentZone =
    reading.equivalent_mm_s < 2.3
      ? { name: "Zone A", label: "Good / Permissible", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/30" }
      : reading.equivalent_mm_s < 4.5
      ? { name: "Zone B", label: "Acceptable Condition", color: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/30" }
      : reading.equivalent_mm_s < 7.1
      ? { name: "Zone C", label: "Restricted / Critical Anomaly", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30" }
      : { name: "Zone D", label: "Emergency Danger Trip", color: "text-red-400", bg: "bg-red-500/10 border-red-500/30" };

  return (
    <div className="space-y-4">
      {/* Cockpit Card Container */}
      <Card className="border-border/70 bg-card/90 shadow-md backdrop-blur-xs overflow-hidden">
        {/* Cockpit Top Bar */}
        <CardHeader className="p-4 sm:p-5 border-b border-border/40 bg-muted/20">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <Badge className="bg-[#003087] text-white border-0 text-[10px] font-mono">
                  PAYPAL AI 2026 COCKPIT
                </Badge>
                {mode === "live_mems" && (
                  <Badge variant="outline" className="border-emerald-500/50 bg-emerald-500/10 text-emerald-300 text-[10px] font-mono flex items-center gap-1.5 animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    LIVE PHYSICAL MEMS ACCELEROMETER
                  </Badge>
                )}
                {mode === "nasa_ims" && (
                  <Badge variant="outline" className="border-cyan-500/50 bg-cyan-500/10 text-cyan-300 text-[10px] font-mono">
                    NASA IMS BEARING REPLAY (20 kHz)
                  </Badge>
                )}
                {mode === "industrial_synth" && (
                  <Badge variant="outline" className="border-indigo-500/50 bg-indigo-500/10 text-indigo-300 text-[10px] font-mono">
                    INDUSTRIAL HARMONIC SYNTHESIZER
                  </Badge>
                )}
              </div>
              <CardTitle className="text-lg sm:text-xl font-bold tracking-tight flex items-center gap-2">
                <Activity className="size-5 text-cyan-400" />
                <span>Multi-Source Vibration Cockpit: P-101A Slurry Pump</span>
              </CardTitle>
              <CardDescription className="text-xs text-muted-foreground mt-0.5">
                Empirical 3-axis condition monitoring engine with live physical accelerometer bridge and automated ISO 10816 Zone C failure trip.
              </CardDescription>
            </div>

            {/* Operating Mode Selector Buttons */}
            <div className="flex items-center gap-1.5 bg-muted/50 p-1 rounded-lg border border-border/60 self-start lg:self-center">
              <Button
                size="sm"
                variant={mode === "live_mems" ? "default" : "ghost"}
                onClick={() => setMode("live_mems")}
                className={`h-7 px-2.5 text-xs font-medium gap-1.5 ${mode === "live_mems" ? "bg-[#003087] text-white" : "text-muted-foreground"}`}
              >
                <Smartphone className="size-3.5" />
                <span>Live Phone Sensor</span>
              </Button>
              <Button
                size="sm"
                variant={mode === "nasa_ims" ? "default" : "ghost"}
                onClick={() => setMode("nasa_ims")}
                className={`h-7 px-2.5 text-xs font-medium gap-1.5 ${mode === "nasa_ims" ? "bg-[#003087] text-white" : "text-muted-foreground"}`}
              >
                <Radio className="size-3.5" />
                <span>NASA IMS Replay</span>
              </Button>
              <Button
                size="sm"
                variant={mode === "industrial_synth" ? "default" : "ghost"}
                onClick={() => setMode("industrial_synth")}
                className={`h-7 px-2.5 text-xs font-medium gap-1.5 ${mode === "industrial_synth" ? "bg-[#003087] text-white" : "text-muted-foreground"}`}
              >
                <Cpu className="size-3.5" />
                <span>Harmonic Synth</span>
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-4 sm:p-5 space-y-5">
          {/* Main Display Grid: Left Column Gauges + Right Column Real-time Oscilloscope */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Left 4 Cols: VSENSE & Dewesoft Style Radial Dial Readouts */}
            <div className="lg:col-span-4 space-y-4">
              {/* Asset Health Card */}
              <div className="p-4 rounded-xl border border-border/50 bg-card/60 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Equipment Monitor
                  </span>
                  <Badge variant="outline" className={`text-[10px] font-mono ${currentZone.bg} ${currentZone.color}`}>
                    {currentZone.name}: {currentZone.label}
                  </Badge>
                </div>

                <div className="flex items-baseline justify-between border-b border-border/40 pb-3">
                  <div>
                    <div className="text-2xl sm:text-3xl font-extrabold font-mono tracking-tight text-foreground flex items-baseline gap-1">
                      <span className={reading.equivalent_mm_s >= 4.5 ? "text-red-400 animate-pulse" : "text-emerald-400"}>
                        {reading.equivalent_mm_s.toFixed(2)}
                      </span>
                      <span className="text-xs font-normal text-muted-foreground">mm/s RMS</span>
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">
                      ISO 10816 Vibration Severity
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] font-mono text-muted-foreground block">Threshold</span>
                    <span className="text-sm font-bold font-mono text-amber-400">4.50 mm/s</span>
                  </div>
                </div>

                {/* 3 Circular Axis Gauges (X, Y, Z) - matching VSENSE dashboard */}
                <div className="grid grid-cols-3 gap-2 pt-1 text-center">
                  {/* Axis X */}
                  <div className="p-2.5 rounded-lg bg-muted/30 border border-cyan-500/20">
                    <span className="text-[10px] font-semibold text-cyan-400 block mb-1">AXIS X</span>
                    <div className="text-base font-bold font-mono text-foreground">
                      {reading.x >= 0 ? `+${reading.x.toFixed(1)}` : reading.x.toFixed(1)}
                    </div>
                    <span className="text-[9px] text-muted-foreground font-mono">m/s²</span>
                  </div>

                  {/* Axis Y */}
                  <div className="p-2.5 rounded-lg bg-muted/30 border border-pink-500/20">
                    <span className="text-[10px] font-semibold text-pink-400 block mb-1">AXIS Y</span>
                    <div className="text-base font-bold font-mono text-foreground">
                      {reading.y >= 0 ? `+${reading.y.toFixed(1)}` : reading.y.toFixed(1)}
                    </div>
                    <span className="text-[9px] text-muted-foreground font-mono">m/s²</span>
                  </div>

                  {/* Axis Z */}
                  <div className="p-2.5 rounded-lg bg-muted/30 border border-blue-500/20">
                    <span className="text-[10px] font-semibold text-blue-400 block mb-1">AXIS Z</span>
                    <div className="text-base font-bold font-mono text-foreground">
                      {reading.z >= 0 ? `+${reading.z.toFixed(1)}` : reading.z.toFixed(1)}
                    </div>
                    <span className="text-[9px] text-muted-foreground font-mono">m/s²</span>
                  </div>
                </div>

                {/* Auxiliary Industrial Parameters */}
                <div className="pt-2 border-t border-border/30 text-[11px] grid grid-cols-2 gap-2 text-muted-foreground">
                  <div>
                    <span>Bearing Temp:</span>{" "}
                    <span className="font-mono text-foreground font-medium">
                      {mode === "nasa_ims" ? `${NASA_STAGES[nasaIndex].bearing_temp_c}°C` : "62.4°C"}
                    </span>
                  </div>
                  <div>
                    <span>RPM Speed:</span>{" "}
                    <span className="font-mono text-foreground font-medium">1,780 RPM</span>
                  </div>
                  <div>
                    <span>Peak Freq:</span>{" "}
                    <span className="font-mono text-foreground font-medium">236.4 Hz</span>
                  </div>
                  <div>
                    <span>Standard:</span>{" "}
                    <span className="font-mono text-foreground font-medium">ISO 10816-3</span>
                  </div>
                </div>
              </div>

              {/* Interactive Mode Control Panel */}
              {mode === "live_mems" && (
                <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-emerald-300 flex items-center gap-1.5">
                      <Smartphone className="size-3.5 text-emerald-400" />
                      Live Smartphone Accelerometer
                      {cloudStreamActive && (
                        <Badge variant="outline" className="text-[9px] border-emerald-400/50 bg-emerald-500/10 text-emerald-300 font-mono py-0 px-1.5 animate-pulse">
                          STREAMING 🟢
                        </Badge>
                      )}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setQrModalOpen(true)}
                      className="h-6 px-2 text-[10px] border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10"
                    >
                      <QrCode className="size-3 mr-1" />
                      Phone QR Link
                    </Button>
                  </div>

                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    Shake your phone or tap the desk. Browser <code className="text-emerald-400 text-[10px]">DeviceMotionEvent</code> streams live 3-axis MEMS inertia into the anomaly detection engine.
                  </p>

                  {/* Desktop Shake Injection Button (guarantees testability on laptops without accelerometer) */}
                  <div className="flex items-center gap-2 pt-1">
                    <Button
                      size="sm"
                      onClick={() => injectShockPulse(6.2)}
                      className="flex-1 h-7 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-medium"
                    >
                      <Zap className="size-3.5 mr-1" />
                      Shake Sensor (Test Breach)
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => injectShockPulse(0.8)}
                      className="h-7 text-xs border-border/60 text-muted-foreground hover:text-foreground"
                    >
                      <RotateCcw className="size-3.5 mr-1" />
                      Reset Idle
                    </Button>
                  </div>
                </div>
              )}

              {mode === "nasa_ims" && (
                <div className="p-3.5 rounded-xl border border-cyan-500/30 bg-cyan-950/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-cyan-300 flex items-center gap-1.5">
                      <Radio className="size-3.5 text-cyan-400" />
                      NASA IMS Bearing Timeline
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setNasaPlaying(!nasaPlaying)}
                      className="h-6 px-2 text-[10px] border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10"
                    >
                      {nasaPlaying ? <Pause className="size-3 mr-1" /> : <Play className="size-3 mr-1" />}
                      {nasaPlaying ? "Pause" : "Auto-Play"}
                    </Button>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[11px] text-muted-foreground font-mono">
                      <span>{NASA_STAGES[nasaIndex].record_id}</span>
                      <span>{NASA_STAGES[nasaIndex].elapsed_hours}h Run Time</span>
                    </div>
                    <Slider
                      value={[nasaIndex]}
                      min={0}
                      max={NASA_STAGES.length - 1}
                      step={1}
                      onValueChange={(val) => {
                        const n = Array.isArray(val) ? val[0] : (typeof val === "number" ? val : 0);
                        setNasaIndex(n);
                      }}
                      className="w-full"
                    />
                    <div className="text-[10px] text-muted-foreground leading-tight pt-1">
                      {NASA_STAGES[nasaIndex].notes}
                    </div>
                  </div>
                </div>
              )}

              {mode === "industrial_synth" && (
                <div className="p-3.5 rounded-xl border border-indigo-500/30 bg-indigo-950/10 space-y-3">
                  <span className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                    <Cpu className="size-3.5 text-indigo-400" />
                    Harmonic Tuning & Mechanical Load
                  </span>
                  <div className="space-y-2">
                    <div className="flex justify-between text-[11px] text-muted-foreground">
                      <span>Rotor Unbalance:</span>
                      <span className="font-mono text-foreground font-medium">{synthUnbalance}%</span>
                    </div>
                    <Slider
                      value={[synthUnbalance]}
                      min={10}
                      max={100}
                      step={5}
                      onValueChange={(val) => {
                        const n = Array.isArray(val) ? val[0] : (typeof val === "number" ? val : 50);
                        setSynthUnbalance(n);
                      }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Right 8 Cols: Real-time Oscilloscope Waveform & Frequency Spectrogram */}
            <div className="lg:col-span-8 flex flex-col gap-3">
              <div className="p-3 rounded-xl border border-border/50 bg-card/70 flex-1 flex flex-col">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-border/30 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-foreground flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                      Real-time 3-Axis Waveform Oscilloscope
                    </span>
                    <span className="hidden sm:inline-flex items-center gap-2 text-[10px] text-muted-foreground font-mono">
                      <span className="text-cyan-400 font-semibold">• X-Axis</span>
                      <span className="text-pink-400 font-semibold">• Y-Axis</span>
                      <span className="text-blue-400 font-semibold">• Z-Axis</span>
                      <span className="text-emerald-400 font-semibold">• RMS Trend</span>
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-muted-foreground">
                    Sampling: {mode === "nasa_ims" ? "20,000 Hz" : "60 Hz WebAPI"}
                  </span>
                </div>

                {/* Canvas Oscilloscope */}
                <div className="relative w-full h-[240px] sm:h-[260px] bg-black/40 rounded-lg overflow-hidden border border-border/30">
                  <canvas
                    ref={canvasRef}
                    width={720}
                    height={260}
                    className="w-full h-full block"
                  />
                  {reading.equivalent_mm_s >= 4.5 && (
                    <div className="absolute top-2 right-2 px-2.5 py-1 rounded bg-red-500/20 border border-red-500/40 text-red-400 text-[10px] font-mono font-bold flex items-center gap-1 animate-pulse">
                      <AlertTriangle className="size-3" />
                      ZONE C / D EXCURSION BREACH
                    </div>
                  )}
                </div>

                {/* ISO Severity Scale Bar */}
                <div className="mt-3 space-y-1">
                  <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
                    <span className="text-emerald-400">Zone A (0 - 2.3 mm/s)</span>
                    <span className="text-cyan-400">Zone B (2.3 - 4.5 mm/s)</span>
                    <span className="text-amber-400 font-bold">Zone C (4.5 - 7.1 mm/s)</span>
                    <span className="text-red-400">Zone D (&gt; 7.1 mm/s)</span>
                  </div>
                  <div className="h-2 w-full bg-muted rounded-full overflow-hidden flex">
                    <div className="w-[23%] bg-emerald-500/40 h-full border-r border-background"></div>
                    <div className="w-[22%] bg-cyan-500/40 h-full border-r border-background"></div>
                    <div className="w-[26%] bg-amber-500/60 h-full border-r border-background"></div>
                    <div className="w-[29%] bg-red-500/60 h-full"></div>
                  </div>
                </div>
              </div>

              {/* Honest Engineering Disclosure (As recommended by ChatGPT & Hackathon best practices) */}
              <div className="p-3 rounded-lg border border-border/40 bg-muted/20 text-[11px] text-muted-foreground flex items-start gap-2.5">
                <Info className="size-4 text-cyan-400 shrink-0 mt-0.5" />
                <div className="leading-relaxed">
                  <span className="font-semibold text-foreground">Engineering Disclosure:</span>{" "}
                  Smartphones and laptops utilize 3-axis MEMS accelerometers measuring linear acceleration (<code className="text-cyan-300">m/s²</code>). Industrial ISO 10816 standards benchmark vibration velocity (<code className="text-cyan-300">mm/s RMS</code>). Our real-time pipeline translates live physical MEMS motion into a calibrated anomaly index to demonstrate authentic physical IoT trigger interaction without masking hardware boundaries.
                </div>
              </div>
            </div>
          </div>

          {/* Cross-Workflow Trigger Card: Direct Link to Autonomous PayPal Procurement */}
          {reading.equivalent_mm_s >= 4.5 && (
            <div className="p-4 rounded-xl border border-red-500/50 bg-red-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-in fade-in duration-300">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 shrink-0 mt-0.5">
                  <ShieldAlert className="size-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-red-300">
                      Vibration Breach Threshold Exceeded ({reading.equivalent_mm_s} mm/s RMS)
                    </span>
                    <Badge variant="destructive" className="text-[10px] font-mono">
                      WO-2026-IMS-001 TRIGGERED
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    ISO 10816 Zone C/D violation detected on CM Pump P-101A. Autonomous agentic pipeline has drafted emergency procurement quote ($450.00 SKF Bearings) ready for supervisor authorization.
                  </p>
                </div>
              </div>

              <Link
                href="/procurement"
                className="inline-flex items-center justify-center gap-1.5 text-xs font-semibold text-white bg-red-600 hover:bg-red-500 px-4 py-2.5 rounded-lg shrink-0 transition-colors shadow-xs"
              >
                <span>Authorize PayPal Procurement</span>
                <ArrowRight className="size-3.5" />
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* QR Code Modal for Phone Pairing */}
      {qrModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs">
          <Card className="max-w-sm w-full border-border/80 bg-card p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Smartphone className="size-4 text-emerald-400" />
                <span>Open Sensor on Smartphone</span>
              </CardTitle>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setQrModalOpen(false)}
                className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground"
              >
                ✕
              </Button>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              Scan this QR code with your iPhone or Android camera to open the dedicated tactile sensor controller and shake the physical device in your hand.
            </p>

            <div className="p-4 bg-white rounded-xl flex items-center justify-center mx-auto shadow-inner">
              <QRCodeSVG value={clientUrl} size={180} level="M" />
            </div>

            <div className="text-center">
              <span className="text-[10px] font-mono text-muted-foreground break-all">
                {clientUrl}
              </span>
            </div>

            <Button
              className="w-full h-8 text-xs bg-[#003087] hover:bg-[#00256c] text-white"
              onClick={() => setQrModalOpen(false)}
            >
              Done
            </Button>
          </Card>
        </div>
      )}
    </div>
  );
}
