<template>
  <router-view />
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f5f5f5;
  color: #1f2937;
  -webkit-font-smoothing: antialiased;
}
#app { min-height: 100vh; display: flex; flex-direction: column; }

/* 滚动条美化 */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #9ca3af; }

/* 选中文本颜色 */
::selection { background: #6366f1; color: #fff; }

/* Markdown 基础样式 */
.markdown-body code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
  font-family: "Consolas", "Courier New", monospace;
}
.markdown-body pre {
  background: #1f2937;
  color: #f3f4f6;
  padding: 12px 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
  font-size: 13px;
  line-height: 1.5;
}
.markdown-body strong { font-weight: 600; }
.markdown-body li { margin-left: 1.5em; }
</style>
