"use client";

import type {
  AgentResult,
  AgentRun,
  ForecastResponse,
  Incident,
  KnowledgeDocument,
  KnowledgeSearchResult,
  Station,
  User,
} from "@/lib/types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/proxy${path}`, {
    ...init,
    cache: "no-store",
  });

  if (response.status === 401) {
    window.location.href = "/";
    throw new Error("Session expired");
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      detail = payload.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "Incorrect email or password.");
  }
}

export async function logout() {
  await fetch("/api/auth/logout", { method: "POST" });
  window.location.href = "/";
}

export const api = {
  me: () => request<User>("/auth/me"),
  stations: () => request<Station[]>("/stations"),
  incidents: (stationId: string) =>
    request<Incident[]>(`/incidents?station_id=${encodeURIComponent(stationId)}&limit=100`),
  updateIncident: (incidentId: number, status: string) =>
    request<Incident>(`/incidents/${incidentId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),
  forecast: (stationId: string, hours: number) =>
    request<ForecastResponse>(
      `/forecast/stations/${encodeURIComponent(stationId)}?hours=${hours}`,
    ),
  agentRun: (stationId: string, message: string, threadId: string) =>
    request<AgentResult>("/agent/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ station_id: stationId, message, thread_id: threadId }),
    }),
  agentResume: (threadId: string, approved: boolean) =>
    request<AgentResult>("/agent/resume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: threadId, approved }),
    }),
  knowledgeDocuments: () => request<KnowledgeDocument[]>("/knowledge/documents"),
  knowledgeSearch: (query: string, limit: number) =>
    request<{ results: KnowledgeSearchResult[] }>("/knowledge/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, limit }),
    }),
  uploadKnowledge: (form: FormData) =>
    request<KnowledgeDocument>("/knowledge/documents/upload", { method: "POST", body: form }),
  deleteKnowledge: (id: number) =>
    request<void>(`/knowledge/documents/${id}`, { method: "DELETE" }),
  runs: (stationId: string, limit = 100) =>
    request<AgentRun[]>(
      `/observability/runs?station_id=${encodeURIComponent(stationId)}&limit=${limit}`,
    ),
  users: () => request<User[]>("/users"),
  createUser: (email: string, password: string, role: string) =>
    request<User>("/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role }),
    }),
  changeUserRole: (id: string, role: string) =>
    request<User>(`/users/${id}/role`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    }),
  changeUserStatus: (id: string, isActive: boolean) =>
    request<User>(`/users/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_active: isActive }),
    }),
};
