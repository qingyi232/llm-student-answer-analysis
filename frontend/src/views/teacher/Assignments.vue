<template>
  <div>
    <div class="page-header">
      <h2>作业管理</h2>
      <el-button type="primary" @click="showDialog()"><el-icon><Plus /></el-icon>发布作业</el-button>
    </div>

    <el-table :data="assignments" stripe>
      <el-table-column prop="title" label="作业标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="course_name" label="所属课程" width="200" />
      <el-table-column prop="question_count" label="题目数" width="80" align="center" />
      <el-table-column label="提交情况" width="150">
        <template #default="{row}">
          <span style="color:var(--primary);font-weight:600">{{ row.submitted_students || 0 }}</span>
          <span style="color:var(--text-muted)"> / {{ row.total_students || 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="deadline" label="截止时间" width="170" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{row}">
          <el-tag :type="row.status==='active'?'success':'info'" size="small" round>
            {{ row.status==='active'?'进行中':row.status==='draft'?'草稿':'已关闭' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{row}">
          <el-button size="small" text type="primary" @click="viewDetail(row)">查看</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference><el-button size="small" text type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 发布作业对话框 -->
    <el-dialog v-model="dialogVisible" title="发布作业" width="600px" destroy-on-close>
      <el-form :model="form" label-width="90px">
        <el-form-item label="作业标题"><el-input v-model="form.title" placeholder="请输入作业标题" /></el-form-item>
        <el-form-item label="所属课程">
          <el-select v-model="form.course_id" placeholder="选择课程" style="width:100%" @change="loadCourseQuestions">
            <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="作业描述"><el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入作业说明" /></el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker v-model="form.deadline" type="datetime" placeholder="选择截止时间" format="YYYY-MM-DD HH:mm:ss" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="选择题目">
          <el-checkbox-group v-model="form.question_ids">
            <div v-for="q in courseQuestions" :key="q.id" style="margin-bottom:8px">
              <el-checkbox :value="q.id">
                <span>{{ q.title }}</span>
                <el-tag size="small" type="info" style="margin-left:8px">{{ q.question_type }}</el-tag>
                <el-tag size="small" effect="plain" style="margin-left:4px">{{ q.max_score }}分</el-tag>
              </el-checkbox>
            </div>
          </el-checkbox-group>
          <el-empty v-if="!courseQuestions.length" description="请先选择课程或该课程暂无题目" :image-size="60" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="handleSave">发布</el-button>
      </template>
    </el-dialog>

    <!-- 作业详情 -->
    <el-dialog v-model="detailVisible" title="作业详情" width="700px">
      <template v-if="detailData">
        <el-descriptions :column="2" border style="margin-bottom:20px">
          <el-descriptions-item label="作业标题" :span="2">{{ detailData.title }}</el-descriptions-item>
          <el-descriptions-item label="所属课程">{{ detailData.course_name }}</el-descriptions-item>
          <el-descriptions-item label="截止时间">{{ detailData.deadline }}</el-descriptions-item>
          <el-descriptions-item label="说明" :span="2">{{ detailData.description }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin-bottom:12px">包含题目</h4>
        <el-table :data="detailData.questions || []" stripe size="small">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="title" label="题目" />
          <el-table-column prop="question_type" label="题型" width="100" />
          <el-table-column prop="max_score" label="满分" width="70" align="center" />
          <el-table-column prop="difficulty" label="难度" width="70" />
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { assignmentApi, courseApi, questionApi } from '../../api'
import { ElMessage } from 'element-plus'

const assignments = ref([])
const courses = ref([])
const courseQuestions = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const detailData = ref(null)
const form = reactive({ title: '', course_id: null, description: '', deadline: '', question_ids: [] })

const load = async () => { const res = await assignmentApi.getList(); assignments.value = res.data }

const loadCourses = async () => { const res = await courseApi.getList(); courses.value = res.data }

const loadCourseQuestions = async () => {
  if (!form.course_id) { courseQuestions.value = []; return }
  const res = await questionApi.getList({ course_id: form.course_id })
  courseQuestions.value = res.data
}

const showDialog = () => {
  Object.assign(form, { title: '', course_id: null, description: '', deadline: '', question_ids: [] })
  courseQuestions.value = []
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!form.question_ids.length) { ElMessage.warning('请至少选择一道题目'); return }
  await assignmentApi.create(form)
  ElMessage.success('发布成功')
  dialogVisible.value = false
  load()
}

const viewDetail = async (row) => {
  const res = await assignmentApi.getDetail(row.id)
  detailData.value = res.data
  detailVisible.value = true
}

const handleDelete = async (id) => { await assignmentApi.delete(id); ElMessage.success('删除成功'); load() }

onMounted(() => { load(); loadCourses() })
</script>
