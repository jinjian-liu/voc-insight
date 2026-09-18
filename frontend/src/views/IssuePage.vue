<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { api, type Issue, type IssueDetail } from '../api'

const loading = ref(false)
const items = ref<Issue[]>([])
const total = ref(0)
const drawerVisible = ref(false)
const completeVisible = ref(false)
const selected = ref<IssueDetail | null>(null)
const solution = ref('')
const filters = reactive({ keyword: '', status: '' })
const severityLabels: Record<string, string> = { low: '低', medium: '中', high: '高', urgent: '紧急' }

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.keyword.trim()) params.set('keyword', filters.keyword.trim())
    if (filters.status) params.set('status', filters.status)
    const data = await api.listIssues(params)
    items.value = data.items
    total.value = data.total
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '加载失败') }
  finally { loading.value = false }
}

async function openDetail(issue: Issue) {
  selected.value = await api.getIssue(issue.id)
  drawerVisible.value = true
}

function openComplete() {
  solution.value = selected.value?.solution || ''
  completeVisible.value = true
}

async function complete() {
  if (!selected.value || !solution.value.trim()) return ElMessage.warning('请填写处理结果')
  await api.completeIssue(selected.value.id, solution.value)
  completeVisible.value = false
  ElMessage.success('问题已完成处理')
  selected.value = await api.getIssue(selected.value.id)
  await load()
}

async function remove(issue: Issue) {
  await ElMessageBox.confirm('删除后问题将不再出现在列表和统计中，是否继续？', '删除问题', { type: 'warning' })
  await api.deleteIssue(issue.id)
  drawerVisible.value = false
  ElMessage.success('问题已删除')
  await load()
}

function formatTime(value: string | null) { return value ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '—' }
onMounted(load)
</script>

<template>
  <div>
    <div class="page-heading"><div><div class="eyebrow dark">ISSUES</div><h1>问题管理</h1><p>汇总相似反馈，跟踪问题从发现到处理完成的过程。</p></div><el-tag type="info" effect="plain">共 {{ total }} 个问题</el-tag></div>
    <section class="content-card">
      <div class="toolbar"><el-input v-model="filters.keyword" :prefix-icon="Search" clearable placeholder="搜索问题标题或描述" @keyup.enter="load" @clear="load" /><el-select v-model="filters.status" clearable placeholder="全部状态" @change="load"><el-option label="待处理" value="pending" /><el-option label="已处理" value="processed" /></el-select><el-button @click="load">查询</el-button></div>
      <el-table v-loading="loading" :data="items" empty-text="暂无问题，请先从反馈分析结果创建" @row-dblclick="openDetail">
        <el-table-column label="编号" width="90"><template #default="scope">IS-{{ String(scope.row.id).padStart(4, '0') }}</template></el-table-column>
        <el-table-column prop="title" label="问题标题" min-width="300" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="130" />
        <el-table-column label="严重程度" width="100"><template #default="scope"><el-tag :type="scope.row.severity === 'urgent' || scope.row.severity === 'high' ? 'danger' : 'info'" effect="plain">{{ severityLabels[scope.row.severity] }}</el-tag></template></el-table-column>
        <el-table-column prop="priority" label="优先级" width="90" />
        <el-table-column label="状态" width="100"><template #default="scope"><el-tag :type="scope.row.status === 'processed' ? 'success' : 'warning'">{{ scope.row.status === 'processed' ? '已处理' : '待处理' }}</el-tag></template></el-table-column>
        <el-table-column prop="feedback_count" label="反馈数" width="85" />
        <el-table-column label="处理者" width="110"><template #default="scope">{{ scope.row.processed_by_name || '—' }}</template></el-table-column>
        <el-table-column label="操作" width="110" fixed="right"><template #default="scope"><el-button link type="primary" @click="openDetail(scope.row)">查看详情</el-button></template></el-table-column>
      </el-table>
    </section>

    <el-drawer v-model="drawerVisible" title="问题详情" size="720px">
      <template v-if="selected">
        <div class="issue-title-row"><div><span class="issue-id">IS-{{ String(selected.id).padStart(4, '0') }}</span><h2>{{ selected.title }}</h2></div><el-tag :type="selected.status === 'processed' ? 'success' : 'warning'" size="large">{{ selected.status === 'processed' ? '已处理' : '待处理' }}</el-tag></div>
        <div class="issue-meta"><span>分类：{{ selected.category }}</span><span>严重程度：{{ severityLabels[selected.severity] }}</span><span>优先级：{{ selected.priority }}</span><span>关联反馈：{{ selected.feedback_count }}</span></div>
        <section class="detail-section"><h3>问题描述</h3><p>{{ selected.description }}</p></section>
        <section v-if="selected.solution" class="solution-box"><h3>处理结果</h3><p>{{ selected.solution }}</p><small>{{ selected.processed_by_name }} · {{ formatTime(selected.processed_at) }}</small></section>
        <section class="detail-section"><h3>关联反馈</h3><div v-for="feedback in selected.feedbacks" :key="feedback.id" class="linked-feedback"><strong>FB-{{ String(feedback.id).padStart(4, '0') }}</strong><span>{{ feedback.content }}</span></div></section>
        <section class="detail-section"><h3>操作记录</h3><el-timeline><el-timeline-item v-for="activity in selected.activities" :key="activity.id" :timestamp="formatTime(activity.created_at)"><strong>{{ activity.operator_name }}</strong> · {{ activity.comment }}</el-timeline-item></el-timeline></section>
        <div class="drawer-footer"><el-button type="danger" plain @click="remove(selected)">删除问题</el-button><el-button v-if="selected.status !== 'processed'" type="primary" @click="openComplete">完成处理</el-button></div>
      </template>
    </el-drawer>

    <el-dialog v-model="completeVisible" title="填写处理结果" width="560px"><el-input v-model="solution" type="textarea" :rows="6" maxlength="5000" show-word-limit placeholder="说明解决方案、处理结论或无需继续处理的原因" /><template #footer><el-button @click="completeVisible = false">取消</el-button><el-button type="primary" @click="complete">提交并标记已处理</el-button></template></el-dialog>
  </div>
</template>

