"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowRight, BrainCircuit, Check, Database, Globe2 } from "lucide-react";
import { Shell } from "@/components/shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/badge";
import { LoadingState } from "@/components/loading";
import { useAudit } from "@/hooks/use-audit";
import { money } from "@/lib/api";

export default function Overview() {
  const { id } = useParams<{ id: string }>();
  const { audit } = useAudit(id, true);
  if (!audit) return <Shell auditId={id}><LoadingState /></Shell>;

  const currentTask = audit.recovery_tasks.find((task) => task.status === "awaiting_verification" || task.status === "pending_approval" || task.status === "held");
  const decided = audit.recovery_tasks.filter((task) => !["awaiting_verification", "pending_approval", "held"].includes(task.status)).length;
  const releasedValue = audit.recovery_tasks.reduce((sum, task) => sum + task.savings, 0);

  return <Shell auditId={id}>
    <PageHeader
      eyebrow="Recovery case ready"
      title={`${money(audit.metrics.potential_leakage)} found. ${money(releasedValue)} cleared for decision.`}
      description="Margin rejected unsafe shortcuts and released three evidence-backed recovery actions. Your next move is clear."
      action={<Link href={`/actions?id=${id}`} className="flex items-center gap-2 rounded-lg bg-[#5eead4] px-4 py-2.5 text-xs font-semibold text-[#07110f] hover:bg-[#83f1e0]">Open decision queue <ArrowRight size={13} /></Link>}
    />

    <div className="mx-auto max-w-[1120px] space-y-5 p-6 md:p-10">
      <section className="panel grid gap-px overflow-hidden bg-white/[0.06] md:grid-cols-3">
        <ResultStat label="Potential leakage found" value={money(audit.metrics.potential_leakage)} />
        <ResultStat label="Gate-released actions" value={money(releasedValue)} accent />
        <ResultStat label="Your decisions" value={`${decided} / ${audit.recovery_tasks.length}`} />
      </section>

      <section className="panel overflow-hidden">
        {currentTask ? <div className="grid lg:grid-cols-[1fr_auto]">
          <div className="p-6">
            <div className="flex items-center gap-2"><Badge tone={currentTask.status === "awaiting_verification" ? "warning" : "accent"}>{currentTask.status === "awaiting_verification" ? "Waiting for live Slack evidence" : "Passed Langfuse gate"}</Badge><Badge>{currentTask.vendor}</Badge></div>
            <h2 className="mt-5 text-3xl font-medium tracking-[-0.045em]">{currentTask.title}</h2>
            <p className="mt-3 max-w-2xl text-xs leading-6 text-[#7d858f]">{currentTask.rationale}</p>
            <div className="mt-6 flex flex-wrap items-center gap-4"><span className="metric-number text-4xl font-semibold text-[#8af3e3]">{money(currentTask.savings)}</span><span className="text-[9px] uppercase tracking-[0.12em] text-[#626b76]">annual recovery</span></div>
          </div>
          <Link href={`/actions?id=${id}`} className="flex min-h-[150px] items-center justify-center gap-2 border-t border-white/[0.07] bg-[#5eead4]/[0.035] px-8 text-[11px] font-semibold text-[#8af3e3] hover:bg-[#5eead4]/[0.06] lg:border-l lg:border-t-0">{currentTask.status === "awaiting_verification" ? "Open live verification" : "Make the next decision"} <ArrowRight size={13} /></Link>
        </div> : <div className="flex flex-col items-center px-6 py-14 text-center"><Check size={17} className="text-[#5eead4]" /><h2 className="mt-4 text-xl font-medium">Decision queue complete</h2><p className="mt-2 text-[10px] text-[#737b86]">All recovery actions have a recorded outcome.</p></div>}
      </section>

      <section className="panel overflow-hidden">
        <div className="border-b border-white/[0.07] px-5 py-4"><div className="eyebrow">Why you can trust the queue</div><div className="mt-1.5 text-[11px] text-[#aeb5be]">Every action has visible market evidence, an audited gate result, and durable memory</div></div>
        <ProofRow href={`/research?id=${id}`} icon={Globe2} title="Market evidence" value={`${audit.research_activity.length} observable browser operations`} detail="See exactly how Margin built the external case." />
        <ProofRow href={`/decision?id=${id}`} icon={BrainCircuit} title="Langfuse decision gate" value={`${audit.strategies.filter((strategy) => strategy.approved).length} released · ${audit.strategies.filter((strategy) => !strategy.approved).length} blocked`} detail="See which ideas became actions and which never reached you." />
        <ProofRow href={`/memory?id=${id}`} icon={Database} title="ClickHouse audit memory" value={`${audit.analytics.row_count} rows across ${audit.analytics.table_counts.length} tables`} detail="Query the complete evidence-to-execution trail." />
      </section>
    </div>
  </Shell>;
}

function ResultStat({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return <div className="bg-[#111318] p-5"><div className="eyebrow">{label}</div><div className={`metric-number mt-4 text-3xl font-semibold ${accent ? "text-[#8af3e3]" : "text-[#e0e3e7]"}`}>{value}</div></div>;
}

function ProofRow({ href, icon: Icon, title, value, detail }: { href: string; icon: typeof Database; title: string; value: string; detail: string }) {
  return <Link href={href} className="group grid gap-3 border-b border-white/[0.06] px-5 py-4 last:border-0 md:grid-cols-[auto_180px_1fr_auto] md:items-center">
    <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-[#5eead4]/15 bg-[#5eead4]/[0.04]"><Icon size={13} className="text-[#5eead4]" /></div>
    <div className="text-[10px] font-medium text-[#c4cad1]">{title}</div>
    <div><div className="text-[10px] text-[#a4abb5]">{value}</div><div className="mt-1 text-[8px] text-[#626b76]">{detail}</div></div>
    <ArrowRight size={12} className="text-[#626b76] transition-transform group-hover:translate-x-1 group-hover:text-[#5eead4]" />
  </Link>;
}
