<template>
  <div class="chat-page">
    <!-- 左侧：历史对话列表 -->
    <aside class="history-sidebar">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <span class="logo-icon">◆</span>
          <span class="logo-text">RAG 智能问答</span>
        </div>
        <button class="btn-new-chat" @click="newChat">+ 新建对话</button>
      </div>
      <div class="search-box">
        <input v-model="searchQuery" placeholder="搜索历史对话..." />
      </div>
      <div class="history-list">
        <div
          v-for="conv in filteredHistory"
          :key="conv.id"
          :class="['history-item', { active: currentConvId === conv.id }]"
          @click="loadConversation(conv.id)"
        >
          <div class="history-item-title">{{ conv.title || "新对话" }}</div>
          <div class="history-item-meta">
            <span>{{ timeAgo(conv.created_at) }}</span>
            <span class="msg-count">{{ conv.message_count || 0 }} 条</span>
          </div>
          <button class="btn-delete" @click.stop="delConversation(conv.id)" title="删除">✕</button>
        </div>
        <div v-if="!filteredHistory.length" class="history-empty">
          {{ searchQuery ? "无匹配结果" : "暂无历史记录" }}
        </div>
      </div>
    </aside>

    <!-- 右侧：对话主区域 -->
    <div class="chat-main">
      <!-- 顶部栏 -->
      <div class="chat-topbar">
        <div class="topbar-left">
          <span class="topbar-title">{{ currentTitle || "新对话" }}</span>
        </div>
        <div class="topbar-right">
          <span class="sys-badge" v-if="info">{{ info.llm }} · {{ info.vector_store }}</span>
          <button class="btn-icon" @click="refreshInfo" title="刷新状态">⟳</button>
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="messages" ref="msgBox">
        <div v-if="!messages.length && !loading" class="empty-state">
          <div class="empty-icon">📚</div>
          <h3>有什么可以帮你的？</h3>
          <p>基于知识库智能问答，输入问题开始对话</p>
          <div class="suggestions">
            <div v-for="(q, i) in quickQuestions" :key="i" class="suggestion-chip" @click="askQuick(q)">
              {{ q }}
            </div>
          </div>
        </div>
        <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
          <div class="avatar">{{ m.role === "user" ? "👤" : "🤖" }}</div>
          <div class="bubble">
            <div class="content markdown-body" v-html="renderMarkdown(m.content)"></div>
            <div v-if="m.sources?.length" class="sources">
              <div class="sources-label">📎 来源引用</div>
              <div v-for="(s, j) in m.sources" :key="j" class="source-item">
                <span class="source-badge">来源 {{ j + 1 }}</span>
                <span class="source-score">{{ (s.score * 100).toFixed(0) }}%</span>
                <span class="source-preview">{{ s.text?.slice(0, 80) }}...</span>
              </div>
            </div>
            <div v-if="m.latency_ms" class="msg-meta">{{ m.latency_ms }}ms · {{ m.model_used || "" }}</div>
          </div>
        </div>
        <div v-if="loading" class="msg assistant">
          <div class="avatar">🤖</div>
          <div class="bubble">
            <div class="content loading-dots">
              <span>正在检索知识</span>
              <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <form @submit.prevent="send">
          <div class="input-wrapper">
            <input
              v-model="question"
              placeholder="请输入您的问题，回车发送..."
              :disabled="loading"
              @keydown.enter.prevent="send"
            />
            <button type="button" class="btn-upload" @click="triggerUpload" title="上传文档">📎</button>
            <button type="submit" class="btn-send" :disabled="loading || !question.trim()">
              发送
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 隐藏的文件上传 -->
    <input ref="fileInput" type="file" accept=".txt,.md,.pdf,.docx" style="display:none" @change="handleUpload" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue"
import { chat, getInfo, getConversations, getConversation, saveConversation, deleteConversation, uploadDocument, reloadVectorStore } from "../api"

const question = ref("")
const messages = ref<any[]>([])
const loading = ref(false)
const info = ref<any>(null)
const msgBox = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLElement | null>(null)
const searchQuery = ref("")
const historyList = ref<any[]>([])
const currentConvId = ref<string | null>(null)
const currentTitle = ref("")

