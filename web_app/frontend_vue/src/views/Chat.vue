<template>
  <div class="chat-layout">
    <div class="chat-main">
      <div class="chat-topbar">
        <span class="logo">RAG 问答</span>
        <span class="sys-info" v-if="info">{{ info.llm }} · {{ info.vector_store }} · {{ info.cache }}</span>
      </div>
      <div class="messages" ref="msgBox">
        <div v-if="!messages.length && !loading" class="empty-state">
          <div class="empty-icon">📚</div>
          <h3>有什么可以帮你的？</h3>
          <p>基于知识库智能问答，输入问题开始对话</p>
        </div>
        <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
          <div class="avatar">{{ m.role === "user" ? "👤" : "🤖" }}</div>
          <div class="bubble">
            <div class="content" style="white-space:pre-wrap">{{ m.content }}</div>
            <div v-if="m.sources?.length" class="sources">
              <div v-for="(s, j) in m.sources" :key="j" class="source-tag">来源 {{ j+1 }} ({{ (s.score*100).toFixed(0) }}%)</div>
            </div>
          </div>
        </div>
        <div v-if="loading" class="msg assistant">
          <div class="avatar">🤖</div>
          <div class="bubble"><div class="content">正在检索知识...</div></div>
        </div>
      </div>
      <div class="input-area">
        <form @submit.prevent="send">
          <input v-model="question" placeholder="请输入您的问题..." :disabled="loading" />
          <button type="submit" :disabled="loading || !question.trim()">发送</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from "vue"
import { chat, getInfo } from "../api"

const question = ref("")
const messages = ref<any[]>([])
const loading = ref(false)
const info = ref<any>(null)
const msgBox = ref<HTMLElement | null>(null)

onMounted(async () => {
  try { info.value = await getInfo() } catch {}
})

async function send() {
  const q = question.value.trim()
  if (!q || loading.value) return
  question.value = ""
  messages.value.push({ role: "user", content: q })
  loading.value = true
  try {
    const r = await chat(q)
    messages.value.push({ role: "assistant", content: r.answer, sources: r.sources })
  } catch {
    messages.value.push({ role: "assistant", content: "抱歉，发生了错误。请确认后端服务是否正常运行。" })
  }
  loading.value = false
  nextTick(() => msgBox.value?.scrollTo({ top: msgBox.value.scrollHeight, behavior: "smooth" }))
}
</script>

<style scoped>
.chat-layout { flex: 1; display: flex; justify-content: center; padding: 20px; }
.chat-main { width: 100%; max-width: 800px; display: flex; flex-direction: column; background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.chat-topbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #e5e7eb; }
.logo { font-weight: 600; font-size: 16px; }
.sys-info { font-size: 12px; color: #6b7280; }
.messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; min-height: 400px; max-height: 60vh; }
.empty-state { text-align: center; padding: 60px 20px; color: #6b7280; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state h3 { color: #1f2937; margin-bottom: 8px; }
.msg { display: flex; gap: 10px; max-width: 80%; }
.msg.user { align-self: flex-end; flex-direction: row-reverse; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: #f3f4f6; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.bubble { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.msg.user .bubble { background: #6366f1; color: #fff; border-color: #6366f1; }
.content { font-size: 14px; line-height: 1.6; }
.sources { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px; }
.source-tag { font-size: 11px; color: #6366f1; background: #eef2ff; padding: 2px 8px; border-radius: 4px; }
.input-area { border-top: 1px solid #e5e7eb; padding: 16px 20px; }
.input-area form { display: flex; gap: 8px; }
.input-area input { flex: 1; padding: 10px 14px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; outline: none; }
.input-area input:focus { border-color: #6366f1; }
.input-area button { padding: 10px 24px; background: #6366f1; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; white-space: nowrap; }
.input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
