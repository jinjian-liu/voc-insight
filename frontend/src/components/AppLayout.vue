<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataAnalysis, Document, Setting, Tickets } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'
import { sessionState } from '../session'

const route = useRoute()
const activeMenu = computed(() => route.path)

async function clearKey() {
  await ElMessageBox.confirm('清除后需要重新填写 DeepSeek API Key，是否继续？', '清除当前会话', {
    confirmButtonText: '确认清除', cancelButtonText: '取消', type: 'warning',
  })
  await api.clearSession()
  sessionState.ready = false
  ElMessage.success('当前会话已清除')
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">V</div>
        <div><strong>VoC Insight</strong><span>反馈管理工作台</span></div>
      </div>
      <el-menu :default-active="activeMenu" router class="nav-menu">
        <el-menu-item index="/feedbacks"><el-icon><Document /></el-icon><span>反馈管理</span></el-menu-item>
        <el-menu-item index="/issues"><el-icon><Tickets /></el-icon><span>问题管理</span></el-menu-item>
        <el-menu-item index="/dashboard"><el-icon><DataAnalysis /></el-icon><span>数据看板</span></el-menu-item>
        <el-menu-item index="/settings"><el-icon><Setting /></el-icon><span>系统设置</span></el-menu-item>
      </el-menu>
      <div class="sidebar-foot">MVP · 单企业内部版</div>
    </aside>
    <main class="main-area">
      <header class="topbar">
        <div class="environment"><span class="status-dot"></span>AI 会话已就绪</div>
        <div class="operator">
          <span>当前操作人：{{ sessionState.operatorName }}</span>
          <el-button text type="primary" @click="clearKey">清除 API Key</el-button>
        </div>
      </header>
      <div class="page-body"><router-view /></div>
    </main>
  </div>
</template>

