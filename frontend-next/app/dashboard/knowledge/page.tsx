"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { KnowledgeDocument, KnowledgeSearchResult } from "@/lib/types";
import { useDashboard } from "@/components/dashboard/dashboard-context";

export default function KnowledgePage() {
  const { user } = useDashboard();
  const isAdmin = user?.role === "admin";
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(5);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() { try { setDocs(await api.knowledgeDocuments()); } catch (e) { setError(e instanceof Error ? e.message : "Could not load knowledge documents."); } }
  useEffect(() => { load(); }, []);

  async function search(event: FormEvent) { event.preventDefault(); if (query.trim().length < 3) return; setBusy(true); setError(""); try { const data = await api.knowledgeSearch(query.trim(), limit); setResults(data.results ?? []); } catch (e) { setError(e instanceof Error ? e.message : "Knowledge search failed."); } finally { setBusy(false); } }
  async function upload(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); setBusy(true); try { await api.uploadKnowledge(form); event.currentTarget.reset(); await load(); } catch (e) { setError(e instanceof Error ? e.message : "Document upload failed."); } finally { setBusy(false); } }
  async function remove(id: number) { if (!confirm("Delete this document and all vector chunks?")) return; await api.deleteKnowledge(id); await load(); }

  const chunks = docs.reduce((sum, doc) => sum + (doc.chunk_count ?? 0), 0);
  return <div className="page-stack">
    <section className="page-hero compact"><div><div className="eyebrow">▤ RAG KNOWLEDGE</div><h1>Search by meaning, not just words.</h1><p>Technical EV charging knowledge is extracted, chunked, embedded and retrieved from PostgreSQL + pgvector.</p></div></section>
    {error && <div className="form-error">{error}</div>}
    <section className="metric-grid two"><article><span>Indexed documents</span><strong>{docs.length}</strong></article><article><span>Vector chunks</span><strong>{chunks}</strong></article></section>
    <section className="split-grid">
      <div className="panel"><div className="panel-head"><div><span>Semantic search</span><b>Grounded retrieval</b></div></div><form className="search-form" onSubmit={search}><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. charger cable becomes extremely hot"/><input type="range" min="1" max="10" value={limit} onChange={(e) => setLimit(Number(e.target.value))}/><button disabled={busy}>{busy ? "Searching…" : `Search top ${limit}`}</button></form><div className="search-results">{results.map((result, index) => <article key={`${result.title}-${index}`}><div><b>{index + 1}. {result.title ?? "Untitled"}</b><span>{Math.round((result.similarity ?? 0) * 100)}%</span></div><small>{result.category} · {result.source}</small><p>{result.content}</p></article>)}</div></div>
      {isAdmin ? <div className="panel"><div className="panel-head"><div><span>Upload document</span><b>PDF · TXT · MD</b></div></div><form className="upload-form" onSubmit={upload}><label>File<input name="file" type="file" accept=".pdf,.txt,.md" required/></label><label>Title<input name="title" placeholder="ABB Terra 54 Installation Manual"/></label><label>Category<input name="category" defaultValue="manual"/></label><button disabled={busy}>Upload and index →</button></form></div> : <div className="panel locked-panel"><span>🔒</span><h2>Viewer access</h2><p>Upload and deletion are restricted to administrators.</p></div>}
    </section>
    <section className="document-grid">{docs.map((doc) => <article key={doc.id}><div className="doc-icon">▤</div><div><h3>{doc.title}</h3><p>{doc.category} · {doc.chunk_count} chunks</p><small>{doc.source_filename}</small></div>{isAdmin && <button onClick={() => remove(doc.id)}>Delete</button>}</article>)}</section>
  </div>;
}
