<template>
  <div id="app">
    <nav class="top-nav">
      <router-link to="/">💬 问答</router-link>
      <router-link to="/admin">⚙️ 管理</router-link>
    </nav>
    <router-view />
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif; background: #f5f5f5; color: #1f2937; }
#app { min-height: 100vh; display: flex; flex-direction: column; }
.top-nav { display: flex; gap: 16px; padding: 12px 24px; background: #6366f1; }
.top-nav a { color: #fff; text-decoration: none; font-size: 14px; padding: 4px 12px; border-radius: 4px; }
.top-nav a:hover { background: rgba(255,255,255,0.15); }
.top-nav a.router-link-exact-active { background: rgba(255,255,255,0.25); }
</style>