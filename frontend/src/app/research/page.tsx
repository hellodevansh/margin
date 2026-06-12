"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ExternalLink, List, Search } from "lucide-react";
import { Shell } from "@/components/shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/badge";
import { LoadingState } from "@/components/loading";
import { BrowserResearchPanel, SourceLedger } from "@/components/browser-research-panel";
import { useAudit } from "@/hooks/use-audit";

export default function ResearchPage() {
  return <Suspense fallback={<LoadingState />}><Research /></Suspense>;
}

function Research() {
  const id = useSearchParams().get("id");
  const { audit } = useAudit(id);
  if (!id || !audit) return <Shell auditId={id || ""}><LoadingState /></Shell>;

  return <Shell auditId={id}>
    <PageHeader
      eyebrow="Web research"
      title="See the market case being built."
      description="Margin does not hide its research. Watch it inspect official pricing, test alternatives, and attach every claim to a source before the gate scores an action."
      action={<Badge tone="accent">{audit.research_activity.length} observable operations</Badge>}
    />
    <div className="mx-auto max-w-[1280px] space-y-5 p-6 md:p-10">
      <BrowserResearchPanel activities={audit.research_activity} findings={audit.research} />

      <div className="grid gap-5 xl:grid-cols-2">
        <details className="panel group overflow-hidden">
          <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4">
            <div className="flex items-center gap-3"><ExternalLink size={13} className="text-[#5eead4]" /><div><div className="text-[11px] font-medium text-[#c4cad1]">Verified source ledger</div><div className="mt-1 text-[8px] text-[#626b76]">{audit.research.length} official pricing and competitor pages</div></div></div>
            <Badge>{audit.research.length} sources</Badge>
          </summary>
          <div className="border-t border-white/[0.07]"><SourceLedger findings={audit.research} /></div>
        </details>

        <details className="panel group overflow-hidden">
          <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4">
            <div className="flex items-center gap-3"><List size={13} className="text-[#5eead4]" /><div><div className="text-[11px] font-medium text-[#c4cad1]">Complete operation ledger</div><div className="mt-1 text-[8px] text-[#626b76]">Open to inspect every browser action in order</div></div></div>
            <Badge>{audit.research_activity.length} operations</Badge>
          </summary>
          <div className="max-h-[520px] divide-y divide-white/[0.055] overflow-y-auto border-t border-white/[0.07]">
            {audit.research_activity.map((activity, index) => <div key={activity.id} className="flex items-center gap-4 px-5 py-3">
              <span className="mono shrink-0 text-[8px] text-[#59616c]">{String(index + 1).padStart(2, "0")}</span>
              <Search size={10} className="shrink-0 text-[#5eead4]" />
              <div className="min-w-0 flex-1"><div className="truncate text-[9px] font-medium text-[#b9c0c8]">{activity.label}</div><div className="mono mt-1 truncate text-[7px] text-[#5d6570]">{activity.url || activity.query || activity.detail}</div></div>
              <span className="mono text-[7px] uppercase text-[#6f7782]">{activity.kind}</span>
            </div>)}
          </div>
        </details>
      </div>
    </div>
  </Shell>;
}
