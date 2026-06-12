"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Check, ExternalLink, LockKeyhole, ShieldAlert, X } from "lucide-react";
import { Shell } from "@/components/shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/badge";
import { LoadingState } from "@/components/loading";
import { useAudit } from "@/hooks/use-audit";
import { money } from "@/lib/api";
import type { Strategy } from "@/lib/types";

export default function DecisionPage() {
  return <Suspense fallback={<LoadingState />}><DecisionEngine /></Suspense>;
}

function DecisionEngine() {
  const id = useSearchParams().get("id");
  const { audit } = useAudit(id);
  if (!id || !audit) return <Shell auditId={id || ""}><LoadingState /></Shell>;

  const approved = audit.strategies.filter((strategy) => strategy.approved);
  const blocked = audit.strategies.filter((strategy) => !strategy.approved);
  const unsafe = audit.strategies.find((strategy) => strategy.id === "slack-cancel");
  const safeSlack = audit.strategies.find((strategy) => strategy.id === "slack-downgrade");

  return <Shell auditId={id}>
    <PageHeader
      eyebrow="Langfuse gate"
      title="The gate turns ideas into decisions."
      description="Claude can propose a recovery strategy. Only Langfuse-audited strategies that pass Margin's deterministic policy can become actions."
      action={audit.trace_url ? <a href={audit.trace_url} target="_blank" className="flex items-center gap-2 rounded-lg border border-[#5eead4]/20 bg-[#5eead4]/[0.04] px-4 py-2.5 text-xs text-[#8af3e3] hover:bg-[#5eead4]/[0.07]">Open Langfuse trace <ExternalLink size={12} /></a> : <Badge tone="warning">Local trace mirror</Badge>}
    />

    <div className="mx-auto max-w-[1180px] space-y-5 p-6 md:p-10">
      <section className="panel overflow-hidden border-[#5eead4]/12">
        <div className="grid lg:grid-cols-[1.2fr_.8fr]">
          <div className="border-b border-white/[0.07] p-6 lg:border-b-0 lg:border-r">
            <div className="flex items-center gap-2"><LockKeyhole size={13} className="text-[#5eead4]" /><span className="eyebrow">Deterministic execution policy</span></div>
            <div className="mt-6 flex items-baseline gap-3"><span className="metric-number text-5xl font-semibold">.85</span><span className="text-xs text-[#6d7580]">action safety</span><span className="text-[#474e58]">+</span><span className="metric-number text-5xl font-semibold">.90</span><span className="text-xs text-[#6d7580]">confidence</span></div>
            <p className="mt-5 max-w-2xl text-[11px] leading-6 text-[#777f89]">Both thresholds must pass. Langfuse makes the model evaluation auditable; Margin enforces the final rule without model discretion.</p>
          </div>
          <div className="grid grid-cols-2 gap-px bg-white/[0.06]">
            <GateCount label="Passed to queue" value={approved.length} accent />
            <GateCount label="Blocked for review" value={blocked.length} />
          </div>
        </div>
      </section>

      {unsafe && safeSlack && <section className="panel overflow-hidden">
        <div className="border-b border-white/[0.07] px-5 py-4"><div className="eyebrow">Why the gate matters</div><div className="mt-1.5 text-[11px] text-[#aeb5be]">The same Slack leak produces two very different actions</div></div>
        <div className="grid gap-px bg-white/[0.06] md:grid-cols-2">
          <GateOutcome icon={ShieldAlert} label="Blocked before your queue" strategy={unsafe} detail="Raw inactivity alone is not enough evidence to remove every seat." />
          <GateOutcome icon={Check} label="Released to your queue" strategy={safeSlack} detail="Owner verification protects active users and makes the action defensible." passed />
        </div>
      </section>}

      <section className="panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4"><div><div className="eyebrow">Evaluated strategies</div><div className="mt-1.5 text-[11px] text-[#aeb5be]">Every result recorded in the live Langfuse trace</div></div><Badge>{audit.strategies.length} scored</Badge></div>
        <div className="divide-y divide-white/[0.06]">
          {audit.strategies.map((strategy) => <StrategyRow key={strategy.id} strategy={strategy} />)}
        </div>
      </section>

      <details className="panel group overflow-hidden">
        <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4">
          <div><div className="text-[11px] font-medium text-[#c4cad1]">Langfuse observation ledger</div><div className="mt-1 text-[8px] text-[#626b76]">Open to inspect each root workflow observation</div></div>
          <ArrowRight size={13} className="text-[#69717c] transition-transform group-open:rotate-90" />
        </summary>
        <div className="divide-y divide-white/[0.06] border-t border-white/[0.07]">
          {audit.trace_tree?.children.map((node) => <div key={node.id} className="flex items-center gap-4 px-5 py-3"><span className="mono w-20 text-[8px] text-[#5d6570]">{node.id}</span><span className="flex-1 text-[9px] text-[#aeb5be]">{node.label}</span><span className="mono text-[8px] text-[#626b76]">{node.duration_ms} ms</span><Badge tone={node.status === "completed" ? "accent" : "warning"}>{node.status}</Badge></div>)}
        </div>
      </details>
    </div>
  </Shell>;
}

