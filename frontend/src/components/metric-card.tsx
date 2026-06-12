"use client";
import { motion } from "motion/react";
export function MetricCard({ label, value, note, accent = false }: { label: string; value: string; note: string; accent?: boolean }) {
  return <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="panel min-h-[166px] p-5"><div className="eyebrow">{label}</div><div className={`metric-number mt-7 text-[34px] font-semibold ${accent ? "text-[#8af3e3]" : "text-[#f3f4f6]"}`}>{value}</div><div className="mt-4 flex items-center gap-2 text-[11px] text-[#707680]"><span className={`h-1.5 w-1.5 rounded-full ${accent ? "bg-[#5eead4]" : "bg-white/25"}`} />{note}</div></motion.div>;
}

