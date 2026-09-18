<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, type Category } from '../api'

const items = ref<Category[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', description: '' })

async function load() { items.value = await api.listCategories() }
function openCreate() { editingId.value = null; Object.assign(form, { name: '', description: '' }); dialogVisible.value = true }
function openEdit(item: Category) { editingId.value = item.id; Object.assign(form, { name: item.name, description: item.description || '' }); dialogVisible.value = true }
async function save() {
  if (!form.name.trim()) return ElMessage.warning('请输入分类名称')
  if (editingId.value) await api.updateCategory(editingId.value, form)
  else await api.createCategory(form)
  dialogVisible.value = false
  ElMessage.success('分类已保存')
  await load()
}
async function remove(item: Category) {
  await ElMessageBox.confirm(`确定删除分类“${item.name}”吗？历史数据中的分类名称不会改变。`, '删除分类', { type: 'warning' })
  await api.deleteCategory(item.id)
  await load()
}
onMounted(load)
</script>

<template>
  <div><div class="page-heading"><div><div class="eyebrow dark">SETTINGS</div><h1>系统设置</h1><p>维护 AI 分析可以使用的问题分类。</p></div><el-button type="primary" :icon="Plus" @click="openCreate">新增分类</el-button></div>
    <section class="content-card settings-card"><div class="settings-title"><h2>问题分类</h2><span>AI 只会从启用的分类及“其他/待确认”中选择</span></div><el-table :data="items"><el-table-column type="index" label="排序" width="80" /><el-table-column prop="name" label="分类名称" width="180" /><el-table-column prop="description" label="说明" min-width="360" /><el-table-column label="操作" width="150"><template #default="scope"><el-button link type="primary" @click="openEdit(scope.row)">编辑</el-button><el-button link type="danger" @click="remove(scope.row)">删除</el-button></template></el-table-column></el-table></section>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分类' : '新增分类'" width="500px"><el-form label-position="top"><el-form-item label="分类名称"><el-input v-model="form.name" maxlength="100" /></el-form-item><el-form-item label="分类说明"><el-input v-model="form.description" type="textarea" :rows="3" maxlength="300" /></el-form-item></el-form><template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template></el-dialog>
  </div>
</template>

