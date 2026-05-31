<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <h3>管理后台</h3>
      <a href="/admin" class="active">📊 概览</a>
      <a href="/">💬 返回问答</a>
    </aside>
    <main class="admin-main">
      <div class="card">
        <h3>系统概览</h3>
        <div v-if="info" class="info-grid">
          <div class="info-item"><label>向量存储</label><span>{{ info.vector_store }}</span></div>
          <div class="info-item"><label>Chunks</label><span>{{ info.chunks }}</span></div>
          <div class="info-item"><label>LLM</label><span>{{ info.llm }}</span></div>
          <div class="info-item"><label>嵌入模型</label><span>{{ info.emb }}</span></div>
          <div class="info-item"><label>缓存</label><span>{{ info.cache }}</span></div>
        </div>
        <p v-else class="loading">加载中...</p>
      </div>
      <div class="card">
        <h3>快速操作</h3>
        <p style="color:#6b7280;font-size:14px;">Django Admin: <a :href="adminUrl" target="_blank">{{ adminUrl }}</a></p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { getInfo } from "../api"

const info = ref<any>(null)
const adminUrl = ref("http://localhost:18762/admin/")

onMounted(async () => {
  try { info.value = await getInfo() } catch {}
})
</script>

<style scoped>
.admin-layout { display: flex; flex: 1; }
.sidebar { width: 200px; background: #1f2937; color: #fff; padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.sidebar h3 { font-size: 16px; margin-bottom: 16px; }
.sidebar a { color: #9ca3af; text-decoration: none; padding: 8px 12px; border-radius: 6px; font-size: 14px; }
.sidebar a:hover, .sidebar a.active { color: #fff; background: rgba(255,255,255,0.1); }
.admin-main { flex: 1; padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.card { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.card h3 { margin-bottom: 16px; font-size: 16px; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item { display: flex; justify-content: space-between; padding: 8px 12px; background: #f9fafb; border-radius: 6px; font-size: 14px; }
.info-item label { color: #6b7280; }
.loading { color: #6b7280; }
.card a { color: #6366f1; }
</style>
