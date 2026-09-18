<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'
import { sessionState } from '../session'

const loading = ref(false)
const form = reactive({ operatorName: sessionState.operatorName, apiKey: '' })

async function submit() {
  if (!form.operatorName.trim() || !form.apiKey.trim()) {
    ElMessage.warning('请填写操作人名称和 API Key')
    return
  }
  loading.value = true
  try {
    const data = await api.createSession(form.operatorName, form.apiKey)
    localStorage.setItem('voc_operator_name', data.operator_name)
    sessionState.operatorName = data.operator_name
    sessionState.ready = true
    form.apiKey = ''
    ElMessage.success('系统初始化完成')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '初始化失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="init-page">
    <section class="intro-panel">
      <div class="intro-content">
        <div class="eyebrow">VOICE OF CUSTOMER</div>
        <h1>让每一条反馈<br />都变成可处理的问题</h1>
        <p>集中收集、智能分析并持续跟踪客户反馈，帮助售后和产品团队看清真正需要解决的问题。</p>
        <div class="feature-row"><span>结构化分析</span><span>相似问题归并</span><span>处理闭环</span></div>
      </div>
    </section>
    <section class="setup-panel">
      <div class="setup-card">
        <div class="setup-icon">V</div>
        <h2>初始化工作台</h2>
        <p class="muted">无需注册或登录，填写本次操作署名和 DeepSeek API Key 即可开始。</p>
        <el-form label-position="top" size="large" @submit.prevent="submit">
          <el-form-item label="当前操作人名称">
            <el-input v-model="form.operatorName" maxlength="50" placeholder="例如：产品团队" />
          </el-form-item>
          <el-form-item label="DeepSeek API Key">
            <el-input v-model="form.apiKey" type="password" show-password placeholder="sk-..." />
          </el-form-item>
          <el-alert title="API Key 仅保存在后端内存，空闲 8 小时或服务重启后自动清除。" type="info" :closable="false" show-icon />
          <el-button class="start-button" type="primary" :loading="loading" @click="submit">进入工作台</el-button>
        </el-form>
        <p class="trust-note">本系统不提供身份认证，请仅在可信内部网络中部署。</p>
      </div>
    </section>
  </div>
</template>

