export type User = {
  id: string;
  email: string;
  role: "viewer" | "operator" | "admin" | string;
  is_active: boolean;
  created_at?: string;
};

export type Station = {
  station_id: string;
  name: string;
  charger_model: string;
  location: string;
  latitude: number;
  longitude: number;
  status: string;
  [key: string]: unknown;
};

export type Incident = {
  id: number;
  category: string;
  confidence: number;
  severity: string;
  status: string;
  issue: string;
  summary: string;
  likely_causes?: string[];
  diagnostic_steps?: { step?: number | string; action?: string }[];
  needs_human_escalation?: boolean;
  created_at?: string;
  [key: string]: unknown;
};

export type AgentTrace = {
  tool?: string;
  summary?: string;
  status?: string;
  [key: string]: unknown;
};

export type AgentResult = {
  answer?: string;
  used_tools?: string[];
  trace?: AgentTrace[];
  approval_required?: boolean;
  approval_request?: Record<string, unknown>;
};

export type ForecastPoint = {
  timestamp: string;
  predicted_energy_kwh: number;
  risk_level?: string;
  temperature_c?: number;
  precipitation_mm?: number;
  mobility_index?: number;
};

export type ForecastResponse = {
  summary: {
    peak_energy_kwh: number;
    total_predicted_energy_kwh: number;
    average_hourly_energy_kwh: number;
    peak_timestamp: string;
  };
  peak_risk: string;
  points: ForecastPoint[];
  model_version?: string;
  history_source?: string;
  weather_source?: string;
};

export type KnowledgeDocument = {
  id: number;
  title: string;
  category: string;
  status: string;
  source_filename: string;
  media_type: string;
  document_key: string;
  created_at: string;
  chunk_count: number;
};

export type KnowledgeSearchResult = {
  title?: string;
  category?: string;
  source?: string;
  similarity?: number;
  content?: string;
};

export type AgentRun = {
  id: string;
  thread_id: string;
  status: string;
  latency_ms: number;
  used_tools: string[];
  approval_required: boolean;
  approval_decision?: boolean | null;
  started_at: string;
  model?: string;
  user_message?: string;
  answer?: string | null;
  trace?: unknown;
};
