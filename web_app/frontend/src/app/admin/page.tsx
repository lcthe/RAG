"use client";
import { useEffect, useState } from "react";
import { getStats, getInfo } from "@/lib/api";

export default function AdminDashboard() {
  const [stats, setStats] = useState<Record<string, any> | null>(null);
  const [info, setInfo] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.all([getStats(), getInfo()])
      .then(([s, i]) => { setStats(s); setInfo(i); })
      .catch(() => setError(true));
  }, []);

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <AdminSidebar active="/admin" />
      <div className="admin-content">
        <div className="admin-topbar">
          <div className="admin-breadcrumb">首页 / <span>概览</span></div>
          <div className="admin-topbar-right">
            <input className="admin-search" placeholder="搜索..." />
            <div className="admin-user"><div className="admin-avatar">A</div><span>管理员</span></div>
          </div>
        </div>
        <div className="admin-main">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-card-header"><span className="stat-icon">🧩</span></div>
              <div className="stat-value">{stats?.chunks ?? "-"}</div>
              <div className="stat-label">向量分块</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-header"><span className="stat-icon">💬</span></div>
              <div className="stat-value">{stats?.queries ?? "-"}</div>
              <div className="stat-label">总查询次数</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-header"><span className="stat-icon">⚡</span></div>
              <div className="stat-value">{stats?.cache_available ? "在线" : "离线"}</div>
              <div className="stat-label">Redis 缓存</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-header"><span className="stat-icon">🤖</span></div>
              <div className="stat-value">{info?.llm ?? "-"}</div>
              <div className="stat-label">LLM 模型</div>
            </div>
          </div>

          <div className="admin-card">
            <div className="card-header"><h2>系统信息</h2></div>
            <div className="card-body">
              {info ? (
                <table className="info-table">
                  <tbody>
                  {Object.entries(info).map(([k, v]) => (
                    <tr key={k}><td>{k}</td><td>{String(v)}</td></tr>
                  ))}
                  </tbody>
                </table>
              ) : (
                <p className="placeholder">加载中...</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminSidebar({ active }: { active: string }) {
  const items = [
    { url: "/admin", icon: "📊", label: "概览" },
    { url: "/admin/documents", icon: "📄", label: "知识库" },
    { url: "/admin/logs", icon: "📋", label: "日志" },
    { url: "/admin/config", icon: "⚙️", label: "系统设置" },
  ];
  return (
    <div className="admin-sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">R</div><span className="logo-text">RAG Console</span>
      </div>
      <div className="sidebar-menu">
        {items.map(item => (
          <a key={item.url} href={item.url}
             className={`sidebar-item ${active === item.url ? "active" : ""}`}>
            <span className="icon">{item.icon}</span>{item.label}
          </a>
        ))}
      </div>
    </div>
  );
}
