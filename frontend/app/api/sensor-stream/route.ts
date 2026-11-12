import { neon } from "@neondatabase/serverless";
import { NextResponse } from "next/server";

// Fallback in-memory state for local testing
let inMemoryState = {
  ax: 0,
  ay: 0,
  az: 0,
  rms: 1.25,
  peak: 1.25,
  breached: false,
  updated_at: new Date().toISOString(),
};

function getDb() {
  const conn = process.env.DATABASE_URL || process.env.DATABASE_URL_UNPOOLED;
  if (!conn) return null;
  return neon(conn);
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { ax = 0, ay = 0, az = 0, rms = 1.25, peak = 1.25, breached = false } = body;

    inMemoryState = {
      ax: Number(ax),
      ay: Number(ay),
      az: Number(az),
      rms: Number(rms),
      peak: Number(peak),
      breached: Boolean(breached),
      updated_at: new Date().toISOString(),
    };

    const sql = getDb();
    if (sql) {
      await sql`
        INSERT INTO live_telemetry (id, ax, ay, az, rms, peak, breached, updated_at)
        VALUES ('current', ${ax}, ${ay}, ${az}, ${rms}, ${peak}, ${breached}, NOW())
        ON CONFLICT (id) DO UPDATE SET
          ax = EXCLUDED.ax,
          ay = EXCLUDED.ay,
          az = EXCLUDED.az,
          rms = EXCLUDED.rms,
          peak = EXCLUDED.peak,
          breached = EXCLUDED.breached,
          updated_at = NOW();
      `;
    }

    return NextResponse.json({ success: true, data: inMemoryState });
  } catch (err: any) {
    return NextResponse.json({ success: true, error: err?.message, data: inMemoryState });
  }
}

export async function GET() {
  try {
    const sql = getDb();
    if (sql) {
      const rows = await sql`
        SELECT ax, ay, az, rms, peak, breached, updated_at 
        FROM live_telemetry 
        WHERE id = 'current' 
        LIMIT 1;
      `;
      if (rows && rows.length > 0) {
        return NextResponse.json({ success: true, source: "neon", data: rows[0] });
      }
    }
    return NextResponse.json({ success: true, source: "memory", data: inMemoryState });
  } catch (err: any) {
    return NextResponse.json({ success: true, source: "memory-fallback", data: inMemoryState });
  }
}
