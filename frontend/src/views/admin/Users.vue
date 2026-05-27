<template>
  <div>
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showDialog()"><el-icon><Plus /></el-icon>添加用户</el-button>
    </div>

    <el-card style="margin-bottom:20px">
      <el-row :gutter="16">
        <el-col :span="5">
          <el-select v-model="filters.role" placeholder="角色筛选" clearable style="width:100%" @change="load">
            <el-option label="管理员" value="admin" /><el-option label="教师" value="teacher" /><el-option label="学生" value="student" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input v-model="filters.keyword" placeholder="搜索姓名/学号" clearable @change="load" prefix-icon="Search" />
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="users" stripe>
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{row}">
          <el-tag :type="roleTag(row.role)" size="small" round>{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="student_no" label="学号" width="130" />
      <el-table-column prop="department" label="院系/班级" width="160" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="phone" label="电话" width="130" />
      <el-table-column prop="created_at" label="注册时间" width="170" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{row}">
          <el-button size="small" text type="primary" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确认删除该用户？" @confirm="handleDelete(row.id)">
            <template #reference><el-button size="small" text type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑用户':'添加用户'" width="520px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名" v-if="!isEdit"><el-input v-model="form.username" placeholder="登录用户名" /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.real_name" placeholder="真实姓名" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" :placeholder="isEdit?'不修改请留空':'设置密码'" show-password /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="管理员" value="admin" /><el-option label="教师" value="teacher" /><el-option label="学生" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item label="学号"><el-input v-model="form.student_no" placeholder="仅学生需填" /></el-form-item>
        <el-form-item label="院系"><el-input v-model="form.department" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
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
import { userApi, authApi } from '../../api'
import { ElMessage } from 'element-plus'

const users = ref([])
const filters = reactive({ role: null, keyword: '' })
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = reactive({ username: '', real_name: '', password: '', role: 'student', student_no: '', department: '', email: '', phone: '' })

const roleTag = r => ({ admin: 'danger', teacher: 'warning', student: 'success' }[r] || 'info')
const roleLabel = r => ({ admin: '管理员', teacher: '教师', student: '学生' }[r] || r)

const load = async () => { const res = await userApi.getList(filters); users.value = res.data }

const showDialog = (u) => {
  if (u) {
    isEdit.value = true; editId.value = u.id
    Object.assign(form, { ...u, password: '' })
  } else {
    isEdit.value = false; editId.value = null
    Object.assign(form, { username: '', real_name: '', password: '', role: 'student', student_no: '', department: '', email: '', phone: '' })
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (isEdit.value) {
    const data = { ...form }
    if (!data.password) delete data.password
    await userApi.update(editId.value, data)
    ElMessage.success('更新成功')
  } else {
    await authApi.register(form)
    ElMessage.success('添加成功')
  }
  dialogVisible.value = false
  load()
}

const handleDelete = async (id) => { await userApi.delete(id); ElMessage.success('删除成功'); load() }

onMounted(load)
</script>
