import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Margin - Autonomous Spend Recovery",
  description: "Detect, validate, and recover SaaS spend leakage.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
