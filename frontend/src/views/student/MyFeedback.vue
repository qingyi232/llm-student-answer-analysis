<template>
  <div>
    <div class="page-header">
      <h2>反馈报告</h2>
    </div>

    <el-table :data="answers" stripe>
      <el-table-column prop="question_title" label="题目" min-width="200" show-overflow-tooltip />
      <el-table-column label="答案预览" min-width="180">
        <template #default="{row}">
          <span style="font-size:13px;color:var(--text-secondary)">{{ row.answer_content?.substring(0,50) }}...</span>
        </template>
      </el-table-column>
      <el-table-column prop="submit_time" label="提交时间" width="170" />
      <el-table-column label="评分" width="100" align="center">
        <template #default="{row}">
          <template v-if="row.analysis">
            <span class="score-badge" :class="scoreClass(row.analysis.overall_score)">{{ row.analysis.overall_score }}</span>
          </template>
          <span v-else style="color:var(--text-muted)">--</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{row}">
          <el-tag :type="row.status==='completed'?'success':'warning'" size="small" round>
            {{ row.status==='completed'?'已批阅':'待批阅' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{row}">
          <el-button v-if="row.analysis" size="small" type="primary" @click="viewReport(row)">查看报告</el-button>
          <el-button v-if="row.analysis" size="small" type="success" @click="handleExport(row)">导出</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 反馈报告详情 -->
    <el-dialog v-model="reportVisible" title="个性化反馈报告" width="850px" top="3vh">
      <template v-if="currentReport">
        <div style="text-align:center;margin-bottom:24px">
          <div style="font-size:48px;font-weight:800;color:var(--primary)">{{ currentReport.analysis.overall_score }}</div>
          <div style="font-size:14px;color:var(--text-muted)">综合得分（满分 {{ currentReport.max_score || 10 }}）</div>
        </div>

        <el-row :gutter="20" style="margin-bottom:24px">
          <el-col :span="8">
            <div class="score-dim-card" style="border-left:3px solid var(--primary)">
              <div class="dim-label">知识覆盖</div>
              <div class="dim-value" style="color:var(--primary)">{{ currentReport.analysis.knowledge_score }}</div>
              <el-progress :percentage="currentReport.analysis.knowledge_score/10*100" :stroke-width="6" color="var(--primary)" :show-text="false" />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="score-dim-card" style="border-left:3px solid var(--accent)">
              <div class="dim-label">逻辑推理</div>
              <div class="dim-value" style="color:var(--accent)">{{ currentReport.analysis.logic_score }}</div>
              <el-progress :percentage="currentReport.analysis.logic_score/10*100" :stroke-width="6" color="var(--accent)" :show-text="false" />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="score-dim-card" style="border-left:3px solid #5c9ced">
              <div class="dim-label">语言表达</div>
              <div class="dim-value" style="color:#5c9ced">{{ currentReport.analysis.expression_score }}</div>
              <el-progress :percentage="currentReport.analysis.expression_score/10*100" :stroke-width="6" color="#5c9ced" :show-text="false" />
            </div>
          </el-col>
        </el-row>

        <!-- 题目与答案 -->
        <el-card style="margin-bottom:16px">
          <template #header><span style="font-weight:600">题目内容</span></template>
          <div style="line-height:1.8;font-size:14px">{{ currentReport.question_content }}</div>
        </el-card>

        <el-card style="margin-bottom:16px">
          <template #header><span style="font-weight:600">我的答案</span></template>
          <div style="line-height:1.8;font-size:14px">{{ currentReport.answer_content }}</div>
        </el-card>

        <!-- AI反馈 -->
        <template v-if="currentReport.feedback">
          <el-card style="margin-bottom:16px;border-left:3px solid var(--primary) !important">
            <template #header><span style="font-weight:600;color:var(--primary)">AI 综合评语</span></template>
            <div style="line-height:1.8;font-size:14px">{{ currentReport.feedback.overall_feedback }}</div>
          </el-card>

          <el-row :gutter="16" style="margin-bottom:16px">
            <el-col :span="12">
              <el-card>
                <template #header><span style="font-weight:600;color:#2e7d32">✓ 答案亮点</span></template>
                <ul style="padding-left:16px;line-height:2">
                  <li v-for="(s,i) in (currentReport.feedback.strengths||[])" :key="i" style="font-size:14px;color:var(--text-secondary)">{{ s }}</li>
                </ul>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card>
                <template #header><span style="font-weight:600;color:#c62828">✗ 需改进</span></template>
                <ul style="padding-left:16px;line-height:2">
                  <li v-for="(w,i) in (currentReport.feedback.weaknesses||[])" :key="i" style="font-size:14px;color:var(--text-secondary)">{{ w }}</li>
                </ul>
              </el-card>
            </el-col>
          </el-row>

          <el-card style="margin-bottom:16px">
            <template #header><span style="font-weight:600;color:var(--accent)">改进建议</span></template>
            <ol style="padding-left:18px;line-height:2">
              <li v-for="(s,i) in (currentReport.feedback.improvement_suggestions||[])" :key="i" style="font-size:14px;color:var(--text-secondary)">{{ s }}</li>
            </ol>
          </el-card>

          <el-card style="margin-bottom:16px">
            <template #header><span style="font-weight:600;color:#5c9ced">推荐资源</span></template>
            <div v-for="(r,i) in (currentReport.feedback.recommended_resources||[])" :key="i" style="padding:8px 0;font-size:14px;color:var(--text-secondary);border-bottom:1px solid var(--border-light)">
              {{ r }}
            </div>
          </el-card>

          <el-card v-if="currentReport.feedback.study_tips">
            <template #header><span style="font-weight:600">学习方法建议</span></template>
            <div style="line-height:1.8;font-size:14px;color:var(--text-secondary)">{{ currentReport.feedback.study_tips }}</div>
          </el-card>

          <el-card v-if="currentReport.feedback.teacher_comment" style="margin-top:16px;border-left:3px solid var(--accent) !important">
            <template #header><span style="font-weight:600;color:var(--accent)">教师批注</span></template>
            <div style="line-height:1.8;font-size:14px">{{ currentReport.feedback.teacher_comment }}</div>
          </el-card>
        </template>

        <!-- 错误分析 -->
        <template v-if="currentReport.analysis.error_points?.length">
          <el-card style="margin-top:16px">
            <template #header><span style="font-weight:600;color:#e65100">错因诊断</span></template>
            <div v-for="(e,i) in currentReport.analysis.error_points" :key="i" style="padding:10px 0;border-bottom:1px solid var(--border-light)">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                <el-tag :type="e.severity==='严重'?'danger':e.severity==='中等'?'warning':'info'" size="small">{{ e.severity }}</el-tag>
                <span style="font-weight:600;font-size:14px">{{ e.type }}</span>
              </div>
              <div style="font-size:13px;color:var(--text-secondary)">{{ e.description }}</div>
            </div>
          </el-card>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { answerApi, questionApi, exportApi } from '../../api'

const answers = ref([])
const reportVisible = ref(false)
const currentReport = ref(null)

const scoreClass = (s) => {
  const pct = (s / 10) * 100
  if (pct >= 90) return 'excellent'
  if (pct >= 75) return 'good'
  if (pct >= 60) return 'average'
  return 'poor'
}

const viewReport = async (row) => {
  let qContent = ''
  try {
    const qRes = await questionApi.getDetail(row.question_id)
    qContent = qRes.data.content
  } catch {}
  currentReport.value = {
    ...row,
    question_content: qContent,
    max_score: 10
  }
  reportVisible.value = true
}

const handleExport = async (row) => {
  try {
    await exportApi.feedbackReport(row.id, row.student_name)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(async () => {
  const res = await answerApi.getList()
  answers.value = res.data
})
</script>

<style scoped>
.score-dim-card {
  background: var(--bg-white);
  padding: 16px 20px;
  border-radius: 8px;
  border: 1px solid var(--border-light);
}
.dim-label { font-size: 13px; color: var(--text-muted); margin-bottom: 4px; }
.dim-value { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
</style>
