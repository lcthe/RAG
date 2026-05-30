"use client";
import { useEffect, useState, useRef } from "react";
import { getInfo, getDocuments, uploadDocument, reloadDocuments } from "@/lib/api";

interface DocInfo {
  name: string;
  path: string;
  size: number;
  format: string;
}

export default function AdminDocuments() {
  const [info, setInfo] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);
  const [docs, setDocs] = useState<DocInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [reloading, setReloading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [i, d] = await Promise.all([getInfo(), getDocuments()]);
      setInfo(i);
      setDocs(d);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg("");
    try {
      const res = await uploadDocument(file);
      setUploadMsg(✅  上传成功，已生成  个分块);
      await loadData();
    } catch (err: any) {
      setUploadMsg("❌ 上传失败: " + (err.message || "未知错误"));
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleReload = async () => {
    setReloading(true);
    try {
      const res = await reloadDocuments();
      setUploadMsg(✅ 已重新加载，共  个分块);
      await loadData();
    } catch {
      setUploadMsg("❌ 重新加载失败");
    }
    setReloading(false);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

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
               className={sidebar-item }>
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
              <input type="file" ref={fileInputRef} onChange={handleUpload} accept=".txt,.md,.pdf,.csv"
                style={{ display: "none" }} />
              <button className="btn btn-primary btn-sm" onClick={() => fileInputRef.current?.click()}
                disabled={uploading}>
                {uploading ? "上传中..." : "上传文档"}
              </button>
              <button className="btn btn-sm" onClick={handleReload} disabled={reloading}>
                {reloading ? "加载中..." : "重新加载"}
              </button>
            </div>
          </div>

          {uploadMsg && (
            <div style={{ padding: "8px 16px", marginBottom: "16px", borderRadius: "var(--radius)", background: uploadMsg.includes("✅") ? "#ECFDF5" : "#FEF2F2", color: uploadMsg.includes("✅") ? "var(--success)" : "var(--danger)", fontSize: "14px" }}>
              {uploadMsg}
            </div>
          )}

          <div className="admin-card">
            <div className="card-body" style={{ padding: 0 }}>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>文件名</th>
                      <th>格式</th>
                      <th>大小</th>
                    </tr>
                  </thead>
                  <tbody>
                    {docs.length === 0 ? (
                      <tr><td colSpan={3}><p className="placeholder">暂无文档，点击上方「上传文档」按钮添加</p></td></tr>
                    ) : (
                      docs.map((doc, i) => (
                        <tr key={i}>
                          <td>{doc.name}</td>
                          <td><span className="badge badge-primary">{doc.format}</span></td>
                          <td>{formatSize(doc.size)}</td>
                        </tr>
                      ))
                    )}
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
                  <tr><td>文档数</td><td>{docs.length}</td></tr>
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
