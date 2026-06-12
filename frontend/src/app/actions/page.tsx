"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertCircle,
  ArrowRight,
  Check,
  CheckCircle2,
  Clock3,
  Mail,
  MessageSquare,
  Pause,
  RefreshCw,
  ShieldCheck,
  X,
} from "lucide-react";
import { Shell } from "@/components/shell";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/badge";
import { LoadingState } from "@/components/loading";
import { useAudit } from "@/hooks/use-audit";
import { decideTask, money, syncTaskVerification } from "@/lib/api";
import type { RecoveryTask, Strategy } from "@/lib/types";

type Decision = "approve" | "hold" | "reject";

export default function ActionsPage() {
  return <Suspense fallback={<LoadingState />}><Actions /></Suspense>;
}

function Actions() {
  const id = useSearchParams().get("id");
  const { audit } = useAudit(id, true);
  const [note, setNote] = useState("");
  const [processing, setProcessing] = useState(false);
  const [syncingVerification, setSyncingVerification] = useState(false);
  const [message, setMessage] = useState<{ text: string; error?: boolean } | null>(null);

  const awaitingTask = audit?.recovery_tasks.find((task) => task.status === "awaiting_verification");
  const awaitingTaskId = awaitingTask?.id;

  const checkVerification = useCallback(async (taskId: string) => {
    if (!id) return;
    setSyncingVerification(true);
    try {
      const result = await syncTaskVerification(id, taskId);
      if (result.task.status === "pending_approval") {
        setMessage({ text: "Slack replied RECLAIM. Resource verification is recorded and the final Margin decision is now unlocked." });
      } else if (result.task.status === "closed_no_action") {
        setMessage({ text: "Slack replied KEEP. Figma was retained and no external action was launched." });
      } else if (result.task.verification?.status === "unrecognized") {
        setMessage({ text: "Slack replied, but Margin is still waiting for RECLAIM or KEEP.", error: true });
      } else if (result.task.verification?.status === "error") {
        setMessage({ text: result.task.verification.error_detail || "Could not check Slack verification", error: true });
      }
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Could not check Slack verification", error: true });
    } finally {
      setSyncingVerification(false);
    }
  }, [id]);

  useEffect(() => {
    if (!awaitingTaskId) return;
    const immediate = window.setTimeout(() => void checkVerification(awaitingTaskId), 0);
    const timer = window.setInterval(() => void checkVerification(awaitingTaskId), 2_000);
    return () => { window.clearTimeout(immediate); window.clearInterval(timer); };
  }, [awaitingTaskId, checkVerification]);

  if (!id || !audit) return <Shell auditId={id || ""}><LoadingState /></Shell>;

  const currentTask = audit.recovery_tasks.find((task) => task.status === "awaiting_verification" || task.status === "pending_approval" || task.status === "held");
  const blockedAlternative = currentTask ? audit.strategies.find((strategy) => strategy.vendor === currentTask.vendor && !strategy.approved) : undefined;
  const completedTasks = audit.recovery_tasks.filter((task) => !["awaiting_verification", "pending_approval", "held"].includes(task.status));
  const decided = completedTasks.length;

  const decide = async (task: RecoveryTask, decision: Decision) => {
    setProcessing(true);
    setMessage(null);
    try {
      const result = await decideTask(id, task.id, decision, note);
      const external = result.receipts.length ? "Vendor draft created and retained as the execution record." : "No external action was launched.";
      setMessage({ text: `${decisionLabel(decision)} recorded. ${external}` });
      setNote("");
    } catch (error) {
      setMessage({ text: error instanceof Error ? error.message : "Could not process decision", error: true });
    } finally {
      setProcessing(false);
    }
  };

  return <Shell auditId={id}>
    <PageHeader
      eyebrow="Project-head queue"
      title="Approve only what survived the gate."
      description="Every action here has passed the Langfuse-audited safety policy. Review the released action, record your decision, then move to the next."
      action={<Badge tone={decided === audit.recovery_tasks.length ? "accent" : "warning"}>{decided} of {audit.recovery_tasks.length} decided</Badge>}
    />

    <div className="mx-auto max-w-[1120px] space-y-6 p-6 md:p-10">
      <QueueProgress tasks={audit.recovery_tasks} />

      {currentTask
        ? currentTask.status === "awaiting_verification"
          ? <VerificationDecision
              task={currentTask}
              position={audit.recovery_tasks.findIndex((task) => task.id === currentTask.id) + 1}
              total={audit.recovery_tasks.length}
              syncing={syncingVerification}
              message={message}
              onRetry={() => void checkVerification(currentTask.id)}
            />
          : <FocusedDecision
            task={currentTask}
            blockedAlternative={blockedAlternative}
            position={audit.recovery_tasks.findIndex((task) => task.id === currentTask.id) + 1}
            total={audit.recovery_tasks.length}
            note={note}
            setNote={setNote}
            processing={processing}
            message={message}
            onDecision={(decision) => decide(currentTask, decision)}
            />
        : <section className="panel px-6 py-16 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-[#5eead4]/20 bg-[#5eead4]/[0.05]">
              <CheckCircle2 size={19} className="text-[#5eead4]" />
            </div>
            <h2 className="mt-5 text-2xl font-medium tracking-[-0.035em]">Decision queue complete</h2>
            <p className="mx-auto mt-2 max-w-lg text-xs leading-6 text-[#777f89]">Every recovery action has been recorded. Approved actions created vendor-facing drafts; rejected actions launched nothing.</p>
          </section>}

      {completedTasks.length > 0 && <DecisionHistory tasks={completedTasks} actions={audit.actions} />}
    </div>
  </Shell>;
}

