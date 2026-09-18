<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Plus, Search, Upload } from '@element-plus/icons-vue'
import type { UploadRequestOptions } from 'element-plus'
import { api, type Category, type Feedback, type Issue } from '../api'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const issueDialogVisible = ref(false)
const items = ref<Feedback[]>([])
const total = ref(0)
const selected = ref<Feedback | null>(null)
const categories = ref<Category[]>([])
const similarIssues = ref<Array<Issue & { similarity_score: number }>>([])
const filters = reactive({ keyword: '', source: '' })
const pagination = reactive({ page: 1, pageSize: 20 })
const form = reactive({ content: '', source: '售后记录', feedbackTime: new Date(), productModule: '', externalId: '', note: '' })
const analysisForm = reactive({ summary: '', category: '', subcategory: '', keywords: '', sentiment: 'negative', severity: 'medium', userImpact: '', priority: 'P2', confidence: 0, informationMissing: '' })
const issueForm = reactive({ title: '', description: '', category: '', severity: 'medium', priority: 'P2' })
const sourceOptions = ['售后记录', '客服工单', '访谈记录', '问卷反馈', '其他']
const severityLabels: Record<string, string> = { low: '低', medium: '中', high: '高', urgent: '紧急' }

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: String(pagination.page), page_size: String(pagination.pageSize) })
    if (filters.keyword.trim()) params.set('keyword', filters.keyword.trim())
    if (filters.source) params.set('source', filters.source)
    const data = await api.listFeedbacks(params)
    items.value = data.items
    total.value = data.total
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '加载失败') }
  finally { loading.value = false }
}

async function createFeedback() {
  if (!form.content.trim()) return ElMessage.warning('请输入反馈内容')
  saving.value = true
  try {
    const created = await api.createFeedback({ content: form.content, source: form.source, feedback_time: form.feedbackTime.toISOString(), product_module: form.productModule || null, external_id: form.externalId || null, note: form.note || null })
    dialogVisible.value = false
    Object.assign(form, { content: '', productModule: '', externalId: '', note: '', feedbackTime: new Date() })
    ElMessage.success('反馈已录入，正在启动智能分析')
    await load()
    await startAnalysis(created)
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '保存失败') }
  finally { saving.value = false }
}

async function startAnalysis(feedback: Feedback) {
  feedback.analysis_status = 'analyzing'
  try {
    await api.analyzeFeedback(feedback.id)
    ElMessage.success('AI 分析任务已启动')
    await waitForAnalysis(feedback.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '分析启动失败')
    await load()
  }
}

async function waitForAnalysis(id: number) {
  for (let attempt = 0; attempt < 45; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 1200))
    const feedback = await api.getFeedback(id)
    if (feedback.analysis_status === 'success') {
      ElMessage.success('AI 分析完成')
      await load()
      await openDetail(feedback)
      return
    }
    if (feedback.analysis_status === 'failed') {
      ElMessage.error('AI 分析失败，请检查 API Key 后重试')
      await load()
      return
    }
  }
  ElMessage.warning('分析仍在进行，可稍后刷新查看')
  await load()
}

async function openDetail(feedback: Feedback) {
  selected.value = await api.getFeedback(feedback.id)
  drawerVisible.value = true
  similarIssues.value = []
  const analysis = selected.value.analysis
  if (analysis) {
    Object.assign(analysisForm, { summary: analysis.summary, category: analysis.category, subcategory: analysis.subcategory || '', keywords: analysis.keywords.join('，'), sentiment: analysis.sentiment, severity: analysis.severity, userImpact: analysis.user_impact, priority: analysis.suggested_priority, confidence: analysis.confidence, informationMissing: analysis.information_missing.join('，') })
    similarIssues.value = await api.findSimilarIssues(analysis.summary, analysis.category)
  }
}

function analysisPayload() {
  return { summary: analysisForm.summary, category: analysisForm.category, subcategory: analysisForm.subcategory || null, keywords: analysisForm.keywords.split(/[，,]/).map(v => v.trim()).filter(Boolean), sentiment: analysisForm.sentiment, severity: analysisForm.severity, user_impact: analysisForm.userImpact, suggested_priority: analysisForm.priority, confidence: analysisForm.confidence, information_missing: analysisForm.informationMissing.split(/[，,]/).map(v => v.trim()).filter(Boolean), confirmed: true }
}

async function confirmAnalysis() {
  if (!selected.value) return
  try {
    await api.updateAnalysis(selected.value.id, analysisPayload())
    ElMessage.success('分析结果已确认')
    await openDetail(selected.value)
    await load()
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '保存失败') }
}

