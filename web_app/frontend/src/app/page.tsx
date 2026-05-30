"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { chatQuery, getInfo, getHistory, getConversation, saveConversation, deleteConversation } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: { text: string; score: number }[];
  latency?: number;
  model?: string;
  liked?: boolean;
  disliked?: boolean;
}

interface HistoryItem {
  id: string;
  title: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [sysInfo, setSysInfo] = useState("加载中...");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [activeHistory, setActiveHistory] = useState<string | null>(null);
  const [historySearch, setHistorySearch] = useState("");
  const [expandedCitation, setExpandedCitation] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    getInfo().then(info => 
      setSysInfo(`${info.llm} · ${info.vector_store} · ${info.cache}`)
    ).catch(() => setSysInfo("API 不可用"));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const q = question.trim();
    setQuestion("");
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: q };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      const res = await chatQuery(q);
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: res.answer,
        sources: res.sources,
        latency: res.latency_ms,
        model: res.model,
      };
      setMessages(prev => [...prev, assistantMsg]);

      // Add to history if first message
      if (history.length === 0) {
        const title = q.length > 20 ? q.substring(0, 20) + "..." : q;
        const newHistory = [{ id: Date.now().toString(), title }, ...history];
        setHistory(newHistory);
        setActiveHistory(newHistory[0].id);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "抱歉，发生了错误。请确认后端服务是否正常运行。",
      }]);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 150) + "px";
  };

  const newChat = () => {
    setMessages([]);
    setActiveHistory(null);
    setExpandedCitation(null);
    setShowPreview(null);
    if (textareaRef.current) textareaRef.current.focus();
  };

  const loadHistory = async (id: string) => {
    setActiveHistory(id);
    // In a real app, load messages from backend
  };

  const deleteHistory = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setHistory(prev => prev.filter(h => h.id !== id));
    deleteConversation(id).catch(() => {});
    if (activeHistory === id) {
      setActiveHistory(null);
      setMessages([]);
    }
  };

  const toggleCitation = (msgId: string, sourceIdx: number) => {
    const key = `${msgId}-${sourceIdx}`;
    setShowPreview(prev => prev === key ? null : key);
  };

  const filteredHistory = history.filter(h =>
    h.title.toLowerCase().includes(historySearch.toLowerCase())
  );

  return (
    <div className="chat-layout">
      {/* History Sidebar */}
      <div className="chat-history">
        <div className="history-header">
          <h3>历史对话</h3>
          <input
            className="history-search"
            placeholder="搜索对话..."
            value={historySearch}
            onChange={e => setHistorySearch(e.target.value)}
          />
        </div>
        <div className="history-list">
          {filteredHistory.map(h => (
            <div
              key={h.id}
              className={`history-item ${activeHistory === h.id ? "active" : ""}`}
              onClick={() => loadHistory(h.id)}
              title={h.title}
            >
              <span>{h.title}</span>
              <span
                style={{ float: "right", cursor: "pointer", opacity: 0.5 }}
                onClick={e => deleteHistory(h.id, e)}
              >
                ×
              </span>
            </div>
          ))}
          {filteredHistory.length === 0 && (
            <p className="placeholder">暂无对话记录</p>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-main-area">
        {/* Top Bar */}
        <div className="chat-topbar">
          <div className="chat-topbar-left">
            <div className="chat-logo">R</div>
            <span className="chat-app-name">RAG 问答</span>
          </div>
          <div className="chat-topbar-actions">
            <button className="btn-icon" onClick={newChat}>
              ＋ 新建对话
            </button>
            <button className="btn-icon" onClick={() => window.location.reload()}>
              ↻ 刷新
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.length === 0 && !loading && (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--text-muted)" }}>
              <div style={{ fontSize: "48px", marginBottom: "16px" }}>💬</div>
              <h2 style={{ color: "var(--text)", fontWeight: 600, marginBottom: "8px" }}>
                有什么可以帮助你的？
              </h2>
              <p style={{ fontSize: "14px" }}>
                基于知识库智能问答，输入问题开始对话
              </p>
            </div>
          )}

          {messages.map(msg => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="msg-avatar">
                {msg.role === "user" ? "👤" : "🤖"}
              </div>
              <div>
                <div className="msg-bubble">
                  <div className="msg-content" style={{ whiteSpace: "pre-wrap" }}>
                    {msg.content}
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="msg-citations">
                      {msg.sources.map((s, idx) => (
                        <span key={idx}>
                          <span
                            className="citation-tag"
                            onClick={() => toggleCitation(msg.id, idx)}
                          >
                            📎 来源 · 分段 {idx + 1} · {(s.score * 100).toFixed(0)}%
                          </span>
                          <div className={`citation-preview ${showPreview === `${msg.id}-${idx}` ? "visible" : ""}`}>
                            {s.text}
                          </div>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === "assistant" && (
                  <div className="msg-actions">
                    <button className="msg-action-btn" title="有用">👍</button>
                    <button className="msg-action-btn" title="没用">👎</button>
                    {msg.latency && (
                      <span style={{ fontSize: "11px", color: "var(--text-muted)", marginLeft: "8px" }}>
                        {msg.latency.toFixed(0)}ms · {msg.model}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="msg-avatar">🤖</div>
              <div className="msg-bubble">
                <div className="msg-content">
                  正在检索知识
                  <span className="thinking-dots">
                    <span></span><span></span><span></span>
                  </span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <form onSubmit={handleSubmit}>
            <div className="input-container">
              <div className="input-wrapper">
                <textarea
                  ref={textareaRef}
                  value={question}
                  onChange={handleTextareaInput}
                  onKeyDown={handleKeyDown}
                  placeholder="请输入您的问题..."
                  disabled={loading}
                  rows={1}
                />
              </div>
              <button type="submit" className="send-btn" disabled={loading || !question.trim()}>
                →
              </button>
            </div>
          </form>
          <div className="input-tools">
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              {sysInfo}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
