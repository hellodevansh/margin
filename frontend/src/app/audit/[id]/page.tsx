"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowRight, BrainCircuit, Database, MessageSquare } from "lucide-react";
import { motion } from "motion/react";
import { API_URL } from "@/lib/api";
import type { AuditEvent, ResearchActivity } from "@/lib/types";
import { useAudit } from "@/hooks/use-audit";
import { Logo } from "@/components/logo";
import { Badge } from "@/components/badge";
import { WorkflowRibbon } from "@/components/workflow-ribbon";
import { BrowserResearchPanel } from "@/components/browser-research-panel";

export default function LiveAudit() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const { audit } = useAudit(id, true);

  useEffect(() => {
    const source = new EventSource(`${API_URL}/api/audits/${id}/events`);
    source.addEventListener("audit", (message) => {
      const event = JSON.parse((message as MessageEvent).data) as AuditEvent;
      setEvents((current) => [...current, event]);
      if (event.step === "complete") source.close();
    });
    source.onerror = () => source.close();
    return () => source.close();
  }, [id]);

  const completed = useMemo(() => new Set(events.filter((item) => item.status === "completed").map((item) => item.step)), [events]);
  const current = events.at(-1)?.step;
  const activities = events.map((event) => event.payload?.activity).filter(Boolean) as ResearchActivity[];
  const done = audit?.status === "completed";
  const activeMessage = [...events].reverse().find((event) => event.status === "started" || event.status === "progress")?.message || "Preparing audit";

  return <main className="min-h-screen bg-[#08090B]">
    <header className="flex h-16 items-center justify-between border-b border-white/[0.07] px-6 md:px-9"><Logo /><div className="flex items-center gap-3"><Badge tone={done ? "accent" : "warning"}>{done ? "Audit ready for decisions" : activeMessage}</Badge><span className="mono hidden text-[10px] text-[#59606b] md:block">{id}</span></div></header>
    <section className="mx-auto max-w-[1500px] px-5 py-7 md:px-9">
      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between"><div><div className="eyebrow mb-2">Live recovery case</div><h1 className="text-3xl font-semibold tracking-[-0.045em]">Watch every action earn its place.</h1><p className="mt-2 text-sm text-[#7e848e]">Margin finds the waste, verifies the facts, proves the market case, and blocks unsafe shortcuts before you decide.</p></div>{done && <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} onClick={() => router.push(`/actions?id=${id}`)} className="flex items-center gap-2 rounded-lg border border-[#5eead4]/20 bg-[#5eead4] px-4 py-2.5 text-xs font-semibold text-[#07110f] hover:bg-[#83f1e0]">Review released actions <ArrowRight size={13} /></motion.button>}</div>
      <WorkflowRibbon completed={completed} current={current} />

      <div className="mt-5"><BrowserResearchPanel activities={activities.length ? activities : audit?.research_activity || []} findings={audit?.research || []} /></div>

      <div className="mt-5 grid gap-px overflow-hidden rounded-xl border border-white/[0.07] bg-white/[0.06] lg:grid-cols-3">
        <SystemRole icon={MessageSquare} name="Slack verification posted" status={completed.has("verification")} value={audit?.verification_events.some((event) => event.interpretation) ? "Live Figma reply captured" : "Waiting for Figma owner reply"} />
        <SystemRole icon={BrainCircuit} name="Langfuse gates risk" status={completed.has("gate")} value={`${audit?.strategies.length || 0} strategies scored`} />
        <SystemRole icon={Database} name="ClickHouse stores proof" status={completed.has("memory")} value={`${audit?.analytics.row_count || 0} rows queried`} />
      </div>
    </section>
  </main>;
}

function SystemRole({ icon: Icon, name, status, value }: { icon: typeof Database; name: string; status: boolean; value: string }) {
  return <section className="flex items-center gap-3 bg-[#111318] p-4"><div className="flex h-8 w-8 items-center justify-center rounded-lg border border-[#5eead4]/15 bg-[#5eead4]/[0.04]"><Icon size={13} className="text-[#5eead4]" /></div><div className="min-w-0 flex-1"><div className="text-[10px] font-medium text-[#bdc3ca]">{name}</div><div className="mt-1 text-[8px] text-[#656e79]">{value}</div></div><Badge tone={status ? "accent" : "warning"}>{status ? "complete" : "working"}</Badge></section>;
}
