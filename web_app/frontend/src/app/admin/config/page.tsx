"use client";
import { useState } from "react";
import { clearCache } from "@/lib/api";

export default function AdminConfig() {
  const [cacheCleared, setCacheCleared] = useState(false);

  const handleClearCache = async () => {
    try {
      await clearCache();
      setCacheCleared(true);
      setTimeout(() => setCacheCleared(false), 3000);
    } catch {}
  };

  const items = [
    { url: "/admin", icon: "📊", label: "概览" },
    { url: "/admin/documents", icon: "📄", label: "知识库" },
    { url: "/admin/logs", icon: "📋", label: "日志" },
    { url: "/admin/config", icon: "⚙️", label: "系统设置" },
  ];

  const configItems = [
    { key: "CHUNK_SIZE", value: "300", desc: "文本分块大小" },
    { key: "CHUNK_OVERLAP", value: "50", desc: "分块重叠长度" },
    { key: "TOP_K", value: "5", desc: "每次检索返回的块数" },
    { key: "EMBEDDING", value: "local_bge", desc: "嵌入模型" },
    { key: "LLM", value: "auto", desc: "LLM 供应商" },
    { key: "VECTOR_DB", value: "ChromaDB", desc: "向量数据库" },
    { key: "CACHE", value: "Redis", desc: "查询缓存" },
  ];

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div className="admin-sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">R</div><span className="logo-text">RAG Console</span>
        </div>
        <div className="sidebar-menu">
          {items.map(item => (
            <a key={item.url} href={item.url}
               className={`sidebar-item ${item.url === "/admin/config" ? "active" : ""}`}>
              <span className="icon">{item.icon}</span>{item.label}
            </a>
          ))}
        </div>
      </div>
      <div className="admin-content">
        <div className="admin-topbar">
          <div className="admin-breadcrumb">首页 / <span>系统设置</span></div>
          <div className="admin-topbar-right">
            <div className="admin-user"><div className="admin-avatar">A</div><span>管理员</span></div>
          </div>
        </div>
        <div className="admin-main">
          <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>系统设置</h2>

          <div className="admin-card">
            <div className="card-header"><h2>RAG 参数配置</h2></div>
            <div className="card-body" style={{ padding: 0 }}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>参数</th>
                      <th>当前值</th>
                      <th>说明</th>
                    </tr>
                  </thead>
                  <tbody>
                    {configItems.map(item => (
                      <tr key={item.key}>
                        <td style={{ fontWeight: 600, fontFamily: "monospace", fontSize: "13px" }}>{item.key}</td>
                        <td><code>{item.value}</code></td>
                        <td style={{ color: "var(--text-secondary)", fontSize: "13px" }}>{item.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="admin-card">
            <div className="card-header"><h2>缓存管理</h2></div>
            <div className="card-body">
              <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "12px" }}>
                Redis 缓存查询结果以加速重复问题的响应速度。更新数据后请清除缓存。
              </p>
              <button className="btn" onClick={handleClearCache}
                style={{ background: cacheCleared ? "var(--success)" : "var(--danger)", color: "#fff", border: "none" }}>
                {cacheCleared ? "✓ 缓存已清除" : "清除 Redis 缓存"}
              </button>
            </div>
          </div>

          <div className="admin-card">
            <div className="card-header"><h2>API 接口</h2></div>
            <div className="card-body" style={{ padding: 0 }}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr><th>端点</th><th>方法</th><th>说明</th></tr>
                  </thead>
                  <tbody>
                    <tr><td><code>/api/chat</code></td><td><span className="badge badge-primary">POST</span></td><td>发送问题</td></tr>
                    <tr><td><code>/api/chat/info</code></td><td><span className="badge badge-success">GET</span></td><td>系统信息</td></tr>
                    <tr><td><code>/api/admin/stats</code></td><td><span className="badge badge-success">GET</span></td><td>统计数据</td></tr>
                    <tr><td><code>/api/admin/logs</code></td><td><span className="badge badge-success">GET</span></td><td>查询日志</td></tr>
                    <tr><td><code>/api/admin/cache/clear</code></td><td><span className="badge badge-warning">POST</span></td><td>清除缓存</td></tr>
                    <tr><td><code>/api/health</code></td><td><span className="badge badge-success">GET</span></td><td>健康检查</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
