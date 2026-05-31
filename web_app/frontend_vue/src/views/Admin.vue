<template>
  <div class="admin-page">
    <!-- 左侧导航 -->
    <aside class="admin-sidebar">
      <div class="sidebar-logo">
        <span class="logo-icon">◆</span>
        <span class="logo-text">RAG 管理</span>
      </div>
      <nav class="sidebar-nav">
        <a
          v-for="item in navItems"
          :key="item.key"
          :class="['nav-item', { active: activeTab === item.key }]"
          @click="activeTab = item.key"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </a>
      </nav>
      <div class="sidebar-footer">
        <a class="nav-item" href="/">
          <span class="nav-icon">💬</span>
          <span class="nav-label">返回问答</span>
        </a>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="admin-content">
      <!-- 顶部栏 -->
      <header class="admin-topbar">
        <div class="breadcrumb">
          <span>RAG 管理</span>
          <span class="sep">/</span>
          <span class="current">{{ currentNav?.label }}</span>
        </div>
        <div class="topbar-right">
          <span class="health-badge" :class="{ ok: healthy }">
            {{ healthy ? "● 服务正常" : "○ 服务异常" }}
          </span>
        </div>
      </header>

      <main class="admin-main">
        <!-- ===== 概览 ===== -->
        <div v-if="activeTab === 'overview'" class="tab-content">
          <h2 class="page-title">系统概览</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ info?.chunks ?? "-" }}</div>
              <div class="stat-label">知识库分块</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ info?.llm ?? "-" }}</div>
              <div class="stat-label">LLM 模型</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ info?.vector_store ?? "-" }}</div>
              <div class="stat-label">向量数据库</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ info?.emb ?? "-" }}</div>
              <div class="stat-label">嵌入模型</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ info?.cache ?? "无" }}</div>
              <div class="stat-label">缓存服务</div>
            </div>
          </div>
        </div>

        <!-- ===== 知识库 ===== -->
        <div v-if="activeTab === 'knowledge'" class="tab-content">
          <div class="page-header">
            <h2 class="page-title">知识库管理</h2>
            <div class="header-actions">
              <button class="btn btn-outline" @click="reloadDocs">重新加载</button>
            </div>
          </div>
          <div class="upload-zone" @drop.prevent="onDrop" @dragover.prevent>
            <div class="upload-icon">📄</div>
            <p>拖拽文件到此处上传，或</p>
            <button class="btn btn-primary" @click="triggerUpload">选择文件</button>
            <p class="upload-hint">支持 TXT、MD、PDF、DOCX 格式</p>
          </div>
          <input ref="fileInput" type="file" accept=".txt,.md,.pdf,.docx" style="display:none" @change="handleUpload" />
          <div class="doc-list">
            <h3>已上传文档 ({{ documents.length }})</h3>
            <table class="data-table">
              <thead>
                <tr><th>文件名</th><th>大小</th><th>格式</th><th>分块数</th><th>上传时间</th></tr>
              </thead>
              <tbody>
                <tr v-for="doc in documents" :key="doc.id">
                  <td>{{ doc.name }}</td>
                  <td>{{ (doc.file_size / 1024).toFixed(1) }} KB</td>
                  <td><span class="format-tag">{{ doc.format }}</span></td>
                  <td>{{ doc.chunk_count }}</td>
                  <td>{{ timeStr(doc.created_at) }}</td>
                </tr>
                <tr v-if="!documents.length">
                  <td colspan="5" class="empty-cell">暂无文档</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ===== 模型管理 ===== -->
        <div v-if="activeTab === 'models'" class="tab-content">
          <h2 class="page-title">模型管理</h2>
          <div class="info-card">
            <table class="data-table">
              <thead>
                <tr><th>配置项</th><th>当前值</th></tr>
              </thead>
              <tbody>
                <tr><td>LLM 模型</td><td>{{ info?.llm ?? "-" }}</td></tr>
                <tr><td>嵌入模型</td><td>{{ info?.emb ?? "BAAI/bge-small-zh-v1.5" }}</td></tr>
                <tr><td>向量数据库</td><td>{{ info?.vector_store ?? "-" }}</td></tr>
                <tr><td>缓存</td><td>{{ info?.cache ?? "-" }}</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ===== 系统管理 ===== -->
        <div v-if="activeTab === 'system'" class="tab-content">
          <h2 class="page-title">系统管理</h2>
          <div class="info-card">
            <h3>Django 管理后台</h3>
            <p>完整的数据库管理和用户权限管理：</p>
            <a :href="adminUrl" target="_blank" class="btn btn-primary">{{ adminUrl }}</a>
          </div>
          <div class="info-card" style="margin-top: 16px;">
            <h3>健康检查</h3>
            <p>状态：<span :class="healthy ? 'text-green' : 'text-red'">{{ healthy ? "运行正常" : "异常" }}</span></p>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { getInfo, getDocuments, uploadDocument, reloadVectorStore, healthCheck } from "../api"

