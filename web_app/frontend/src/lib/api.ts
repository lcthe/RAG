export const API_BASE = "";

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
  const res = await fetch(`/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getInfo(): Promise<Record<string, any>> {
  const res = await fetch(`/api/chat/info`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getStats(): Promise<StatsResponse> {
  const res = await fetch(`/api/admin/stats`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getLogs(limit = 100): Promise<LogEntry[]> {
  const res = await fetch(`/api/admin/logs?limit=${limit}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function clearCache(): Promise<void> {
  await fetch(`/api/admin/cache/clear`, { method: "POST" });
}

export interface DocInfo {
  name: string;
  path: string;
  size: number;
  format: string;
}

export async function getDocuments(): Promise<DocInfo[]> {
  const res = await fetch(`/api/admin/documents`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function uploadDocument(file: File): Promise<{ status: string; filename: string; chunks: number }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`/api/admin/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload error: ${res.status}`);
  return res.json();
}

export async function reloadDocuments(): Promise<{ status: string; chunks: number }> {
  const res = await fetch(`/api/admin/documents/reload`, { method: "POST" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}


export async function getHistory(): Promise<{ id: string; title: string }[]> {
  const res = await fetch(`/api/chat/history`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getConversation(convId: string): Promise<{ id: string; title: string; messages: any[] }> {
  const res = await fetch(`/api/chat/history/${convId}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function saveConversation(convId: string, messages: any[], title: string = ""): Promise<void> {
  await fetch(`/api/chat/history/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: convId, messages, title }),
  });
}

export async function deleteConversation(convId: string): Promise<void> {
  await fetch(`/api/chat/history/${convId}`, { method: "DELETE" });
}