function QueueProgress({ tasks }: { tasks: RecoveryTask[] }) {
  const lastCompleted = [...tasks].reverse().find((task) => task.status === "executed" || task.status === "closed_no_action");
  return <section className="panel flex flex-col gap-4 px-5 py-4 md:flex-row md:items-center md:justify-between">
    <div className="flex items-center gap-3">
      <ShieldCheck size={14} className="text-[#5eead4]" />
      <div>
        <div className="text-[11px] font-medium text-[#cbd0d6]">Only gate-released actions reach you</div>
        <div className="mt-1 text-[9px] text-[#68717c]">{lastCompleted ? `Last recorded: ${lastCompleted.vendor} · ${lastCompleted.status.replaceAll("_", " ")}` : "Live evidence can hold an item before the final Margin decision."}</div>
      </div>
    </div>
    <div className="flex items-center gap-2">
      {tasks.map((task, index) => <div key={task.id} className="flex items-center gap-2">
        <span className={`flex h-7 w-7 items-center justify-center rounded-full border text-[9px] font-semibold ${task.status === "executed" || task.status === "closed_no_action" ? "border-[#5eead4]/25 bg-[#5eead4]/[0.08] text-[#8af3e3]" : task.status === "awaiting_verification" ? "border-[#fcd34d]/20 bg-[#fcd34d]/[0.04] text-[#fcd34d]" : task.status === "pending_approval" || task.status === "held" ? "border-white/[0.13] bg-white/[0.04] text-[#c3c9d0]" : "border-white/[0.07] text-[#606974]"}`}>
          {task.status === "executed" || task.status === "closed_no_action" ? <Check size={11} /> : task.status === "awaiting_verification" ? <MessageSquare size={10} /> : index + 1}
        </span>
        {index < tasks.length - 1 && <span className="h-px w-5 bg-white/[0.08]" />}
      </div>)}
    </div>
  </section>;
}