function openCreateIssue() {
  Object.assign(issueForm, { title: analysisForm.summary, description: analysisForm.userImpact, category: analysisForm.category, severity: analysisForm.severity, priority: analysisForm.priority })
  issueDialogVisible.value = true
}

async function createIssue() {
  if (!selected.value) return
  try {
    await api.createIssue({ feedback_id: selected.value.id, ...issueForm })
    issueDialogVisible.value = false
    drawerVisible.value = false
    ElMessage.success('问题已创建并关联当前反馈')
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '创建失败') }
}

async function linkIssue(issue: Issue) {
  if (!selected.value) return
  await api.linkFeedback(issue.id, selected.value.id)
  ElMessage.success(`已关联问题 IS-${String(issue.id).padStart(4, '0')}`)
  drawerVisible.value = false
}

async function deleteFeedback(feedback: Feedback) {
  await ElMessageBox.confirm('删除后反馈将不再出现在列表和统计中，是否继续？', '删除反馈', { type: 'warning' })
  await api.deleteFeedback(feedback.id)
  ElMessage.success('反馈已删除')
  await load()
}

async function importFile(options: UploadRequestOptions) {
  try {
    const result = await api.importFeedbacks(options.file)
    if (result.failed) ElMessage.warning(`成功导入 ${result.success} 条，失败 ${result.failed} 条：${result.errors.slice(0, 3).join('；')}`)
    else ElMessage.success(`成功导入 ${result.success} 条反馈`)
    await load()
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '导入失败') }
}

function formatTime(value: string) { return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }
function statusLabel(value: string) { return ({ pending: '待分析', analyzing: '分析中', success: '已分析', failed: '分析失败' } as Record<string, string>)[value] || value }
function statusType(value: string) { return ({ pending: 'warning', analyzing: 'primary', success: 'success', failed: 'danger' } as Record<string, string>)[value] || 'info' }

onMounted(async () => { categories.value = await api.listCategories(); await load() })
</script>

