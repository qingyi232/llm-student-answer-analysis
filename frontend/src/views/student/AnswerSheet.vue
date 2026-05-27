<template>
  <div>
    <div class="page-header">
      <div>
        <h2>{{ assignment?.title || '答题' }}</h2>
        <p style="font-size:13px;color:var(--text-muted);margin-top:4px">{{ assignment?.course_name }} · 截止时间: {{ assignment?.deadline || '无限制' }}</p>
      </div>
      <el-button @click="$router.push('/student-assignments')"><el-icon><ArrowLeft /></el-icon>返回</el-button>
    </div>

    <div v-if="assignment?.description" style="background:#f0f8f5;padding:14px 20px;border-radius:8px;margin-bottom:24px;font-size:14px;color:var(--text-secondary)">
      {{ assignment.description }}
    </div>

    <div v-for="(q, idx) in questions" :key="q.id" style="margin-bottom:24px">
      <el-card>
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">
          <div>
            <span style="font-size:16px;font-weight:600;color:var(--primary)">第{{ idx+1 }}题</span>
            <el-tag :type="typeTag(q.question_type)" size="small" style="margin-left:8px" round>{{ q.question_type }}</el-tag>
            <el-tag size="small" effect="plain" style="margin-left:4px">{{ q.max_score }}分</el-tag>
          </div>
          <div>
            <el-tag v-for="kp in (q.knowledge_points||[]).slice(0,3)" :key="kp" size="small" type="info" effect="plain" style="margin-left:4px" round>{{ kp }}</el-tag>
          </div>
        </div>
        <div style="font-size:15px;line-height:1.8;margin-bottom:16px;color:var(--text-primary)">{{ q.content }}</div>
        <el-input
          v-model="answerMap[q.id]"
          type="textarea"
          :rows="6"
          :placeholder="'请在此作答...'"
          show-word-limit
          maxlength="3000"
        />
        <div style="display:flex;justify-content:space-between;margin-top:8px">
          <span style="font-size:12px;color:var(--text-muted)">已输入 {{ (answerMap[q.id]||'').length }} 字</span>
        </div>
      </el-card>
    </div>

    <div style="text-align:center;padding:20px 0" v-if="questions.length">
      <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit" style="padding:12px 60px;font-size:16px">
        提交作业
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { assignmentApi, answerApi } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const assignment = ref(null)
const questions = ref([])
const answerMap = reactive({})
const submitting = ref(false)

const typeTag = t => ({ '论述题': 'danger', '简答题': 'warning', '案例分析题': '' }[t] || 'info')

onMounted(async () => {
  const res = await assignmentApi.getDetail(route.params.assignmentId)
  assignment.value = res.data
  questions.value = res.data.questions || []

  const ansRes = await answerApi.getList({ assignment_id: route.params.assignmentId })
  if (ansRes.data) {
    ansRes.data.forEach(a => { answerMap[a.question_id] = a.answer_content })
  }
})

const handleSubmit = async () => {
  const unanswered = questions.value.filter(q => !answerMap[q.id]?.trim())
  if (unanswered.length) {
    try {
      await ElMessageBox.confirm(`还有 ${unanswered.length} 道题未作答，确认提交吗？`, '提示', { type: 'warning' })
    } catch { return }
  }

  submitting.value = true
  try {
    const answers = questions.value
      .filter(q => answerMap[q.id]?.trim())
      .map(q => ({
        question_id: q.id,
        assignment_id: parseInt(route.params.assignmentId),
        answer_content: answerMap[q.id]
      }))
    await answerApi.batchSubmit({ answers })
    ElMessage.success('提交成功')
    router.push('/student-assignments')
  } finally { submitting.value = false }
}
</script>