function GateCount({ label, value, accent = false }: { label: string; value: number; accent?: boolean }) {
  return <div className="flex flex-col justify-center bg-[#111318] p-6"><div className="eyebrow">{label}</div><div className={`metric-number mt-4 text-5xl font-semibold ${accent ? "text-[#8af3e3]" : "text-[#d6dae0]"}`}>{value}</div></div>;
}

function GateOutcome({ icon: Icon, label, strategy, detail, passed = false }: { icon: typeof Check; label: string; strategy: Strategy; detail: string; passed?: boolean }) {
  return <div className="bg-[#111318] p-5"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><Icon size={13} className={passed ? "text-[#5eead4]" : "text-[#fca5a5]"} /><span className="eyebrow">{label}</span></div><Badge tone={passed ? "accent" : "danger"}>{strategy.scores.action_safety.toFixed(2)} safety</Badge></div><div className="mt-5 text-base font-medium">{strategy.title}</div><div className="metric-number mt-3 text-2xl font-semibold">{money(strategy.savings)}</div><p className="mt-3 text-[9px] leading-5 text-[#737b86]">{detail}</p></div>;
}

function StrategyRow({ strategy }: { strategy: Strategy }) {
  const scores = [["Confidence", strategy.scores.confidence], ["Action safety", strategy.scores.action_safety], ["Evidence", strategy.scores.evidence_completeness], ["Expected ROI", strategy.scores.expected_roi], ["Citation coverage", strategy.scores.citation_coverage], ["Hallucination risk", strategy.scores.hallucination_risk]] as const;
  return <details className="group">
    <summary className="grid cursor-pointer list-none gap-4 px-5 py-4 md:grid-cols-[auto_1fr_auto_auto] md:items-center">
      <div className={`flex h-8 w-8 items-center justify-center rounded-lg border ${strategy.approved ? "border-[#5eead4]/20 bg-[#5eead4]/[0.05] text-[#5eead4]" : "border-[#fca5a5]/15 bg-[#fca5a5]/[0.04] text-[#fca5a5]"}`}>{strategy.approved ? <Check size={13} /> : <X size={13} />}</div>
      <div><div className="flex items-center gap-2"><span className="text-[10px] font-medium text-[#c2c8cf]">{strategy.title}</span><span className="text-[8px] text-[#656e79]">{strategy.vendor}</span></div><div className="mt-1 text-[8px] text-[#626b76]">{strategy.description}</div></div>
      <div className="metric-number text-sm font-semibold text-[#d6dae0]">{money(strategy.savings)}</div>
      <Badge tone={strategy.approved ? "accent" : "danger"}>{strategy.approved ? "passed" : "blocked"}</Badge>
    </summary>
    <div className="grid gap-4 border-t border-white/[0.055] bg-[#0e1014] px-5 py-4 md:grid-cols-3">
      {scores.map(([label, value]) => <div key={label}><div className="mb-1.5 flex justify-between text-[8px] text-[#717985]"><span>{label}</span><span className="mono">{value.toFixed(2)}</span></div><div className="h-1 overflow-hidden rounded-full bg-white/[0.06]"><div className={`h-full rounded-full ${label !== "Hallucination risk" && value >= 0.9 ? "bg-[#5eead4]" : "bg-[#68717c]"}`} style={{ width: `${value * 100}%` }} /></div></div>)}
    </div>
  </details>;
}