<template>
  <div>
    <div class="page-heading">
      <div><div class="eyebrow dark">FEEDBACK</div><h1>反馈管理</h1><p>录入原始反馈，通过 AI 形成结构化、可处理的问题。</p></div>
      <div class="heading-actions"><el-upload :show-file-list="false" accept=".csv,.xlsx" :http-request="importFile"><el-button :icon="Upload">批量导入</el-button></el-upload><el-button type="primary" :icon="Plus" @click="dialogVisible = true">录入反馈</el-button></div>
    </div>

    <section class="content-card">
      <div class="toolbar">
        <el-input v-model="filters.keyword" :prefix-icon="Search" clearable placeholder="搜索反馈内容或产品模块" @keyup.enter="load" @clear="load" />
        <el-select v-model="filters.source" clearable placeholder="全部来源" @change="load"><el-option v-for="option in sourceOptions" :key="option" :label="option" :value="option" /></el-select>
        <el-button @click="load">查询</el-button><span class="record-count">共 {{ total }} 条反馈</span>
      </div>
      <el-table v-loading="loading" :data="items" empty-text="还没有反馈，先录入第一条吧" @row-dblclick="openDetail">
        <el-table-column label="编号" width="90"><template #default="scope">FB-{{ String(scope.row.id).padStart(4, '0') }}</template></el-table-column>
        <el-table-column label="反馈内容" min-width="310" show-overflow-tooltip><template #default="scope"><div class="feedback-content">{{ scope.row.analysis?.summary || scope.row.content }}</div><small>{{ scope.row.product_module || '未指定模块' }}</small></template></el-table-column>
        <el-table-column prop="source" label="来源" width="110" />
        <el-table-column label="严重程度" width="100"><template #default="scope"><el-tag v-if="scope.row.analysis" :type="scope.row.analysis.severity === 'urgent' || scope.row.analysis.severity === 'high' ? 'danger' : 'info'" effect="plain">{{ severityLabels[scope.row.analysis.severity] }}</el-tag><span v-else>—</span></template></el-table-column>
        <el-table-column label="分析状态" width="110"><template #default="scope"><el-tag :type="statusType(scope.row.analysis_status)">{{ statusLabel(scope.row.analysis_status) }}</el-tag></template></el-table-column>
        <el-table-column label="反馈时间" width="170"><template #default="scope">{{ formatTime(scope.row.feedback_time) }}</template></el-table-column>
        <el-table-column label="操作" width="210" fixed="right"><template #default="scope"><el-button link type="primary" @click="openDetail(scope.row)">详情</el-button><el-button v-if="scope.row.analysis_status !== 'analyzing'" link type="primary" :icon="MagicStick" @click="startAnalysis(scope.row)">{{ scope.row.analysis ? '重新分析' : 'AI 分析' }}</el-button><el-button link type="danger" @click="deleteFeedback(scope.row)">删除</el-button></template></el-table-column>
      </el-table>
      <div class="pagination"><el-pagination v-model:current-page="pagination.page" :page-size="pagination.pageSize" :total="total" layout="prev, pager, next" @current-change="load" /></div>
    </section>

    <el-dialog v-model="dialogVisible" title="录入客户反馈" width="640px">
      <el-form label-position="top"><el-form-item label="反馈内容" required><el-input v-model="form.content" type="textarea" :rows="6" maxlength="10000" show-word-limit placeholder="粘贴原始反馈内容，不需要提前整理" /></el-form-item><div class="form-grid"><el-form-item label="来源"><el-select v-model="form.source"><el-option v-for="option in sourceOptions" :key="option" :label="option" :value="option" /></el-select></el-form-item><el-form-item label="反馈时间"><el-date-picker v-model="form.feedbackTime" type="datetime" /></el-form-item><el-form-item label="产品模块"><el-input v-model="form.productModule" placeholder="例如：数据导出" /></el-form-item><el-form-item label="外部记录编号"><el-input v-model="form.externalId" placeholder="选填" /></el-form-item></div><el-form-item label="备注"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item></el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="createFeedback">保存并分析</el-button></template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" title="反馈分析详情" size="680px">
      <template v-if="selected"><div class="raw-feedback"><span>原始反馈</span><p>{{ selected.content }}</p></div>
        <el-empty v-if="!selected.analysis" description="尚未生成 AI 分析"><el-button type="primary" @click="startAnalysis(selected)">开始分析</el-button></el-empty>
        <template v-else><el-form label-position="top" class="analysis-form"><el-form-item label="问题摘要"><el-input v-model="analysisForm.summary" /></el-form-item><div class="form-grid"><el-form-item label="问题分类"><el-select v-model="analysisForm.category"><el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.name" /><el-option label="其他/待确认" value="其他/待确认" /></el-select></el-form-item><el-form-item label="子分类"><el-input v-model="analysisForm.subcategory" /></el-form-item><el-form-item label="严重程度"><el-select v-model="analysisForm.severity"><el-option label="低" value="low" /><el-option label="中" value="medium" /><el-option label="高" value="high" /><el-option label="紧急" value="urgent" /></el-select></el-form-item><el-form-item label="建议优先级"><el-select v-model="analysisForm.priority"><el-option v-for="p in ['P0','P1','P2','P3']" :key="p" :label="p" :value="p" /></el-select></el-form-item></div><el-form-item label="关键词（逗号分隔）"><el-input v-model="analysisForm.keywords" /></el-form-item><el-form-item label="影响描述"><el-input v-model="analysisForm.userImpact" type="textarea" :rows="3" /></el-form-item><el-form-item label="缺失信息"><el-input v-model="analysisForm.informationMissing" /></el-form-item></el-form><div class="analysis-actions"><el-button @click="confirmAnalysis">保存并确认分析</el-button><el-button type="primary" @click="openCreateIssue">创建问题</el-button></div><el-divider content-position="left">相似问题推荐</el-divider><el-empty v-if="similarIssues.length === 0" description="暂无相似问题" :image-size="70" /><div v-for="issue in similarIssues" :key="issue.id" class="similar-issue"><div><strong>{{ issue.title }}</strong><p>{{ issue.category }} · {{ issue.feedback_count }} 条反馈 · 相似度 {{ Math.round(issue.similarity_score * 100) }}%</p></div><el-button size="small" @click="linkIssue(issue)">关联</el-button></div></template>
      </template>
    </el-drawer>

    <el-dialog v-model="issueDialogVisible" title="创建标准问题" width="620px"><el-form label-position="top"><el-form-item label="问题标题"><el-input v-model="issueForm.title" /></el-form-item><el-form-item label="问题描述"><el-input v-model="issueForm.description" type="textarea" :rows="4" /></el-form-item><div class="form-grid"><el-form-item label="分类"><el-select v-model="issueForm.category"><el-option v-for="item in categories" :key="item.id" :label="item.name" :value="item.name" /></el-select></el-form-item><el-form-item label="严重程度"><el-select v-model="issueForm.severity"><el-option v-for="(label, value) in severityLabels" :key="value" :label="label" :value="value" /></el-select></el-form-item><el-form-item label="优先级"><el-select v-model="issueForm.priority"><el-option v-for="p in ['P0','P1','P2','P3']" :key="p" :label="p" :value="p" /></el-select></el-form-item></div></el-form><template #footer><el-button @click="issueDialogVisible = false">取消</el-button><el-button type="primary" @click="createIssue">创建问题</el-button></template></el-dialog>
  </div>
</template>
