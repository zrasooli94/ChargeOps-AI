import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChargeOps AI",
  description: "Agentic EV Charging Intelligence & Operations Platform",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