function VerificationDecision({ task, position, total, syncing, message, onRetry }: {
  task: RecoveryTask;
  position: number;
  total: number;
  syncing: boolean;
  message: { text: string; error?: boolean } | null;
  onRetry: () => void;
}) {
  const verification = task.verification;
  const hasError = verification?.status === "error";
  const unrecognized = verification?.status === "unrecognized";
  return <section className="panel overflow-hidden border-[#fcd34d]/15">
    <div className="grid lg:grid-cols-[1.08fr_.92fr]">
      <div className="border-b border-white/[0.07] p-6 lg:border-b-0 lg:border-r">
        <div className="flex flex-wrap items-center gap-2"><Badge tone="warning">Live Slack gate</Badge><Badge>Decision {position} of {total}</Badge><Badge>{task.vendor}</Badge></div>
        <h2 className="mt-5 text-3xl font-medium tracking-[-0.045em]">Waiting for your Slack confirmation</h2>
        <p className="mt-3 max-w-xl text-xs leading-6 text-[#7f8791]">Margin found an unused Figma workspace, but it will not expose the final recovery decision until a resource owner confirms whether it is still needed.</p>

        <div className="mt-6 grid gap-px overflow-hidden rounded-xl border border-white/[0.07] bg-white/[0.06] sm:grid-cols-3">
          <VerificationFact label="Resource" value="Figma Professional" />
          <VerificationFact label="90-day usage" value="0 active days" />
          <VerificationFact label="Annual cost" value={money(task.savings)} accent />
        </div>

        <div className="mt-6">
          <div className="eyebrow">Message posted to Slack</div>
          <pre className="mt-3 max-h-[280px] overflow-y-auto whitespace-pre-wrap rounded-xl border border-white/[0.07] bg-[#0b0d11] p-4 font-sans text-[10px] leading-5 text-[#858d97]">{verification?.prompt || "Preparing Slack verification request"}</pre>
        </div>
      </div>

      <div className="flex flex-col bg-[#0e1014] p-6">
        <div className="flex items-center justify-between"><div><div className="eyebrow">Live confirmation status</div><div className="mt-2 text-sm font-medium">{hasError ? "Slack check needs attention" : unrecognized ? "Reply not recognized" : "Listening for your reply"}</div></div><MessageSquare size={16} className="text-[#fcd34d]" /></div>

        <div className="mt-6 space-y-4">
          <VerificationStatus label="Prompt posted" value={verification?.thread_ts ? "Live Slack thread created" : "Posting request"} complete={Boolean(verification?.thread_ts)} />
          <VerificationStatus label="Thread receipt" value={verification?.thread_ts || verification?.posted_receipt_id || "Waiting for receipt"} complete={Boolean(verification?.thread_ts)} mono />
          <VerificationStatus label="Reply monitor" value={syncing ? "Checking Slack now" : "Checking Slack every 2 seconds"} complete={false} working />
          <VerificationStatus label="Owner response" value={verification?.response_text || "No response received yet"} complete={Boolean(verification?.interpretation)} />
        </div>

        <div className="mt-7 grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-[#5eead4]/15 bg-[#5eead4]/[0.025] p-4"><div className="mono text-[11px] font-semibold text-[#8af3e3]">RECLAIM</div><div className="mt-2 text-[8px] leading-4 text-[#68717c]">Unlocks the final decision inside Margin.</div></div>
          <div className="rounded-xl border border-white/[0.07] p-4"><div className="mono text-[11px] font-semibold text-[#bdc3ca]">KEEP</div><div className="mt-2 text-[8px] leading-4 text-[#68717c]">Closes the item with no vendor action.</div></div>
        </div>

        {(hasError || unrecognized) && <div className="mt-5 rounded-xl border border-[#fca5a5]/15 bg-[#fca5a5]/[0.025] p-4"><div className="text-[10px] font-medium text-[#e3b9b9]">{hasError ? verification?.error_detail : `Received: ${verification?.response_text}`}</div><p className="mt-2 text-[8px] leading-4 text-[#7f7377]">{hasError ? "Margin will continue retrying automatically." : "Reply again in the same thread with exactly RECLAIM or KEEP."}</p>{hasError && <button onClick={onRetry} disabled={syncing} className="mt-3 flex items-center gap-2 rounded-lg border border-white/[0.09] px-3 py-2 text-[9px] text-[#b9c0c8] hover:bg-white/[0.03] disabled:opacity-50"><RefreshCw size={10} className={syncing ? "animate-spin" : ""} /> Retry Slack check</button>}</div>}
        {message && !hasError && !unrecognized && <div className={`mt-5 rounded-xl border p-4 text-[9px] leading-5 ${message.error ? "border-[#fca5a5]/15 text-[#fca5a5]" : "border-[#5eead4]/15 text-[#8af3e3]"}`}>{message.text}</div>}
      </div>
    </div>
  </section>;
}

