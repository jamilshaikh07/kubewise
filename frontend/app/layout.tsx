import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KubeWise — Kubernetes Cost & Performance Optimization",
  description:
    "Advisory-only Kubernetes cost and performance optimization. Detect waste, right-size workloads, estimate savings.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full" suppressHydrationWarning>
      <body className="h-full bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
