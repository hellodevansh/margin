import { ArrowUpRight } from "lucide-react";
export function Logo({ compact = false }: { compact?: boolean }) {
  return <div className="flex items-center gap-3"><div className="flex h-8 w-8 items-center justify-center rounded-[9px] border border-white/10 bg-white/[0.04]"><ArrowUpRight size={15} strokeWidth={1.8} className="text-[#5eead4]" /></div>{!compact && <span className="text-sm font-semibold tracking-[-0.02em]">Margin</span>}</div>;
}

