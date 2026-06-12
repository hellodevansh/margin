"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Download, ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Shell } from "@/components/shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/badge";
import { LoadingState } from "@/components/loading";
import { useAudit } from "@/hooks/use-audit";
import { API_URL } from "@/lib/api";

export default function ReportPage() {
  return <Suspense fallback={<LoadingState />}><Report /></Suspense>;
}

function Report() {
  const id = useSearchParams().get("id");
  const { audit } = useAudit(id);
  if (!id || !audit) return <Shell auditId={id || ""}><LoadingState /></Shell>;

  return <Shell auditId={id}>
    <PageHeader
      eyebrow="Cited recovery report"
      title="The recovery case, ready for scrutiny."
      description="One export connects every finding to its source, every action to its Langfuse gate result, and every approval to its execution receipt."
      action={<a href={`${API_URL}/api/audits/${id}/report`} className="flex items-center gap-2 rounded-lg border border-white/10 px-4 py-2.5 text-xs text-[#b7bbc4] hover:bg-white/[0.03]"><Download size={13} /> Export cited.md</a>}
    />
    <div className="grid gap-6 p-6 md:p-10 xl:grid-cols-[1fr_280px]">
      <article className="panel overflow-x-auto p-7 md:p-10">
        <div className="max-w-none text-sm leading-7 text-[#969ca6] [&_a]:text-[#8af3e3] [&_h1]:mb-6 [&_h1]:text-3xl [&_h1]:font-semibold [&_h1]:tracking-[-0.04em] [&_h2]:mb-4 [&_h2]:mt-10 [&_h2]:border-b [&_h2]:border-white/[0.07] [&_h2]:pb-3 [&_h2]:text-lg [&_h2]:font-medium [&_li]:ml-5 [&_li]:list-disc [&_strong]:text-[#e8eaed] [&_table]:w-full [&_table]:min-w-[680px] [&_table]:text-xs [&_td]:border-b [&_td]:border-white/[0.06] [&_td]:px-2 [&_td]:py-3 [&_th]:border-b [&_th]:border-white/[0.1] [&_th]:px-2 [&_th]:py-3 [&_th]:text-left">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{audit.report_markdown}</ReactMarkdown>
        </div>
      </article>
      <aside className="space-y-4">
        <section className="panel p-5">
          <div className="eyebrow">Source integrity</div>
          <div className="mt-5 space-y-4">{audit.research.map((source) => <a key={source.vendor} href={source.source_url} target="_blank" className="block rounded-xl border border-white/[0.07] p-3 hover:bg-white/[0.025]"><div className="flex items-center justify-between"><span className="text-xs font-medium">{source.vendor}</span><ExternalLink size={11} className="text-[#626975]" /></div><div className="mt-2"><Badge tone={source.source_status === "live" ? "accent" : "warning"}>{source.source_status}</Badge></div></a>)}</div>
        </section>
        <section className="panel p-5">
          <div className="eyebrow">Audit controls</div>
          <div className="mt-4 space-y-3 text-[11px] text-[#7c838e]"><div className="flex justify-between"><span>Trace ID</span><span className="mono max-w-[120px] truncate">{audit.trace_id || "local"}</span></div><div className="flex justify-between"><span>Policy</span><span>Strict</span></div><div className="flex justify-between"><span>Status</span><span className="text-[#5eead4]">Complete</span></div></div>
        </section>
      </aside>
    </div>
  </Shell>;
}
