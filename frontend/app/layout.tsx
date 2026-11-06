import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/AppShell";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata: Metadata = {
  title: "KinetixRAG | High-Frequency Telemetry & Dynamic Industrial GraphRAG",
  description: "Autonomous industrial intelligence platform bridging high-frequency vibration telemetry, deterministic GraphRAG root-cause analysis, and self-healing operational workflows.",
  icons: {
    icon: [
      { url: "/kr.png", type: "image/png" },
      { url: "/favicon.ico" },
    ],
    shortcut: "/kr.png",
    apple: "/kr.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark min-h-full antialiased">
      <body className="min-h-full">
        <TooltipProvider>
          <AppShell>{children}</AppShell>
        </TooltipProvider>
      </body>
    </html>
  );
}
