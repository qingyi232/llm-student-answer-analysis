<template>
  <div>
    <div class="page-header">
      <h2>我的作业</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="8" v-for="a in assignments" :key="a.id" style="margin-bottom:20px">
        <el-card :body-style="{padding:'20px'}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
            <h3 style="font-size:16px;font-weight:600;flex:1">{{ a.title }}</h3>
            <el-tag v-if="a.is_submitted" type="success" size="small" round>已提交</el-tag>
            <el-tag v-else type="warning" size="small" round>待完成</el-tag>
          </div>
          <div style="font-size:13px;color:var(--text-muted);margin-bottom:8px">
            <el-icon><Reading /></el-icon> {{ a.course_name }}
          </div>
          <div style="font-size:13px;color:var(--text-muted);margin-bottom:8px">
            <el-icon><Notebook /></el-icon> 共 {{ a.question_count }} 道题
          </div>
          <div style="font-size:13px;margin-bottom:16px" :style="{color: isOverdue(a.deadline)?'#c62828':'var(--text-muted)'}">
            <el-icon><Clock /></el-icon> 截止: {{ a.deadline || '无限制' }}
            <span v-if="isOverdue(a.deadline)" style="font-size:12px"> (已截止)</span>
          </div>
          <p style="font-size:13px;color:var(--text-secondary);margin-bottom:16px">{{ a.description }}</p>
          <el-button type="primary" style="width:100%" @click="goAnswer(a)">
            {{ a.is_submitted ? '查看/修改' : '开始答题' }}
          </el-button>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!assignments.length" description="暂无作业" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { assignmentApi } from '../../api'

const router = useRouter()
const assignments = ref([])

const isOverdue = (deadline) => {
  if (!deadline) return false
  return new Date(deadline) < new Date()
}

const goAnswer = (a) => { router.push(`/answer/${a.id}`) }

onMounted(async () => {
  const res = await assignmentApi.getList()
  assignments.value = res.data
})
</script>
