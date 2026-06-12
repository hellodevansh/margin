"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, FilePlus2, ShieldCheck, UploadCloud, X } from "lucide-react";
import { motion } from "motion/react";
import { createAudit, getDataRoomPreview, getHealth } from "@/lib/api";
import { Logo } from "@/components/logo";
import { IntegrationStrip } from "@/components/integration-strip";
import { Badge } from "@/components/badge";
import type { DataRoomPreview, Integration } from "@/lib/types";

const fallback: Integration[] = ["Langfuse", "ClickHouse", "Composio", "Anthropic"].map((name) => ({ name, state: "degraded", detail: "Checking connection" }));
const flow = ["Detect", "Verify", "Research", "Gate", "Decide", "Recover"];

export default function Home() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [integrations, setIntegrations] = useState(fallback);
  const [preview, setPreview] = useState<DataRoomPreview | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [running, setRunning] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getHealth().then((data) => setIntegrations(data.integrations)).catch(() => setError("Start the local backend on port 8000 to run an audit."));
    getDataRoomPreview().then(setPreview).catch(() => undefined);
  }, []);

  function addFiles(next: FileList | File[]) {
    setFiles((current) => {
      const byName = new Map(current.map((file) => [file.name.toLowerCase(), file]));
      Array.from(next).filter((file) => file.size <= 5_000_000).forEach((file) => byName.set(file.name.toLowerCase(), file));
      return Array.from(byName.values()).slice(0, 10);
    });
    setError("");
  }

  async function runAudit() {
    if (missingRequired.length) {
      setError(`Upload all required documents before starting. ${missingRequired.length} remaining.`);
      return;
    }
    setRunning(true); setError("");
    try { const audit = await createAudit(files); router.push(`/audit/${audit.audit_id}`); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not start audit"); setRunning(false); }
  }

  const requiredFiles = preview?.required_files || [];
  const selectedNames = new Set(files.map((file) => file.name.toLowerCase()));
  const missingRequired = requiredFiles.filter((filename) => !selectedNames.has(filename.toLowerCase()));
  const ready = requiredFiles.length > 0 && missingRequired.length === 0;

  return <main className="relative min-h-screen overflow-hidden bg-[#08090B]">
    <div className="grid-lines pointer-events-none absolute inset-0" />
    <header className="relative z-10 flex h-16 items-center justify-between border-b border-white/[0.06] px-6 md:px-10"><Logo /><div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.1em] text-[#656c77]"><ShieldCheck size={12} className="text-[#5eead4]" /> Every action must earn approval</div></header>
    <section className="relative z-10 mx-auto grid max-w-[1320px] gap-10 px-6 py-10 lg:grid-cols-[.9fr_1.1fr] lg:px-10 lg:py-16">
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col justify-between">
        <div>
          <Badge tone="accent">Autonomous spend recovery</Badge>
          <h1 className="mt-7 max-w-[650px] text-[48px] font-semibold leading-[1.01] tracking-[-0.062em] text-[#f5f6f7] md:text-[66px]">Stop paying for software nobody can defend.</h1>
          <p className="mt-6 max-w-lg text-sm leading-7 text-[#858c97]">Margin turns contracts, usage, invoices, and live market data into recovery actions you can approve with confidence.</p>
        </div>
        <div className="mt-12 flex flex-wrap items-center gap-2">{flow.map((step, index) => <div key={step} className="flex items-center gap-2"><span className="rounded-full border border-white/[0.08] bg-white/[0.025] px-3 py-2 text-[9px] text-[#9ca3ad]"><span className="mono mr-2 text-[#5eead4]">{String(index + 1).padStart(2, "0")}</span>{step}</span>{index < flow.length - 1 && <ArrowRight size={9} className="text-[#4f5661]" />}</div>)}</div>
      </motion.div>
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .08 }} className="panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4"><div><div className="eyebrow">Start with your evidence</div><div className="mt-1.5 text-sm font-medium">Upload the complete AcmeAI data room</div></div>{ready && <Badge tone="accent">Ready to audit</Badge>}</div>
        <div className="p-5">
          <button onClick={() => inputRef.current?.click()} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); addFiles(event.dataTransfer.files); }} className={`flex min-h-[190px] w-full flex-col items-center justify-center rounded-xl border border-dashed px-5 text-center transition-colors ${dragging ? "border-[#5eead4]/45 bg-[#5eead4]/[0.04]" : "border-white/[0.12] bg-black/10 hover:border-white/[0.2] hover:bg-white/[0.018]"}`}><UploadCloud size={20} className={ready ? "text-[#5eead4]" : "text-[#747c87]"} /><div className="mt-3 text-[11px] font-medium text-[#b4bac3]">{files.length ? "Add or replace documents" : "Select all evidence documents"}</div><div className="mt-1.5 text-[8px] leading-4 text-[#565e69]">Nothing is prefilled · select the seven required files together<br />CSV and JSON · up to 5 MB each</div></button>
          <input ref={inputRef} type="file" multiple accept=".csv,.json,.pdf,.docx,.txt,.md" className="hidden" onChange={(event) => event.target.files && addFiles(event.target.files)} />
          <div className="mt-4 grid gap-2 sm:grid-cols-2">{requiredFiles.map((filename) => {
            const uploaded = selectedNames.has(filename.toLowerCase());
            return <div key={filename} className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 ${uploaded ? "border-[#5eead4]/15 bg-[#5eead4]/[0.025]" : "border-white/[0.06]"}`}><div className={`flex h-5 w-5 items-center justify-center rounded-md border ${uploaded ? "border-[#5eead4]/20 text-[#5eead4]" : "border-white/[0.08] text-[#505863]"}`}>{uploaded ? <Check size={10} /> : <FilePlus2 size={9} />}</div><span className={`min-w-0 flex-1 truncate text-[8px] ${uploaded ? "text-[#aeb6bf]" : "text-[#626b76]"}`}>{filename}</span>{uploaded && <button onClick={() => setFiles((current) => current.filter((file) => file.name.toLowerCase() !== filename.toLowerCase()))} aria-label={`Remove ${filename}`}><X size={9} className="text-[#5f6671] hover:text-white" /></button>}</div>;
          })}</div>
          <button onClick={runAudit} disabled={running || !ready} className="group mt-5 flex h-12 w-full items-center justify-between rounded-xl border border-[#5eead4]/20 bg-[#5eead4] px-4 text-xs font-semibold text-[#07110f] shadow-[0_12px_40px_rgba(94,234,212,0.12)] transition-all hover:bg-[#83f1e0] disabled:cursor-not-allowed disabled:border-white/[0.07] disabled:bg-white/[0.04] disabled:text-[#68717c] disabled:shadow-none"><span>{running ? "Building the recovery case" : ready ? "Audit uploaded evidence" : requiredFiles.length ? `Upload ${missingRequired.length} more document${missingRequired.length === 1 ? "" : "s"}` : "Loading requirements"}</span><ArrowRight size={14} className="transition-transform group-hover:translate-x-0.5" /></button>
          {error && <p className="mt-3 text-[9px] text-[#fca5a5]">{error}</p>}
        </div>
      </motion.div>
    </section>
    <footer className="relative z-10 flex flex-col gap-4 border-t border-white/[0.06] px-6 py-4 md:flex-row md:items-center md:justify-between md:px-10"><IntegrationStrip integrations={integrations} /><div className="text-[9px] uppercase tracking-[0.12em] text-[#4f5661]">Local deterministic demo · live integrations</div></footer>
  </main>;
}
