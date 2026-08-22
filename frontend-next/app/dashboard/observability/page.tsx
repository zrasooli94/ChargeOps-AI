"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { AgentRun } from "@/lib/types";
import { useDashboard } from "@/components/dashboard/dashboard-context";

export default function ObservabilityPage() {
  const { station, user } = useDashboard();
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const allowed = user?.role === "operator" || user?.role === "admin";

  useEffect(() => {
    if (!station || !allowed) return;
    api.runs(station.station_id).then((data) => { setRuns(data); setSelectedId(data[0]?.id ?? ""); }).catch((e) => setError(e.message));
  }, [station?.station_id, allowed]);

  const stats = useMemo(() => {
    const completed = runs.filter((r) => r.status === "completed").length;
    const avg = runs.length ? runs.reduce((sum, r) => sum + r.latency_ms, 0) / runs.length : 0;
    const tools = runs.reduce((sum, r) => sum + (r.used_tools?.length ?? 0), 0);
    const protectedRuns = runs.filter((r) => r.approval_required).length;
    return { completed, avg, tools, protectedRuns };
  }, [runs]);
  const selected = runs.find((r) => r.id === selectedId) ?? null;

  if (!allowed) return <div className="locked-page"><span>◎</span><h1>Observability is protected.</h1><p>Operator or administrator access is required.</p></div>;

  return <div className="page-stack">
    <section className="page-hero compact"><div><div className="eyebrow">◎ PRODUCTION TELEMETRY</div><h1>Every agent decision, inspectable.</h1><p>Persistent execution telemetry across latency, tools, approvals, answers and traces.</p></div></section>
    {error && <div className="form-error">{error}</div>}
    <section className="metric-grid four"><article><span>Runs</span><strong>{runs.length}</strong></article><article><span>Completed</span><strong>{stats.completed}</strong></article><article><span>Avg latency</span><strong>{stats.avg.toFixed(0)} ms</strong></article><article><span>Tool calls</span><strong>{stats.tools}</strong></article></section>
    <section className="split-grid obs-grid"><div className="panel"><div className="panel-head"><div><span>Recent agent runs</span><b>{stats.protectedRuns} protected</b></div></div><div className="run-list">{runs.map((run) => <button key={run.id} className={selectedId === run.id ? "active" : ""} onClick={() => setSelectedId(run.id)}><span>{run.id.slice(0, 8)}</span><b>{run.status}</b><em>{run.latency_ms} ms</em></button>)}</div></div>{selected ? <div className="panel inspector"><div className="panel-head"><div><span>Run inspector</span><b>{selected.id}</b></div></div><dl><dt>Thread</dt><dd>{selected.thread_id}</dd><dt>Model</dt><dd>{selected.model ?? "—"}</dd><dt>Approval</dt><dd>{selected.approval_required ? (selected.approval_decision === true ? "Approved" : selected.approval_decision === false ? "Rejected" : "Pending") : "Not required"}</dd><dt>Tools</dt><dd>{selected.used_tools?.join(", ") || "None"}</dd></dl><h3>User request</h3><pre>{selected.user_message}</pre><h3>Agent answer</h3><p>{selected.answer || "Workflow has not completed yet."}</p><details><summary>Execution trace</summary><pre>{JSON.stringify(selected.trace, null, 2)}</pre></details></div> : <div className="panel locked-panel"><span>◎</span><h2>No run selected</h2></div>}</section>
  </div>;
}
