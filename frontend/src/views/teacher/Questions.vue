<template>
  <div>
    <div class="page-header">
      <h2>题库管理</h2>
      <el-button type="primary" @click="showDialog()"><el-icon><Plus /></el-icon>新建题目</el-button>
    </div>

    <el-card style="margin-bottom:20px">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filters.course_id" placeholder="筛选课程" clearable style="width:100%" @change="load">
            <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.question_type" placeholder="题型" clearable style="width:100%" @change="load">
            <el-option label="论述题" value="论述题" /><el-option label="简答题" value="简答题" />
            <el-option label="案例分析题" value="案例分析题" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="questions" stripe style="width:100%">
      <el-table-column prop="title" label="题目标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="course_name" label="所属课程" width="180" />
      <el-table-column prop="question_type" label="题型" width="100">
        <template #default="{row}">
          <el-tag :type="typeTag(row.question_type)" size="small" round>{{ row.question_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="difficulty" label="难度" width="80">
        <template #default="{row}">
          <el-tag :type="diffTag(row.difficulty)" size="small" effect="plain">{{ row.difficulty }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="max_score" label="满分" width="70" align="center" />
      <el-table-column label="知识点" width="200">
        <template #default="{row}">
          <el-tag v-for="kp in (row.knowledge_points||[]).slice(0,2)" :key="kp" size="small" effect="plain" style="margin:2px" round>{{ kp }}</el-tag>
          <el-tag v-if="(row.knowledge_points||[]).length>2" size="small" type="info" round>+{{ row.knowledge_points.length-2 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{row}">
          <el-button size="small" text type="primary" @click="showDetail(row)">详情</el-button>
          <el-button size="small" text type="primary" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference><el-button size="small" text type="danger">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑题目':'新建题目'" width="700px" destroy-on-close>
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="所属课程">
              <el-select v-model="form.course_id" placeholder="选择课程" style="width:100%">
                <el-option v-for="c in courses" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="题目类型">
              <el-select v-model="form.question_type" placeholder="选择题型" style="width:100%">
                <el-option label="论述题" value="论述题" /><el-option label="简答题" value="简答题" />
                <el-option label="案例分析题" value="案例分析题" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="题目标题"><el-input v-model="form.title" placeholder="题目的简短标题" /></el-form-item>
        <el-form-item label="题目内容"><el-input v-model="form.content" type="textarea" :rows="4" placeholder="完整的题目描述" /></el-form-item>
        <el-form-item label="参考答案"><el-input v-model="form.reference_answer" type="textarea" :rows="4" placeholder="标准参考答案" /></el-form-item>
        <el-form-item label="评分标准"><el-input v-model="form.grading_criteria" type="textarea" :rows="2" placeholder="评分要点和分值分配" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="满分分值"><el-input-number v-model="form.max_score" :min="1" :max="100" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="难度">
              <el-select v-model="form.difficulty" style="width:100%">
                <el-option label="简单" value="简单" /><el-option label="中等" value="中等" /><el-option label="困难" value="困难" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学科"><el-input v-model="form.subject" placeholder="如 语文" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="知识点">
          <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
            <el-tag v-for="(kp,i) in form.knowledge_points" :key="i" closable @close="form.knowledge_points.splice(i,1)" round>{{ kp }}</el-tag>
            <el-input v-if="showKpInput" ref="kpInputRef" v-model="kpValue" size="small" style="width:120px" @keyup.enter="addKp" @blur="addKp" />
            <el-button v-else size="small" @click="showKpInput=true">+ 添加</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="题目详情" width="650px">
      <template v-if="detailData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="题目标题" :span="2">{{ detailData.title }}</el-descriptions-item>
          <el-descriptions-item label="所属课程">{{ detailData.course_name }}</el-descriptions-item>
          <el-descriptions-item label="题型">{{ detailData.question_type }}</el-descriptions-item>
          <el-descriptions-item label="难度">{{ detailData.difficulty }}</el-descriptions-item>
          <el-descriptions-item label="满分">{{ detailData.max_score }}</el-descriptions-item>
          <el-descriptions-item label="题目内容" :span="2">
            <div style="white-space:pre-wrap">{{ detailData.content }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="参考答案" :span="2">
            <div style="white-space:pre-wrap;color:var(--primary)">{{ detailData.reference_answer }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="评分标准" :span="2">{{ detailData.grading_criteria }}</el-descriptions-item>
          <el-descriptions-item label="知识点" :span="2">
            <el-tag v-for="kp in (detailData.knowledge_points||[])" :key="kp" size="small" style="margin:2px" round>{{ kp }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { questionApi, courseApi } from '../../api'
import { ElMessage } from 'element-plus'

const questions = ref([])
const courses = ref([])
const filters = reactive({ course_id: null, question_type: null })
const dialogVisible = ref(false)
const detailVisible = ref(false)
const detailData = ref(null)
const isEdit = ref(false)
const editId = ref(null)
const showKpInput = ref(false)
const kpValue = ref('')
const kpInputRef = ref()

const form = reactive({
  course_id: null, question_type: '', title: '', content: '', reference_answer: '',
  grading_criteria: '', max_score: 10, difficulty: '中等', subject: '', knowledge_points: []
})

const typeTag = t => ({ '论述题': 'danger', '简答题': 'warning', '案例分析题': '' }[t] || 'info')
const diffTag = d => ({ '简单': 'success', '中等': 'warning', '困难': 'danger' }[d] || 'info')

const load = async () => {
  const res = await questionApi.getList(filters)
  questions.value = res.data
}

const loadCourses = async () => {
  const res = await courseApi.getList()
  courses.value = res.data
}

const showDialog = (q) => {
  if (q) {
    isEdit.value = true; editId.value = q.id
    Object.assign(form, { ...q, knowledge_points: [...(q.knowledge_points || [])] })
  } else {
    isEdit.value = false; editId.value = null
    Object.assign(form, { course_id: null, question_type: '', title: '', content: '', reference_answer: '', grading_criteria: '', max_score: 10, difficulty: '中等', subject: '', knowledge_points: [] })
  }
  dialogVisible.value = true
}

const showDetail = (q) => { detailData.value = q; detailVisible.value = true }

const addKp = () => {
  if (kpValue.value.trim()) {
    form.knowledge_points.push(kpValue.value.trim())
    kpValue.value = ''
  }
  showKpInput.value = false
}

const handleSave = async () => {
  if (isEdit.value) {
    await questionApi.update(editId.value, form)
    ElMessage.success('更新成功')
  } else {
    await questionApi.create(form)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  load()
}

const handleDelete = async (id) => { await questionApi.delete(id); ElMessage.success('删除成功'); load() }

onMounted(() => { loadCourses(); load() })
</script>
