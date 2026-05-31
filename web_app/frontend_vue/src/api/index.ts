import axios from "axios";

const api = axios.create({ baseURL: "/api" });

/* ============ 类型定义 ============ */
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

export interface Conversation {
  id: string;
  title: string;
  message_count?: number;
  created_at: string;
}

export interface Message {
  id?: number;
  role: "user" | "assistant";
  content: string;
  sources?: { text: string; score: number }[];
  latency_ms?: number;
  model_used?: string;
  created_at?: string;
}

export interface DocInfo {
  id: number;
  name: string;
  file_size: number;
  format: string;
  chunk_count: number;
  created_at: string;
}

/* ============ 问答接口 ============ */
export async function chat(question: string, topK?: number): Promise<ChatResponse> {
  const r = await api.post("/chat/", { question, top_k: topK });
  return r.data;
}

export async function getInfo(): Promise<SysInfo> {
  const r = await api.get("/chat/info/");
  return r.data;
}

/* ============ 对话历史接口 ============ */
export async function getConversations(): Promise<Conversation[]> {
  const r = await api.get("/chat/conversations/");
  return r.data;
}

export async function getConversation(id: string): Promise<{ messages: Message[] }> {
  const r = await api.get(`/chat/conversations/${id}/`);
  return r.data;
}

export async function saveConversation(data: {
  id?: string;
  title?: string;
  messages: { role: string; content: string; sources?: any[] }[];
}): Promise<{ status: string }> {
  const r = await api.post("/chat/save_conversation/", data);
  return r.data;
}

export async function deleteConversation(id: string): Promise<{ status: string }> {
  const r = await api.delete(`/chat/delete_conversation/${id}/`);
  return r.data;
}

/* ============ 文档管理接口 ============ */
export async function getDocuments(): Promise<DocInfo[]> {
  const r = await api.get("/admin/documents/");
  return r.data;
}

export async function uploadDocument(file: File): Promise<{ status: string; filename: string; chunks: number }> {
  const form = new FormData();
  form.append("file", file);
  const r = await api.post("/admin/documents/upload/", form);
  return r.data;
}

export async function reloadVectorStore(): Promise<{ status: string }> {
  const r = await api.post("/admin/documents/reload/");
  return r.data;
}

/* ============ 健康检查 ============ */
export async function healthCheck(): Promise<boolean> {
  try {
    const r = await api.get("/health/");
    return r.data.status === "ok";
  } catch {
    return false;
  }
}
