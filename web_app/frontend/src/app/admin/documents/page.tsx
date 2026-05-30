"use client";
import { useEffect, useState } from "react";
import { getInfo } from "@/lib/api";

export default function AdminDocuments() {
  const [info, setInfo] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getInfo().then(setInfo).catch(() => {}).finally(() => setLoading(false));
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
               className={`sidebar-item ${item.url === "/admin/documents" ? "active" : ""}`}>
              <span className="icon">{item.icon}</span>{item.label}
            </a>
          ))}
        </div>
      </div>
      <div className="admin-content">
        <div className="admin-topbar">
          <div className="admin-breadcrumb">首页 / <span>知识库</span></div>
          <div className="admin-topbar-right">
            <div className="admin-user"><div className="admin-avatar">A</div><span>管理员</span></div>
          </div>
        </div>
        <div className="admin-main">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: 600 }}>知识库管理</h2>
            <div style={{ display: "flex", gap: "8px" }}>
              <button className="btn btn-primary btn-sm">上传文档</button>
            </div>
          </div>

          <div className="admin-card">
            <div className="card-body">
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>文件名</th>
                      <th>格式</th>
                      <th>大小</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr><td colSpan={4}><p className="placeholder">文档数据由 ChromaDB 管理</p></td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="admin-card">
            <div className="card-header"><h2>向量存储状态</h2></div>
            <div className="card-body">
              {loading ? (
                <p className="placeholder">加载中...</p>
              ) : (
                <table className="info-table">
                  <tbody>
                  <tr><td>向量数据库</td><td>ChromaDB</td></tr>
                  <tr><td>索引分块数</td><td>{info?.chunks ?? "-"}</td></tr>
                  <tr><td>嵌入模型</td><td>{info?.emb ?? "-"}</td></tr>
                </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
