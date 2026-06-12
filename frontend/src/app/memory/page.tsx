"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowRight, CheckCircle2, Database, Table2, TerminalSquare } from "lucide-react";
import { Shell } from "@/components/shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/badge";
import { LoadingState } from "@/components/loading";
import { useAudit } from "@/hooks/use-audit";

export default function MemoryPage() {
  return <Suspense fallback={<LoadingState />}><Memory /></Suspense>;
}

function Memory() {
  const id = useSearchParams().get("id");
  const { audit } = useAudit(id, true);
  if (!id || !audit) return <Shell auditId={id || ""}><LoadingState /></Shell>;

  return <Shell auditId={id}>
    <PageHeader
      eyebrow="ClickHouse memory"
      title="Every decision keeps its proof."
      description="ClickHouse is the durable memory behind Margin. Evidence, research, gate scores, decisions, and execution receipts remain queryable after the demo ends."
      action={<Badge tone={audit.analytics.source === "clickhouse" ? "accent" : "warning"}>{audit.analytics.source} · {audit.analytics.freshness}</Badge>}
    />

    <div className="mx-auto max-w-[1120px] space-y-5 p-6 md:p-10">
      <section className="panel grid gap-px overflow-hidden bg-white/[0.06] md:grid-cols-3">
        <MemoryStat icon={Database} label="Rows query-backed" value={String(audit.analytics.row_count)} />
        <MemoryStat icon={Table2} label="MergeTree tables" value={String(audit.analytics.table_counts.length)} />
        <MemoryStat icon={CheckCircle2} label="Freshness" value={audit.analytics.freshness} />
      </section>

      <section className="panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4"><div><div className="eyebrow">Analytical memory footprint</div><div className="mt-1.5 text-[11px] text-[#aeb5be]">Rows persisted for this audit run</div></div><Badge>{audit.analytics.table_counts.reduce((sum, item) => sum + item.rows, 0)} total rows</Badge></div>
        <div className="grid gap-px bg-white/[0.055] sm:grid-cols-2 lg:grid-cols-3">
          {audit.analytics.table_counts.map((item) => <div key={item.table} className="flex items-center justify-between bg-[#111318] px-4 py-3"><span className="mono text-[9px] text-[#9da5af]">{item.table}</span><span className="metric-number text-sm font-semibold text-[#d7dbe0]">{item.rows}</span></div>)}
        </div>
      </section>

      <section className="panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4"><div><div className="eyebrow">Queries powering the product</div><div className="mt-1.5 text-[11px] text-[#aeb5be]">Open a query to inspect the exact SQL</div></div><TerminalSquare size={14} className="text-[#5eead4]" /></div>
        <div className="divide-y divide-white/[0.06]">
          {audit.analytics.query_log.map((query, index) => <details key={query.name} className="group">
            <summary className="flex cursor-pointer list-none items-center gap-4 px-5 py-4">
              <span className="mono text-[8px] text-[#5eead4]">{String(index + 1).padStart(2, "0")}</span>
              <div className="flex-1"><div className="text-[10px] font-medium text-[#bec4cb]">{query.name}</div><div className="mt-1 text-[8px] text-[#69717c]">{query.purpose}</div></div>
              <ArrowRight size={12} className="text-[#69717c] transition-transform group-open:rotate-90" />
            </summary>
            <pre className="overflow-x-auto border-t border-white/[0.055] bg-[#0b0d11] p-5 text-[9px] leading-5 text-[#84909b]"><code>{query.sql}</code></pre>
          </details>)}
        </div>
      </section>
    </div>
  </Shell>;
}

function MemoryStat({ icon: Icon, label, value }: { icon: typeof Database; label: string; value: string }) {
  return <div className="flex items-center gap-4 bg-[#111318] p-5"><div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#5eead4]/15 bg-[#5eead4]/[0.04]"><Icon size={14} className="text-[#5eead4]" /></div><div><div className="eyebrow">{label}</div><div className="metric-number mt-2 text-2xl font-semibold capitalize text-[#e2e5e9]">{value}</div></div></div>;
}
