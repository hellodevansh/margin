import { Check, Circle } from "lucide-react";
import { cn } from "@/lib/cn";

const stages = [
  ["01", "Detect", "Find the recoverable spend", ["ingest", "load", "leaks", "redundancy"]],
  ["02", "Verify", "Ask owners before acting", ["verification"]],
  ["03", "Research", "Prove the market case", ["research"]],
  ["04", "Gate", "Block unsafe strategies", ["strategies", "gate"]],
  ["05", "Queue", "Release only safe actions", ["actions"]],
  ["06", "Record", "Persist the complete case", ["memory", "report"]],
] as const;

export function WorkflowRibbon({ completed, current }: { completed: Set<string>; current?: string }) {
  return <div className="grid overflow-hidden rounded-xl border border-white/[0.07] bg-[#0d0f13] md:grid-cols-6">{stages.map(([number, label, note, steps]) => { const done = steps.every((step) => completed.has(step)); const active = (steps as readonly string[]).includes(current || ""); return <div key={label} className={cn("relative border-b border-white/[0.06] p-4 last:border-0 md:border-b-0 md:border-r", active && "bg-[#5eead4]/[0.035]")}><div className="flex items-center gap-2"><span className="mono text-[9px] text-[#555d68]">{number}</span>{done ? <Check size={11} className="text-[#5eead4]" /> : <Circle size={8} className={active ? "fill-[#fcd34d] text-[#fcd34d]" : "text-[#3e454f]"} />}</div><div className="mt-2 text-[11px] font-medium text-[#c5c9d0]">{label}</div><div className="mt-1 text-[8px] leading-4 text-[#5f6671]">{note}</div></div>; })}</div>;
}
