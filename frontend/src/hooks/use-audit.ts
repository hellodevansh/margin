"use client";
import { useEffect, useState } from "react";
import { getAudit } from "@/lib/api";
import type { AuditSnapshot } from "@/lib/types";
export function useAudit(id?: string | null, poll = false) {
  const [audit, setAudit] = useState<AuditSnapshot | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!id) return;
    let active = true;
    const load = async () => { try { const next = await getAudit(id); if (active) setAudit(next); } catch (err) { if (active) setError(err instanceof Error ? err.message : "Could not load audit"); } };
    load();
    const timer = poll ? window.setInterval(load, 650) : undefined;
    return () => { active = false; if (timer) window.clearInterval(timer); };
  }, [id, poll]);
  return { audit, error, setAudit };
}