const quickQuestions = ["项目有哪些功能？", "智云音箱 Pro 有吗？", "如何使用 RAG 系统？"]

onMounted(async () => {
  await refreshInfo()
  await loadHistory()
})

const filteredHistory = computed(() => {
  if (!searchQuery.value) return historyList.value
  const q = searchQuery.value.toLowerCase()
  return historyList.value.filter((h: any) => (h.title || "").toLowerCase().includes(q))
})

function timeAgo(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "刚刚"
  if (mins < 60) return mins + "分钟前"
  const hours = Math.floor(mins / 60)
  if (hours < 24) return hours + "小时前"
  return d.toLocaleDateString("zh-CN")
}

async function refreshInfo() {
  try { info.value = await getInfo() } catch {}
}

async function loadHistory() {
  try {
    historyList.value = await getConversations()
  } catch {}
}

async function loadConversation(id: string) {
  currentConvId.value = id
  try {
    const data = await getConversation(id)
    messages.value = data.messages || []
    const conv = historyList.value.find((h: any) => h.id === id)
    currentTitle.value = conv?.title || ""
    nextTick(() => msgBox.value?.scrollTo({ top: msgBox.value.scrollHeight, behavior: "smooth" }))
  } catch {}
}

async function delConversation(id: string) {
  try {
    await deleteConversation(id)
    historyList.value = historyList.value.filter((h: any) => h.id !== id)
    if (currentConvId.value === id) {
      currentConvId.value = null
      messages.value = []
      currentTitle.value = ""
    }
  } catch {}
}

function newChat() {
  currentConvId.value = null
  messages.value = []
  currentTitle.value = ""
  question.value = ""
}

function askQuick(q: string) {
  question.value = q
  send()
}

async function send() {
  const q = question.value.trim()
  if (!q || loading.value) return
  question.value = ""
  messages.value.push({ role: "user", content: q })
  loading.value = true

  try {
    const r = await chat(q)
    messages.value.push({
      role: "assistant",
      content: r.answer,
      sources: r.sources,
      latency_ms: r.latency_ms,
      model_used: r.model,
    })
    // 自动保存对话
    await saveConversation({
      id: currentConvId.value || undefined,
      title: messages.value[0]?.content?.slice(0, 30) || "新对话",
      messages: messages.value.map((m) => ({
        role: m.role,
        content: m.content,
        sources: m.sources,
      })),
    })
    await loadHistory()
    if (!currentConvId.value && historyList.value.length > 0) {
      currentConvId.value = historyList.value[0].id
    }
  } catch {
    messages.value.push({
      role: "assistant",
      content: "抱歉，发生了错误。请确认后端服务是否正常运行。",
    })
  }
  loading.value = false
  nextTick(() => msgBox.value?.scrollTo({ top: msgBox.value.scrollHeight, behavior: "smooth" }))
}

function triggerUpload() {
  fileInput.value?.click()
}

async function handleUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return
  try {
    await uploadDocument(file)
    await reloadVectorStore()
    await refreshInfo()
  } catch {}
  input.value = ""
}

function renderMarkdown(text: string): string {
  if (!text) return ""
  // 简单的 markdown 渲染
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/\n/g, "<br/>")
  return html
}
</script>

<style scoped>
.chat-page {
  display: flex;
  flex: 1;
  height: 100vh;
  overflow: hidden;
}