const activeTab = ref("overview")
const info = ref<any>(null)
const documents = ref<any[]>([])
const healthy = ref(false)
const fileInput = ref<HTMLElement | null>(null)
const adminUrl = "http://localhost:18762/admin/"

const navItems = [
  { key: "overview", label: "概览", icon: "📊" },
  { key: "knowledge", label: "知识库", icon: "📚" },
  { key: "models", label: "模型", icon: "🤖" },
  { key: "system", label: "系统管理", icon: "⚙️" },
]

const currentNav = computed(() => navItems.find((n) => n.key === activeTab.value))

onMounted(async () => {
  await loadData()
})

async function loadData() {
  try { info.value = await getInfo() } catch {}
  try { documents.value = await getDocuments() } catch {}
  healthy.value = await healthCheck()
}

function triggerUpload() { fileInput.value?.click() }

async function handleUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return
  try {
    await uploadDocument(file)
    await loadData()
  } catch {}
  input.value = ""
}

async function onDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (!file) return
  try {
    await uploadDocument(file)
    await loadData()
  } catch {}
}

async function reloadDocs() {
  try {
    await reloadVectorStore()
    await loadData()
  } catch {}
}

function timeStr(dateStr: string): string {
  return new Date(dateStr).toLocaleString("zh-CN")
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex: 1;
  height: 100vh;
  overflow: hidden;
}

/* ===== 左侧导航 ===== */
.admin-sidebar {
  width: 220px;
  min-width: 220px;
  background: #1e1e2f;
  color: #fff;
  display: flex;
  flex-direction: column;
}
.sidebar-logo {
  padding: 24px 20px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.logo-icon { color: #818cf8; font-size: 22px; }
.logo-text { font-weight: 700; font-size: 16px; }
.sidebar-nav {
  flex: 1;
  padding: 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  color: #a5b4fc;
  transition: all 0.15s;
  text-decoration: none;
}
.nav-item:hover { background: rgba(255,255,255,0.08); color: #fff; }
.nav-item.active { background: #6366f1; color: #fff; }
.nav-icon { font-size: 18px; width: 24px; text-align: center; }
.nav-label { font-size: 14px; }
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255,255,255,0.08);
}

/* ===== 右侧主区域 ===== */
.admin-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.admin-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}
.breadcrumb { font-size: 14px; color: #6b7280; }
.breadcrumb .sep { margin: 0 8px; color: #d1d5db; }
.breadcrumb .current { color: #1f2937; font-weight: 600; }
.health-badge { font-size: 12px; padding: 4px 12px; border-radius: 12px; background: #fee2e2; color: #dc2626; }
.health-badge.ok { background: #dcfce7; color: #16a34a; }

.admin-main {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f9fafb;
}
.tab-content { max-width: 960px; }
.page-title { font-size: 20px; color: #1f2937; margin-bottom: 20px; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header .page-title { margin-bottom: 0; }
.header-actions { display: flex; gap: 8px; }

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}
.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  text-align: center;
}
.stat-value { font-size: 16px; font-weight: 700; color: #6366f1; margin-bottom: 6px; }
.stat-label { font-size: 13px; color: #6b7280; }

/* 上传区域 */
.upload-zone {
  background: #fff;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  margin-bottom: 20px;
  transition: border-color 0.15s;
}
.upload-zone:hover { border-color: #6366f1; }
.upload-icon { font-size: 36px; margin-bottom: 8px; }
.upload-zone p { color: #6b7280; font-size: 14px; margin-bottom: 12px; }
.upload-hint { font-size: 12px; color: #9ca3af; margin-top: 8px; }

/* 数据表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.data-table th {
  text-align: left;
  padding: 10px 12px;
  background: #f9fafb;
  color: #6b7280;
  font-weight: 600;
  font-size: 13px;
  border-bottom: 2px solid #e5e7eb;
}
.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #1f2937;
}
.data-table tr:hover td { background: #f9fafb; }
.format-tag {
  background: #eef2ff;
  color: #6366f1;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.empty-cell { text-align: center; color: #9ca3af; padding: 24px; }

/* 信息卡片 */
.info-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.info-card h3 { font-size: 16px; margin-bottom: 12px; color: #1f2937; }
.info-card p { font-size: 14px; color: #6b7280; margin-bottom: 12px; }

/* 按钮 */
.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-primary { background: #6366f1; color: #fff; }
.btn-primary:hover { background: #4f46e5; }
.btn-outline {
  background: #fff;
  color: #6366f1;
  border: 1px solid #6366f1;
}
.btn-outline:hover { background: #eef2ff; }
.text-green { color: #16a34a; }
.text-red { color: #dc2626; }
</style>
