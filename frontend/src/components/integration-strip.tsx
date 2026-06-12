import type { Integration } from "@/lib/types";
export function IntegrationStrip({ integrations }: { integrations: Integration[] }) {
  return <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2">{integrations.map((item) => <div key={item.name} className="flex items-center gap-2 text-[11px] text-[#858b96]" title={item.detail}><span className={`status-dot ${item.state}`} /><span>{item.name}</span></div>)}</div>;
}

