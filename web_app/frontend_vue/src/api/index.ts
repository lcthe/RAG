import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export interface ChatResponse {
  answer: string;
  sources: { text: string; score: number }[];
  latency_ms: number;
  model: string;
  retrieval_count: number;
}

export interface SysInfo {
  chunks: number;
  llm: string;
  emb: string;
  vector_store: string;
  cache: string;
}

export async function chat(question: string, topK?: number): Promise<ChatResponse> {
  const r = await api.post("/chat/", { question, top_k: topK });
  return r.data;
}

export async function getInfo(): Promise<SysInfo> {
  const r = await api.get("/chat/info/");
  return r.data;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const r = await api.get("/health/");
    return r.data.status === "ok";
  } catch {
    return false;
  }
}
