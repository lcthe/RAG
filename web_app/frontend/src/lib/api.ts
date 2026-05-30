export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:18762";

export interface ChatResponse {
  answer: string;
  sources: { text: string; score: number }[];
  latency_ms: number;
  model: string;
  retrieval_count: number;
}

export interface StatsResponse {
  documents: number;
  chunks: number;
  queries: number;
  last_query: string | null;
  cache_available: boolean;
}

export interface LogEntry {
  id: number;
  question: string;
  answer_preview: string;
  latency_ms: number;
  retrieval_count: number;
  model_used: string;
  created_at: string;
}

export async function chatQuery(question: string, topK?: number): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getInfo(): Promise<Record<string, any>> {
  const res = await fetch(`${API_BASE}/api/chat/info`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/api/admin/stats`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getLogs(limit = 100): Promise<LogEntry[]> {
  const res = await fetch(`${API_BASE}/api/admin/logs?limit=${limit}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function clearCache(): Promise<void> {
  await fetch(`${API_BASE}/api/admin/cache/clear`, { method: "POST" });
}