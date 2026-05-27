<template>
  <div>
    <div class="page-header">
      <h2>AI 智能批阅中心</h2>
    </div>

    <el-card style="margin-bottom:20px">
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <el-select v-model="filters.assignment_id" placeholder="选择作业" clearable style="width:100%" @change="loadAnswers">
            <el-option v-for="a in assignments" :key="a.id" :label="a.title" :value="a.id" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" :loading="batchLoading" :disabled="!unanalyzed.length" @click="batchAnalyze">
            <el-icon><Cpu /></el-icon> 一键批量分析 ({{ unanalyzed.length }})
          </el-button>
        </el-col>
        <el-col :span="4">
          <el-button type="success" :disabled="!answers.length" @click="handleExportCsv">
            <el-icon><Download /></el-icon> 导出结果
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="answers" stripe>
      <el-table-column prop="student_name" label="学生" width="100" />
      <el-table-column prop="student_no" label="学号" width="120" />
      <el-table-column prop="question_title" label="题目" min-width="180" show-overflow-tooltip />
      <el-table-column label="答案预览" min-width="200">
        <template #default="{row}">
          <span style="color:var(--text-secondary);font-size:13px">{{ row.answer_content?.substring(0,60) }}...</span>
        </template>
      </el-table-column>
      <el-table-column prop="word_count" label="字数" width="70" align="center" />
      <el-table-column label="AI评分" width="100" align="center">
        <template #default="{row}">
          <template v-if="row.analysis">
            <span class="score-badge" :class="scoreClass(row.analysis.overall_score)">{{ row.analysis.overall_score }}</span>
          </template>
          <span v-else style="color:var(--text-muted)">待分析</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{row}">
          <el-tag :type="statusType(row.status)" size="small" round>{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{row}">
          <el-button v-if="row.status==='submitted'" size="small" type="primary" @click="singleAnalyze(row)" :loading="row._loading">AI分析</el-button>
          <el-button v-if="row.analysis" size="small" text type="primary" @click="showResult(row)">查看结果</el-button>
          <el-button v-if="row.feedback && !row.feedback.is_teacher_reviewed" size="small" text type="warning" @click="showReview(row)">审核</el-button>
          <el-tag v-if="row.feedback?.is_teacher_reviewed" type="success" size="small">已审核</el-tag>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分析结果详情 -->
    <el-dialog v-model="resultVisible" title="AI 分析报告" width="800px">
      <template v-if="currentResult">
        <el-row :gutter="20" style="margin-bottom:20px">
          <el-col :span="6">
            <div class="stat-card" style="text-align:center">
              <div class="stat-value" style="font-size:36px">{{ currentResult.analysis.overall_score }}</div>
              <div class="stat-label">综合得分</div>
            </div>
          </el-col>
          <el-col :span="18">
            <div class="dimension-bar">
              <span class="label">知识覆盖</span>
              <div class="bar-wrap"><div class="bar-fill knowledge" :style="{width: (currentResult.analysis.knowledge_score/10*100)+'%'}"></div></div>
              <span class="value">{{ currentResult.analysis.knowledge_score }}</span>
            </div>
            <div class="dimension-bar">
              <span class="label">逻辑推理</span>
              <div class="bar-wrap"><div class="bar-fill logic" :style="{width: (currentResult.analysis.logic_score/10*100)+'%'}"></div></div>
              <span class="value">{{ currentResult.analysis.logic_score }}</span>
            </div>
            <div class="dimension-bar">
              <span class="label">语言表达</span>
              <div class="bar-wrap"><div class="bar-fill expression" :style="{width: (currentResult.analysis.expression_score/10*100)+'%'}"></div></div>
              <span class="value">{{ currentResult.analysis.expression_score }}</span>
            </div>
          </el-col>
        </el-row>

        <el-divider />

        <h4 style="margin-bottom:12px;color:var(--primary)">学生答案</h4>
        <div style="background:var(--bg);padding:16px;border-radius:8px;margin-bottom:20px;line-height:1.8;font-size:14px">{{ currentResult.answer_content }}</div>

        <template v-if="currentResult.feedback">
          <h4 style="margin-bottom:12px;color:var(--primary)">AI 反馈</h4>
          <div style="background:#f0f8f5;padding:16px;border-radius:8px;margin-bottom:16px;line-height:1.8;font-size:14px">{{ currentResult.feedback.overall_feedback }}</div>

          <el-row :gutter="16">
            <el-col :span="12">
              <h5 style="margin-bottom:8px;color:#2e7d32">✓ 亮点</h5>
              <ul style="padding-left:16px;font-size:13px;color:var(--text-secondary)">
                <li v-for="(s,i) in (currentResult.feedback.strengths||[])" :key="i" style="margin-bottom:4px">{{ s }}</li>
              </ul>
            </el-col>
            <el-col :span="12">
              <h5 style="margin-bottom:8px;color:#c62828">✗ 不足</h5>
              <ul style="padding-left:16px;font-size:13px;color:var(--text-secondary)">
                <li v-for="(w,i) in (currentResult.feedback.weaknesses||[])" :key="i" style="margin-bottom:4px">{{ w }}</li>
              </ul>
            </el-col>
          </el-row>
        </template>
      </template>
    </el-dialog>

    <!-- 教师审核 -->
    <el-dialog v-model="reviewVisible" title="教师审核" width="600px">
      <template v-if="reviewData">
        <div style="margin-bottom:16px">
          <span style="font-size:14px;color:var(--text-secondary)">AI 评分：</span>
          <span style="font-size:20px;font-weight:700;color:var(--primary)">{{ reviewData.analysis?.overall_score }}</span>
        </div>
        <el-form label-width="90px">
          <el-form-item label="分数调整">
            <el-input-number v-model="reviewForm.teacher_score_adjustment" :min="-5" :max="5" :step="0.5" />
            <span style="margin-left:12px;color:var(--text-muted);font-size:13px">正数加分，负数减分</span>
          </el-form-item>
          <el-form-item label="教师评语">
            <el-input v-model="reviewForm.teacher_comment" type="textarea" :rows="4" placeholder="请输入您的审核意见和补充评语" />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="reviewVisible=false">取消</el-button>
        <el-button type="primary" @click="submitReview">确认审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { assignmentApi, answerApi, analysisApi, feedbackApi, exportApi } from '../../api'
import { ElMessage } from 'element-plus'

const assignments = ref([])
const answers = ref([])
const filters = reactive({ assignment_id: null })
const batchLoading = ref(false)
const resultVisible = ref(false)
const reviewVisible = ref(false)
const currentResult = ref(null)
const reviewData = ref(null)
const reviewForm = reactive({ teacher_comment: '', teacher_score_adjustment: 0 })

const unanalyzed = computed(() => answers.value.filter(a => a.status === 'submitted'))

const scoreClass = (s) => {
  const pct = (s / 10) * 100
  if (pct >= 90) return 'excellent'
  if (pct >= 75) return 'good'
  if (pct >= 60) return 'average'
  return 'poor'
}

const statusType = s => ({ submitted: 'warning', analyzing: '', completed: 'success' }[s] || 'info')
const statusLabel = s => ({ submitted: '待分析', analyzing: '分析中', completed: '已完成' }[s] || s)

const loadAssignments = async () => { const res = await assignmentApi.getList(); assignments.value = res.data }

const loadAnswers = async () => {
  if (!filters.assignment_id) { answers.value = []; return }
  const res = await answerApi.getList({ assignment_id: filters.assignment_id })
  answers.value = res.data
}

const singleAnalyze = async (row) => {
  row._loading = true
  try {
    const res = await analysisApi.analyze({ answer_id: row.id })
    row.analysis = res.data.analysis
    row.feedback = res.data.feedback
    row.status = 'completed'
    ElMessage.success('分析完成')
  } finally { row._loading = false }
}

const batchAnalyze = async () => {
  batchLoading.value = true
  try {
    const ids = unanalyzed.value.map(a => a.id)
    await analysisApi.batchAnalyze({ answer_ids: ids })
    ElMessage.success('批量分析完成')
    await loadAnswers()
  } finally { batchLoading.value = false }
}

const showResult = (row) => {
  currentResult.value = {
    ...row,
    analysis: row.analysis,
    feedback: row.feedback
  }
  resultVisible.value = true
}

const showReview = (row) => {
  reviewData.value = row
  reviewForm.teacher_comment = ''
  reviewForm.teacher_score_adjustment = 0
  reviewVisible.value = true
}

const submitReview = async () => {
  await feedbackApi.review(reviewData.value.feedback.id, reviewForm)
  ElMessage.success('审核完成')
  reviewVisible.value = false
  loadAnswers()
}

const handleExportCsv = async () => {
  try {
    await exportApi.gradingCsv(filters.assignment_id)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(loadAssignments)
</script>
