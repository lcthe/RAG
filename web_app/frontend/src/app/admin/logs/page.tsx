"use client";
import { useEffect, useState } from "react";
import { getLogs } from "@/lib/api";

export default function AdminLogs() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getLogs(100).then(setLogs).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const items = [
    { url: "/admin", icon: "📊", label: "概览" },
    { url: "/admin/documents", icon: "📄", label: "知识库" },
    { url: "/admin/logs", icon: "📋", label: "日志" },
    { url: "/admin/config", icon: "⚙️", label: "系统设置" },
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
               className={`sidebar-item ${item.url === "/admin/logs" ? "active" : ""}`}>
              <span className="icon">{item.icon}</span>{item.label}
            </a>
          ))}
        </div>
      </div>
      <div className="admin-content">
        <div className="admin-topbar">
          <div className="admin-breadcrumb">首页 / <span>日志</span></div>
          <div className="admin-topbar-right">
            <div className="admin-user"><div className="admin-avatar">A</div><span>管理员</span></div>
          </div>
        </div>
        <div className="admin-main">
          <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>查询日志</h2>
          <div className="admin-card">
            <div className="card-body" style={{ padding: 0 }}>
              {loading ? (
                <p className="placeholder">加载中...</p>
              ) : logs.length === 0 ? (
                <p className="placeholder">暂无查询记录</p>
              ) : (
                <div className="table-wrap" style={{ maxHeight: "70vh", overflowY: "auto" }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>时间</th>
                        <th>问题</th>
                        <th>回答预览</th>
                        <th>耗时</th>
                        <th>来源数</th>
                        <th>模型</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map(log => (
                        <tr key={log.id}>
                          <td style={{ fontSize: "12px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                            {new Date(log.created_at).toLocaleString("zh-CN")}
                          </td>
                          <td style={{ maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {log.question}
                          </td>
                          <td style={{ maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {log.answer_preview}
                          </td>
                          <td>{log.latency_ms?.toFixed(0)}ms</td>
                          <td>{log.retrieval_count}</td>
                          <td style={{ fontSize: "12px" }}>{log.model_used}</td>
                        </tr>
                      ))}
                    </tbody>
                </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
