"use client";

import { Check, ExternalLink, Globe2, Search } from "lucide-react";
import { motion } from "motion/react";
import type { ResearchActivity, ResearchFinding } from "@/lib/types";
import { Badge } from "@/components/badge";

export function BrowserResearchPanel({ activities, findings }: { activities: ResearchActivity[]; findings: ResearchFinding[] }) {
  const current = activities.at(-1);
  const activity = current?.kind === "cite" ? activities.findLast((item) => item.url) || current : current;
  const recent = [...activities].reverse().slice(0, 6);
  const liveSources = findings.filter((finding) => finding.source_status === "live").length;

  return <section className="panel overflow-hidden border-[#5eead4]/10">
    <div className="flex flex-col gap-3 border-b border-white/[0.07] px-5 py-4 md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#5eead4]/18 bg-[#5eead4]/[0.04]"><Globe2 size={15} className="text-[#5eead4]" /></div>
        <div><div className="eyebrow text-[#73938e]">Live market evidence</div><div className="mt-1 text-[11px] text-[#aeb5be]">Every search and source strengthens or weakens the recovery case.</div></div>
      </div>
      <div className="flex items-center gap-2"><Badge>{activities.length} operations</Badge><Badge tone="accent">{findings.length} sources</Badge></div>
    </div>

    <div className="grid min-h-[440px] xl:grid-cols-[1.45fr_.55fr]">
      <div className="flex flex-col border-b border-white/[0.07] bg-[#0c0e12] p-5 xl:border-b-0 xl:border-r">
        <div className="flex items-center gap-2 text-[8px] uppercase tracking-[0.12em] text-[#555d68]">
          <span className="status-dot" /> What Margin is proving now
        </div>
        <motion.div key={activity?.id || "waiting"} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="my-auto py-8">
          <div className="flex items-center gap-2"><Badge tone="accent">{activity?.kind || "waiting"}</Badge><span className="mono text-[9px] text-[#606874]">operation {activities.length || 0} / 33</span></div>
          <h2 className="mt-6 max-w-3xl text-3xl font-medium tracking-[-0.045em] text-[#e0e3e7]">{activity?.label || "Waiting for market research"}</h2>
          <p className="mt-4 max-w-3xl text-xs leading-6 text-[#858d97]">{activity?.detail || "The browser agent will expose each external research operation as it happens."}</p>
          <div className="mono mt-6 max-w-4xl break-all rounded-lg border border-white/[0.07] bg-black/20 px-4 py-3 text-[10px] leading-5 text-[#76808b]">{activity?.url || activity?.query || "Official pricing and competitor sites will appear here."}</div>
          {activity?.url && <a href={activity.url} target="_blank" className="mt-5 inline-flex items-center gap-2 text-[10px] font-medium text-[#8af3e3] hover:text-white">Open current source <ExternalLink size={11} /></a>}
        </motion.div>
        <div className="grid grid-cols-3 gap-px overflow-hidden rounded-lg border border-white/[0.06] bg-white/[0.06]">
          <BrowserFact label="Operations" value={String(activities.length)} />
          <BrowserFact label="Live sources" value={String(liveSources)} />
          <BrowserFact label="Citations ready" value={String(findings.length)} />
        </div>
      </div>

      <div className="bg-[#101217] p-5">
        <div className="mb-5 flex items-center justify-between"><span className="eyebrow">Latest activity</span><Search size={12} className="text-[#5eead4]" /></div>
        <div className="space-y-1">
          {recent.length ? recent.map((item, index) => <div key={item.id} className="flex gap-3 border-b border-white/[0.055] py-3 last:border-0">
            <span className="mono mt-0.5 shrink-0 text-[8px] text-[#59616c]">{String(activities.length - index).padStart(2, "0")}</span>
            <div className="min-w-0"><div className="truncate text-[10px] font-medium text-[#aeb5be]">{item.label}</div><div className="mt-1 flex items-center gap-2"><span className="mono text-[7px] uppercase text-[#5eead4]">{item.kind}</span><span className="truncate text-[8px] text-[#5e6671]">{item.vendor || item.query || item.url}</span></div></div>
          </div>) : <div className="py-12 text-center text-[10px] text-[#646c77]">Activity appears here as the agent browses.</div>}
        </div>
      </div>
    </div>
  </section>;
}

function BrowserFact({ label, value }: { label: string; value: string }) {
  return <div className="bg-[#101217] px-4 py-3"><div className="eyebrow">{label}</div><div className="metric-number mt-2 text-lg font-semibold text-[#d8dce1]">{value}</div></div>;
}

export function SourceLedger({ findings }: { findings: ResearchFinding[] }) {
  return <div className="divide-y divide-white/[0.06]">
    {findings.map((finding) => <a key={finding.vendor} href={finding.source_url} target="_blank" className="flex items-center gap-4 px-5 py-4 hover:bg-white/[0.018]">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/[0.07]"><Check size={10} className="text-[#5eead4]" /></div>
      <div className="min-w-0 flex-1"><div className="flex items-center gap-2"><span className="text-[10px] font-medium text-[#bec3cb]">{finding.vendor}</span><Badge tone={finding.source_status === "live" ? "accent" : "warning"}>{finding.source_status}</Badge></div><div className="mt-1 truncate text-[8px] text-[#626b76]">{finding.finding}</div></div>
      <ExternalLink size={10} className="text-[#59616c]" />
    </a>)}
  </div>;
}
