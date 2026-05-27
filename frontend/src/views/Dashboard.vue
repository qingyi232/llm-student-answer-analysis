<template>
  <div>
    <div class="page-header">
      <h2>{{ greeting }}，{{ user.real_name }}</h2>
      <el-tag type="info" round>{{ today }}</el-tag>
    </div>

    <!-- 管理员仪表盘 -->
    <template v-if="user.role==='admin'">
      <el-row :gutter="16" style="margin-bottom:24px">
        <el-col :span="4" v-for="(s,i) in adminStats" :key="i">
          <div class="stat-card">
            <div class="stat-icon" :style="{background:s.bg}"><el-icon :size="22"><component :is="s.icon" /></el-icon></div>
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </el-col>
      </el-row>
    </template>

    <!-- 教师仪表盘 -->
    <template v-if="user.role==='teacher'">
      <el-row :gutter="16" style="margin-bottom:24px">
        <el-col :span="4" v-for="(s,i) in teacherStats" :key="i">
          <div class="stat-card">
            <div class="stat-icon" :style="{background:s.bg}"><el-icon :size="22"><component :is="s.icon" /></el-icon></div>
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </el-col>
      </el-row>
    </template>

    <!-- 学生仪表盘 -->
    <template v-if="user.role==='student'">
      <el-row :gutter="16" style="margin-bottom:24px">
        <el-col :span="5" v-for="(s,i) in studentStats" :key="i">
          <div class="stat-card">
            <div class="stat-icon" :style="{background:s.bg}"><el-icon :size="22"><component :is="s.icon" /></el-icon></div>
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </el-col>
      </el-row>
    </template>

    <el-row :gutter="20">
      <el-col :span="14">
        <el-card>
          <template #header><span style="font-weight:600">成绩分布</span></template>
          <div ref="chartRef" style="height:320px"></div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header><span style="font-weight:600">三维能力雷达</span></template>
          <div ref="radarRef" style="height:320px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi } from '../api'
import * as echarts from 'echarts'

const user = computed(() => {
  try { return JSON.parse(localStorage.getItem('casa_user') || '{}') } catch { return {} }
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '上午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const today = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })

const dashData = ref({})
const adminStats = computed(() => [
  { icon: 'User', label: '总用户数', value: dashData.value.total_users || 0, bg: '#e8f5f0' },
  { icon: 'Avatar', label: '教师数', value: dashData.value.total_teachers || 0, bg: '#fef5e4' },
  { icon: 'UserFilled', label: '学生数', value: dashData.value.total_students || 0, bg: '#e8f0fe' },
  { icon: 'Reading', label: '课程数', value: dashData.value.total_courses || 0, bg: '#fce8f0' },
  { icon: 'Document', label: '答案总量', value: dashData.value.total_answers || 0, bg: '#f0e8fc' },
  { icon: 'DataAnalysis', label: '分析完成率', value: (dashData.value.analysis_rate || 0) + '%', bg: '#e8f5f0' },
])

const teacherStats = computed(() => [
  { icon: 'Reading', label: '我的课程', value: dashData.value.total_courses || 0, bg: '#e8f5f0' },
  { icon: 'Tickets', label: '题库数量', value: dashData.value.total_questions || 0, bg: '#fef5e4' },
  { icon: 'EditPen', label: '发布作业', value: dashData.value.total_assignments || 0, bg: '#e8f0fe' },
  { icon: 'UserFilled', label: '学生人数', value: dashData.value.total_students || 0, bg: '#fce8f0' },
  { icon: 'DocumentCopy', label: '收到答案', value: dashData.value.total_answers || 0, bg: '#f0e8fc' },
  { icon: 'Clock', label: '待审核', value: dashData.value.pending_review || 0, bg: '#fff3e0' },
])

const studentStats = computed(() => [
  { icon: 'Reading', label: '已选课程', value: dashData.value.enrolled_courses || 0, bg: '#e8f5f0' },
  { icon: 'EditPen', label: '已提交', value: dashData.value.total_answers || 0, bg: '#fef5e4' },
  { icon: 'CircleCheck', label: '已批阅', value: dashData.value.completed_answers || 0, bg: '#e8f0fe' },
  { icon: 'TrendCharts', label: '平均分', value: dashData.value.average_score || 0, bg: '#fce8f0' },
])

const chartRef = ref()
const radarRef = ref()

onMounted(async () => {
  const res = await statsApi.dashboard()
  dashData.value = res.data

  const distRes = await statsApi.scoreDistribution()
  const dist = distRes.data

  const barColors = ['#ef5350', '#ff9800', '#ffc107', '#66bb6a', '#2d8c6e']
  const chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}分: {c}人' },
    xAxis: { type: 'category', data: Object.keys(dist).map(k => k + '分'), axisLabel: { color: '#637370' } },
    yAxis: { type: 'value', axisLabel: { color: '#637370' }, minInterval: 1 },
    series: [{
      type: 'bar',
      data: Object.values(dist).map((v, i) => ({
        value: v,
        itemStyle: { color: barColors[i], borderRadius: [6, 6, 0, 0] }
      })),
      barWidth: 36
    }],
    grid: { left: 50, right: 20, top: 20, bottom: 40 }
  })

  const dimRes = await statsApi.dimensionAvg()
  const dim = dimRes.data
  const radar = echarts.init(radarRef.value)
  radar.setOption({
    radar: {
      indicator: [
        { name: '知识覆盖', max: 10 },
        { name: '逻辑推理', max: 10 },
        { name: '语言表达', max: 10 }
      ],
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#637370', fontSize: 13 },
      splitArea: { areaStyle: { color: ['#f8faf9', '#edf4f1', '#e4ede9', '#d9e8e3'] } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [dim.knowledge || 0, dim.logic || 0, dim.expression || 0],
        name: '三维能力均值',
        areaStyle: { color: 'rgba(45,140,110,0.15)' },
        lineStyle: { color: '#2d8c6e', width: 2 },
        itemStyle: { color: '#2d8c6e' }
      }]
    }]
  })

  window.addEventListener('resize', () => { chart.resize(); radar.resize() })
})
</script>