/* ===== 左侧历史侧边栏 ===== */
.history-sidebar {
  width: 280px;
  min-width: 280px;
  background: #f8f9fc;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}
.sidebar-header {
  padding: 20px 16px 12px;
  border-bottom: 1px solid #e5e7eb;
}
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.logo-icon {
  color: #6366f1;
  font-size: 20px;
}
.logo-text {
  font-weight: 700;
  font-size: 16px;
  color: #1f2937;
}
.btn-new-chat {
  width: 100%;
  padding: 8px 16px;
  background: #6366f1;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-new-chat:hover { background: #4f46e5; }
.search-box {
  padding: 12px 16px;
}
.search-box input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: #fff;
}
.search-box input:focus { border-color: #6366f1; }
.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}
.history-item {
  position: relative;
  padding: 10px 12px;
  margin: 2px 0;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.history-item:hover { background: #eef2ff; }
.history-item.active { background: #e0e7ff; }
.history-item-title {
  font-size: 14px;
  color: #1f2937;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 24px;
}
.history-item-meta {
  font-size: 11px;
  color: #9ca3af;
  display: flex;
  gap: 8px;
}
.btn-delete {
  position: absolute;
  top: 10px;
  right: 8px;
  width: 20px;
  height: 20px;
  border: none;
  background: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 12px;
  border-radius: 4px;
  display: none;
  align-items: center;
  justify-content: center;
}
.history-item:hover .btn-delete { display: flex; }
.btn-delete:hover { color: #ef4444; background: #fee2e2; }
.history-empty {
  padding: 24px 16px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}

/* ===== 右侧聊天主区域 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}
.chat-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}
.topbar-title {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sys-badge {
  font-size: 11px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 3px 10px;
  border-radius: 12px;
}
.btn-icon {
  width: 32px;
  height: 32px;
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.btn-icon:hover { border-color: #6366f1; color: #6366f1; }

/* ===== 消息区域 ===== */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #fafafa;
}
.empty-state {
  text-align: center;
  padding: 80px 20px 40px;
  color: #6b7280;
}
.empty-icon { font-size: 56px; margin-bottom: 16px; }
.empty-state h3 { color: #1f2937; margin-bottom: 8px; font-size: 18px; }
.empty-state p { color: #6b7280; margin-bottom: 20px; }
.suggestions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.suggestion-chip {
  padding: 6px 14px;
  background: #eef2ff;
  color: #6366f1;
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.suggestion-chip:hover { background: #6366f1; color: #fff; }

.msg {
  display: flex;
  gap: 12px;
  max-width: 85%;
}
.msg.user { align-self: flex-end; flex-direction: row-reverse; }
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.bubble {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  min-width: 80px;
}
.msg.user .bubble {
  background: #6366f1;
  color: #fff;
  border-color: #6366f1;
}
.content { font-size: 14px; line-height: 1.7; }
.msg.user .content { color: #fff; }

/* 来源引用 */
.sources { margin-top: 12px; padding-top: 10px; border-top: 1px solid #e5e7eb; }
.msg.user .sources { border-top-color: rgba(255,255,255,0.2); }
.sources-label { font-size: 12px; color: #6366f1; font-weight: 600; margin-bottom: 6px; }
.source-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-size: 12px;
  color: #6b7280;
}
.source-badge {
  background: #eef2ff;
  color: #6366f1;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 11px;
  white-space: nowrap;
}
.source-score { color: #9ca3af; white-space: nowrap; }
.source-preview { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #9ca3af; }
.msg-meta { font-size: 11px; color: #9ca3af; margin-top: 6px; }

/* 加载动画 */
.loading-dots { display: flex; align-items: center; gap: 2px; color: #6b7280; }
.dot { animation: blink 1.4s infinite; font-size: 20px; line-height: 0; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
.dot:nth-child(4) { animation-delay: 0.6s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0; } 40% { opacity: 1; } }

/* ===== 输入区 ===== */
.input-area {
  border-top: 1px solid #e5e7eb;
  padding: 16px 24px;
  background: #fff;
}
.input-wrapper {
  display: flex;
  gap: 8px;
  align-items: center;
  background: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 4px 4px 4px 16px;
  transition: border-color 0.15s;
}
.input-wrapper:focus-within { border-color: #6366f1; }
.input-wrapper input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  outline: none;
  padding: 10px 0;
  color: #1f2937;
}
.input-wrapper input::placeholder { color: #9ca3af; }
.btn-upload {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.btn-upload:hover { background: #f3f4f6; }
.btn-send {
  padding: 8px 20px;
  background: #6366f1;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}
.btn-send:hover { background: #4f46e5; }
.btn-send:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