function VerificationFact({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return <div className="bg-[#111318] p-4"><div className="eyebrow">{label}</div><div className={`mt-3 text-[11px] font-medium ${accent ? "text-[#8af3e3]" : "text-[#c0c6cd]"}`}>{value}</div></div>;
}

function VerificationStatus({ label, value, complete, working = false, mono = false }: { label: string; value: string; complete: boolean; working?: boolean; mono?: boolean }) {
  return <div className="flex items-start gap-3 border-b border-white/[0.06] pb-4 last:border-0"><div className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${complete ? "border-[#5eead4]/20 text-[#5eead4]" : working ? "border-[#fcd34d]/20 text-[#fcd34d]" : "border-white/[0.08] text-[#5f6772]"}`}>{complete ? <Check size={10} /> : working ? <RefreshCw size={9} className="animate-spin" /> : <Clock3 size={9} />}</div><div className="min-w-0"><div className="eyebrow">{label}</div><div className={`mt-1.5 truncate text-[9px] text-[#9ca4ae] ${mono ? "mono" : ""}`}>{value}</div></div></div>;
}

function FocusedDecision({ task, blockedAlternative, position, total, note, setNote, processing, message, onDecision }: {
  task: RecoveryTask;
  blockedAlternative?: Strategy;
  position: number;
  total: number;
  note: string;
  setNote: (note: string) => void;
  processing: boolean;
  message: { text: string; error?: boolean } | null;
  onDecision: (decision: Decision) => void;
}) {
  return <section className="panel overflow-hidden border-white/[0.1]">
    <div className="flex flex-col gap-5 border-b border-white/[0.07] px-6 py-6 md:flex-row md:items-start md:justify-between">
      <div>
        <div className="flex flex-wrap items-center gap-2"><Badge tone="accent">Released by Langfuse</Badge>{task.verification?.status === "confirmed_reclaim" && <Badge tone="accent">Slack confirmed</Badge>}<Badge>{task.gate_action_safety.toFixed(2)} safety</Badge><Badge>{task.gate_confidence.toFixed(2)} confidence</Badge><Badge>Decision {position} of {total}</Badge><Badge>{task.vendor}</Badge></div>
        <h2 className="mt-5 max-w-2xl text-3xl font-medium tracking-[-0.045em]">{task.title}</h2>
        <p className="mt-3 max-w-2xl text-xs leading-6 text-[#7f8791]">{task.rationale}</p>
      </div>
      <div className="shrink-0 md:text-right">
        <div className="metric-number text-4xl font-semibold text-[#8af3e3]">{money(task.savings)}</div>
        <div className="mt-1.5 text-[9px] uppercase tracking-[0.12em] text-[#606873]">annual recovery</div>
      </div>
    </div>

    <div className="grid lg:grid-cols-[.72fr_1.28fr]">
      <div className="border-b border-white/[0.07] p-6 lg:border-b-0 lg:border-r">
        <div className="eyebrow">Decision brief</div>
        <div className="mt-5 space-y-5">
          <BriefRow label="Recommended action" value={task.action} />
          <BriefRow label="Evidence" value={`${task.evidence_refs.length} verified records`} />
          <BriefRow label="Urgency" value={task.urgency.replaceAll("_", " ")} />
          <BriefRow label="Langfuse strategy" value={task.strategy_id} />
          <BriefRow label="Gate result" value={`Passed · ${task.gate_action_safety.toFixed(2)} safety · ${task.gate_confidence.toFixed(2)} confidence`} accent />
        </div>
        {blockedAlternative ? <div className="mt-7 rounded-xl border border-[#fca5a5]/15 bg-[#fca5a5]/[0.025] p-4"><div className="flex items-center gap-2 text-[10px] font-medium text-[#d1b5b5]"><X size={12} className="text-[#fca5a5]" /> Unsafe alternative blocked</div><p className="mt-2 text-[9px] leading-5 text-[#7f7377]">{blockedAlternative.title} never reached you because action safety scored {blockedAlternative.scores.action_safety.toFixed(2)}.</p></div> : <div className="mt-7 rounded-xl border border-white/[0.07] bg-white/[0.018] p-4"><div className="flex items-center gap-2 text-[10px] font-medium text-[#b8bec6]"><MessageSquare size={12} className="text-[#5eead4]" /> Evidence before execution</div><p className="mt-2 text-[9px] leading-5 text-[#68717c]">The action is grounded in internal evidence and live market research. The final decision remains yours.</p></div>}
      </div>

      <div className="p-6">
        <div className="flex items-center justify-between">
          <div><div className="eyebrow">Draft created on approval</div><div className="mt-2 text-sm font-medium">Actionable vendor email</div></div>
          <Mail size={15} className="text-[#5eead4]" />
        </div>
        <div className="mt-5 grid gap-3 rounded-xl border border-white/[0.07] bg-[#0d0f13] p-4 text-[10px]">
          <div className="grid grid-cols-[56px_1fr] gap-3"><span className="text-[#626b76]">To</span><span className="mono text-[#c2c8cf]">{task.draft_to}</span></div>
          <div className="grid grid-cols-[56px_1fr] gap-3"><span className="text-[#626b76]">Subject</span><span className="text-[#c2c8cf]">{task.draft_subject}</span></div>
        </div>
        <pre className="mt-4 max-h-[260px] overflow-y-auto whitespace-pre-wrap rounded-xl border border-white/[0.07] bg-[#0b0d11] p-4 font-sans text-[10px] leading-5 text-[#858d97]">{task.draft_body}</pre>
      </div>
    </div>

    <div className="border-t border-white/[0.07] bg-[#0e1014] p-5">
      <label className="eyebrow" htmlFor={`note-${task.id}`}>Optional decision note</label>
      <input id={`note-${task.id}`} value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add context to the execution record" className="mt-2 w-full rounded-lg border border-white/[0.08] bg-black/20 px-3 py-2.5 text-[11px] text-[#d3d7dd] outline-none placeholder:text-[#515863] focus:border-[#5eead4]/30" />
      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <button disabled={processing} onClick={() => onDecision("approve")} className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-[#5eead4] px-4 py-3 text-[11px] font-semibold text-[#07110f] hover:bg-[#83f1e0] disabled:opacity-50"><Check size={13} /> Approve and create draft <ArrowRight size={12} /></button>
        <button disabled={processing} onClick={() => onDecision("hold")} className="flex items-center justify-center gap-2 rounded-lg border border-white/[0.09] px-5 py-3 text-[11px] font-medium text-[#aeb4bd] hover:bg-white/[0.03] disabled:opacity-50"><Pause size={12} /> Hold</button>
        <button disabled={processing} onClick={() => onDecision("reject")} className="flex items-center justify-center gap-2 rounded-lg border border-white/[0.09] px-5 py-3 text-[11px] font-medium text-[#aeb4bd] hover:border-[#fca5a5]/20 hover:text-[#fca5a5] disabled:opacity-50"><X size={12} /> Reject</button>
      </div>
      {message && <div className={`mt-3 flex items-start gap-2 rounded-lg border p-3 text-[10px] leading-4 ${message.error ? "border-[#fca5a5]/20 text-[#fca5a5]" : "border-[#5eead4]/20 text-[#8af3e3]"}`}>{message.error ? <AlertCircle size={12} /> : <CheckCircle2 size={12} />}<span>{message.text}</span></div>}
    </div>
  </section>;
}

function BriefRow({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return <div className="border-b border-white/[0.06] pb-4 last:border-0 last:pb-0"><div className="eyebrow">{label}</div><div className={`mt-2 text-[11px] leading-5 ${accent ? "text-[#8af3e3]" : "text-[#b6bdc6]"}`}>{value}</div></div>;
}

function DecisionHistory({ tasks, actions }: { tasks: RecoveryTask[]; actions: Array<{ id: string; title: string; status: string; tool: string; detail: string }> }) {
  return <details className="panel group overflow-hidden">
    <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4">
      <div><div className="eyebrow">Decision history</div><div className="mt-1.5 text-[11px] text-[#aeb5be]">{tasks.length} recorded decision{tasks.length === 1 ? "" : "s"} · {actions.length} external receipt{actions.length === 1 ? "" : "s"}</div></div>
      <Clock3 size={14} className="text-[#69717c] transition-transform group-open:rotate-90" />
    </summary>
    <div className="divide-y divide-white/[0.06] border-t border-white/[0.07]">
      {tasks.map((task) => <div key={task.id} className="flex flex-col gap-3 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div><div className="flex items-center gap-2"><span className="text-[11px] font-medium text-[#c6cbd2]">{task.vendor}</span><TaskStatus status={task.status} /></div><div className="mt-1.5 text-[9px] text-[#69717c]">{task.draft_subject}</div></div>
        <div className="metric-number text-sm font-semibold text-[#8af3e3]">{money(task.savings)}</div>
      </div>)}
      {actions.map((action) => <div key={action.id} className="flex items-center justify-between gap-4 px-5 py-4"><div className="flex items-center gap-3">{action.tool.includes("OUTLOOK") ? <Mail size={12} className="text-[#5eead4]" /> : <MessageSquare size={12} className="text-[#5eead4]" />}<div><div className="text-[10px] font-medium text-[#b9c0c8]">{action.title}</div><div className="mt-1 text-[8px] text-[#626b76]">{action.detail}</div></div></div><Badge tone={action.status === "executed" ? "accent" : "warning"}>{action.status}</Badge></div>)}
    </div>
  </details>;
}

function TaskStatus({ status }: { status: RecoveryTask["status"] }) {
  const tone = status === "executed" || status === "closed_no_action" ? "accent" : status === "failed" || status === "rejected" ? "danger" : status === "held" || status === "awaiting_verification" ? "warning" : "neutral";
  return <Badge tone={tone}>{status.replaceAll("_", " ")}</Badge>;
}

function decisionLabel(decision: Decision) {
  return decision.charAt(0).toUpperCase() + decision.slice(1);
}
