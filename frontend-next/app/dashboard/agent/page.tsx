"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { AgentResult } from "@/lib/types";
import { useDashboard } from "@/components/dashboard/dashboard-context";

type Message = { role: "user" | "assistant"; content: string; tools?: string[]; trace?: unknown[] };

function newThread() {
  return crypto.randomUUID();
}

export default function AgentPage() {
  const { station, user } = useDashboard();
  const [threadId, setThreadId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [pending, setPending] = useState<Record<string, unknown> | null>(null);
  const isOperator = user?.role === "operator" || user?.role === "admin";

  useEffect(() => {
    if (!station) return;
    const key = `chargeops_thread_${station.station_id}`;
    const existing = localStorage.getItem(key);
    const next = existing || newThread();
    localStorage.setItem(key, next);
    setThreadId(next);
    setMessages([]);
    setPending(null);
  }, [station?.station_id]);

  const title = useMemo(() => station ? `${station.station_id} — ${station.name}` : "Select a station", [station]);

  function reset() {
    if (!station) return;
    const next = newThread();
    localStorage.setItem(`chargeops_thread_${station.station_id}`, next);
    setThreadId(next);
    setMessages([]);
    setPending(null);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!station || !prompt.trim() || !threadId) return;
    const message = prompt.trim();
    setMessages((old) => [...old, { role: "user", content: message }]);
    setPrompt("");
    setLoading(true);
    try {
      const result = await api.agentRun(station.station_id, message, threadId);
      applyResult(result);
    } catch (error) {
      setMessages((old) => [...old, { role: "assistant", content: error instanceof Error ? error.message : "Agent request failed." }]);
    } finally {
      setLoading(false);
    }
  }

  function applyResult(result: AgentResult) {
    if (result.approval_required && result.approval_request) {
      setPending(result.approval_request);
      return;
    }
    if (result.answer) {
      setMessages((old) => [...old, { role: "assistant", content: result.answer!, tools: result.used_tools ?? [], trace: result.trace ?? [] }]);
    }
  }

  async function decide(approved: boolean) {
    setLoading(true);
    try {
      const result = await api.agentResume(threadId, approved);
      setPending(null);
      applyResult(result);
    } finally { setLoading(false); }
  }

  return (
    <div className="page-stack">
      <section className="page-hero compact">
        <div><div className="eyebrow">✦ OPERATIONS AGENT</div><h1>Ask. Diagnose. Act.</h1><p>Grounded EV-charging intelligence with RAG, live tools, persistent memory and human approval.</p></div>
        <div className="context-card"><span>Selected station</span><b>{title}</b><small>{station?.charger_model} · {station?.location}</small></div>
      </section>

      {!isOperator && <div className="notice">Viewer mode: safe read-only queries are available. Status-changing actions remain blocked by RBAC.</div>}

      <section className="chat-panel">
        <div className="chat-toolbar"><div><b>Conversation</b><span>{threadId.slice(0, 8) || "…"}</span></div><button className="ghost-button" onClick={reset}>+ New conversation</button></div>
        <div className="message-list">
          {messages.length === 0 && <div className="agent-empty"><span>ϟ</span><h2>What should ChargeOps investigate?</h2><p>Try: “Why is this station frequently going offline?”</p></div>}
          {messages.map((message, index) => <div className={`message ${message.role}`} key={index}><b>{message.role === "user" ? "You" : "ChargeOps AI"}</b><p>{message.content}</p>{message.tools && message.tools.length > 0 && <div className="tool-pills">{message.tools.map((tool) => <span key={tool}>{tool}</span>)}</div>}</div>)}
          {loading && <div className="thinking"><i/><i/><i/> ChargeOps is reasoning</div>}
        </div>

        {pending && isOperator && <div className="approval-card"><strong>Protected operation requires approval</strong><pre>{JSON.stringify(pending, null, 2)}</pre><div><button onClick={() => decide(true)} className="primary-button">Approve</button><button onClick={() => decide(false)} className="ghost-button">Reject</button></div></div>}

        <form className="chat-composer" onSubmit={submit}><textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Ask ChargeOps about this station…" rows={2}/><button disabled={loading || !prompt.trim()}>Send →</button></form>
      </section>
    </div>
  );
}
