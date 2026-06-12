import { cn } from "@/lib/cn";
export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "accent" | "warning" | "danger" }) {
  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.1em]", tone === "neutral" && "border-white/10 bg-white/[0.03] text-[#9ca3af]", tone === "accent" && "border-[#5eead4]/20 bg-[#5eead4]/[0.06] text-[#8af3e3]", tone === "warning" && "border-[#fcd34d]/20 bg-[#fcd34d]/[0.05] text-[#fcd34d]", tone === "danger" && "border-[#fca5a5]/20 bg-[#fca5a5]/[0.05] text-[#fca5a5]")}>{children}</span>;
}

