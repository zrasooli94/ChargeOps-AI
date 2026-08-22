"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Incident } from "@/lib/types";
import { useDashboard } from "@/components/dashboard/dashboard-context";

export default function IncidentsPage() {
  const { station, user } = useDashboard();
  const [items, setItems] = useState<Incident[]>([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const isOperator = user?.role === "operator" || user?.role === "admin";

  async function load() {
    if (!station) return;
    try { setItems(await api.incidents(station.station_id)); setError(""); } catch (e) { setError(e instanceof Error ? e.message : "Could not load incidents."); }
  }
  useEffect(() => { load(); }, [station?.station_id]);

  const shown = useMemo(() => filter === "all" ? items : items.filter((item) => item.status === filter), [items, filter]);
  const counts = { total: items.length, open: items.filter((i) => i.status === "open").length, investigating: items.filter((i) => i.status === "investigating").length, resolved: items.filter((i) => i.status === "resolved").length };

  async function update(id: number, status: string) { await api.updateIncident(id, status); await load(); }

  return <div className="page-stack">
    <section className="page-hero compact"><div><div className="eyebrow">△ INCIDENT INTELLIGENCE</div><h1>Operational issues, without the noise.</h1><p>Trace AI diagnostics, likely causes, escalation needs and incident lifecycle for the selected station.</p></div><div className="select-card"><span>Filter</span><select value={filter} onChange={(e) => setFilter(e.target.value)}><option value="all">All incidents</option><option value="open">Open</option><option value="investigating">Investigating</option><option value="resolved">Resolved</option></select></div></section>
    {error && <div className="form-error">{error}</div>}
    <section className="metric-grid four"><article><span>Total</span><strong>{counts.total}</strong></article><article><span>Open</span><strong>{counts.open}</strong></article><article><span>Investigating</span><strong>{counts.investigating}</strong></article><article><span>Resolved</span><strong>{counts.resolved}</strong></article></section>
    <section className="incident-grid">{shown.map((incident) => <article className="incident-card" key={incident.id}><div className="incident-top"><span className={`severity severity-${incident.severity}`}>{incident.severity}</span><span>#{incident.id}</span></div><h2>{incident.issue}</h2><p>{incident.summary}</p><div className="incident-meta"><span>{incident.category}</span><span>{Math.round((incident.confidence ?? 0) * 100)}% confidence</span><span>{incident.status}</span></div>{incident.likely_causes?.length ? <details><summary>Likely causes</summary><ul>{incident.likely_causes.map((cause) => <li key={cause}>{cause}</li>)}</ul></details> : null}{incident.diagnostic_steps?.length ? <details><summary>Diagnostic steps</summary><ol>{incident.diagnostic_steps.map((step, index) => <li key={index}>{step.action}</li>)}</ol></details> : null}{incident.needs_human_escalation && <div className="notice warn">Human escalation recommended</div>}{isOperator && <div className="incident-actions"><select defaultValue={incident.status} onChange={(e) => update(incident.id, e.target.value)}><option value="open">Open</option><option value="investigating">Investigating</option><option value="resolved">Resolved</option></select></div>}</article>)}</section>
  </div>;
}
