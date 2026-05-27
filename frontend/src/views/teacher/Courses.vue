<template>
  <div>
    <div class="page-header">
      <h2>课程管理</h2>
      <el-button type="primary" @click="showDialog()"><el-icon><Plus /></el-icon>新建课程</el-button>
    </div>
    <el-row :gutter="20">
      <el-col :span="8" v-for="c in courses" :key="c.id" style="margin-bottom:20px">
        <el-card :body-style="{padding:0}">
          <img :src="c.cover_url || 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400&h=180&fit=crop'" style="width:100%;height:160px;object-fit:cover;border-radius:10px 10px 0 0" />
          <div style="padding:16px 20px">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
              <h3 style="font-size:16px;font-weight:600;flex:1">{{ c.name }}</h3>
              <el-tag size="small" type="success" round>{{ c.subject }}</el-tag>
            </div>
            <p style="font-size:13px;color:var(--text-muted);margin-bottom:12px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{{ c.description }}</p>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-size:12px;color:var(--text-muted)">{{ c.student_count }} 名学生 · {{ c.code }}</span>
              <div>
                <el-button size="small" text type="primary" @click="showDialog(c)">编辑</el-button>
                <el-popconfirm title="确认删除此课程？" @confirm="handleDelete(c.id)">
                  <template #reference><el-button size="small" text type="danger">删除</el-button></template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑课程':'新建课程'" width="520px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="课程名称"><el-input v-model="form.name" placeholder="请输入课程名称" /></el-form-item>
        <el-form-item label="课程编号"><el-input v-model="form.code" placeholder="如 YW-2026-01" /></el-form-item>
        <el-form-item label="所属学科">
          <el-select v-model="form.subject" placeholder="选择学科" style="width:100%">
            <el-option label="语文" value="语文" /><el-option label="数学" value="数学" />
            <el-option label="历史" value="历史" /><el-option label="地理" value="地理" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程描述"><el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入课程描述" /></el-form-item>
        <el-form-item label="封面图片"><el-input v-model="form.cover_url" placeholder="请输入封面图片URL" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { courseApi } from '../../api'
import { ElMessage } from 'element-plus'

const courses = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = reactive({ name: '', code: '', subject: '', description: '', cover_url: '' })

const load = async () => { const res = await courseApi.getList(); courses.value = res.data }

const showDialog = (c) => {
  if (c) {
    isEdit.value = true; editId.value = c.id
    Object.assign(form, { name: c.name, code: c.code, subject: c.subject, description: c.description, cover_url: c.cover_url })
  } else {
    isEdit.value = false; editId.value = null
    Object.assign(form, { name: '', code: '', subject: '', description: '', cover_url: '' })
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (isEdit.value) {
    await courseApi.update(editId.value, form)
    ElMessage.success('更新成功')
  } else {
    await courseApi.create(form)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
}

const handleDelete = async (id) => { await courseApi.delete(id); ElMessage.success('删除成功'); load() }

onMounted(load)
</script>
