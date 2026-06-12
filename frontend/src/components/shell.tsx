"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BrainCircuit, Database, FileText, Gauge, Globe2, ListChecks } from "lucide-react";
import { Logo } from "@/components/logo";
import { cn } from "@/lib/cn";
const links = [
  ["Results", Gauge, "overview"],
  ["Research", Globe2, "research"],
  ["Langfuse", BrainCircuit, "decision"],
  ["ClickHouse", Database, "memory"],
  ["Decisions", ListChecks, "actions"],
  ["Report", FileText, "report"],
] as const;
export function Shell({ auditId, children }: { auditId: string; children: React.ReactNode }) {
  const pathname = usePathname(); const id = auditId;
  const hrefFor = (key: string) => key === "overview" ? `/audits/${id}/overview` : `/${key}?id=${id}`;
  return <div className="min-h-screen bg-[#08090B]"><aside className="fixed inset-y-0 left-0 z-30 hidden w-[208px] border-r border-white/[0.07] bg-[#0b0c0f] px-4 py-5 lg:block"><div className="px-2"><Logo /></div><div className="mt-9 px-2"><div className="eyebrow mb-3">AcmeAI workspace</div><div className="flex items-center gap-2 text-[11px] text-[#b7bbc4]"><Activity size={12} className="text-[#5eead4]" /> Active audit</div></div><nav className="mt-8 space-y-1">{links.map(([label, Icon, key]) => <Link key={key} href={hrefFor(key)} className={cn("flex items-center gap-3 rounded-lg px-3 py-2.5 text-[11px] transition-colors", pathname.includes(key) ? "bg-white/[0.055] text-white" : "text-[#777d88] hover:bg-white/[0.03] hover:text-[#c8ccd4]")}><Icon size={13} strokeWidth={1.8} />{label}</Link>)}</nav><div className="absolute bottom-5 left-4 right-4 rounded-xl border border-white/[0.07] bg-white/[0.02] p-3"><div className="flex items-center gap-2 text-[10px] text-[#a4a9b2]"><span className="status-dot" /> Demo ready</div><div className="mt-1.5 truncate font-mono text-[8px] text-[#5e6470]">{id}</div></div></aside><main className="lg:pl-[208px]">{children}</main></div>;
}
