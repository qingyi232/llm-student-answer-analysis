<template>
  <div>
    <div class="page-header">
      <h2>数据统计</h2>
    </div>

    <el-row :gutter="16" style="margin-bottom:24px">
      <el-col :span="4" v-for="(s,i) in statCards" :key="i">
        <div class="stat-card">
          <div class="stat-icon" :style="{background:s.bg}"><el-icon :size="22"><component :is="s.icon" /></el-icon></div>
          <div class="stat-value">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-bottom:24px">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight:600">成绩分布统计</span></template>
          <div ref="barRef" style="height:320px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight:600">三维能力均值</span></template>
          <div ref="radarRef" style="height:320px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header><span style="font-weight:600">系统数据总览</span></template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="总用户数">{{ dash.total_users || 0 }}</el-descriptions-item>
        <el-descriptions-item label="教师数">{{ dash.total_teachers || 0 }}</el-descriptions-item>
        <el-descriptions-item label="学生数">{{ dash.total_students || 0 }}</el-descriptions-item>
        <el-descriptions-item label="课程总数">{{ dash.total_courses || 0 }}</el-descriptions-item>
        <el-descriptions-item label="题目总量">{{ dash.total_questions || 0 }}</el-descriptions-item>
        <el-descriptions-item label="作业数">{{ dash.total_assignments || 0 }}</el-descriptions-item>
        <el-descriptions-item label="答案总量">{{ dash.total_answers || 0 }}</el-descriptions-item>
        <el-descriptions-item label="分析完成">{{ dash.total_analyzed || 0 }}</el-descriptions-item>
        <el-descriptions-item label="平均得分">{{ dash.avg_score || 0 }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi } from '../../api'
import * as echarts from 'echarts'

const dash = ref({})
const barRef = ref()
const radarRef = ref()

const statCards = computed(() => [
  { icon: 'User', label: '总用户', value: dash.value.total_users || 0, bg: '#e8f5f0' },
  { icon: 'Reading', label: '课程数', value: dash.value.total_courses || 0, bg: '#fef5e4' },
  { icon: 'Tickets', label: '题目数', value: dash.value.total_questions || 0, bg: '#e8f0fe' },
  { icon: 'Document', label: '答案量', value: dash.value.total_answers || 0, bg: '#fce8f0' },
  { icon: 'Cpu', label: '已分析', value: dash.value.total_analyzed || 0, bg: '#f0e8fc' },
  { icon: 'DataAnalysis', label: '分析率', value: (dash.value.analysis_rate || 0) + '%', bg: '#e8f5f0' },
])

onMounted(async () => {
  const [dashRes, distRes, dimRes] = await Promise.all([
    statsApi.dashboard(),
    statsApi.scoreDistribution(),
    statsApi.dimensionAvg()
  ])
  dash.value = dashRes.data

  const bar = echarts.init(barRef.value)
  bar.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: Object.keys(distRes.data) },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar', data: Object.values(distRes.data),
      itemStyle: {
        color: (p) => ['#ef5350', '#ff9800', '#ffc107', '#66bb6a', '#2d8c6e'][p.dataIndex],
        borderRadius: [6, 6, 0, 0]
      },
      barWidth: 40
    }],
    grid: { left: 50, right: 20, top: 20, bottom: 40 }
  })

  const dim = dimRes.data
  const radar = echarts.init(radarRef.value)
  radar.setOption({
    radar: {
      indicator: [{ name: '知识覆盖', max: 10 }, { name: '逻辑推理', max: 10 }, { name: '语言表达', max: 10 }],
      shape: 'polygon', splitNumber: 4,
      splitArea: { areaStyle: { color: ['#f8faf9', '#edf4f1', '#e4ede9', '#d9e8e3'] } }
    },
    series: [{
      type: 'radar',
      data: [{ value: [dim.knowledge, dim.logic, dim.expression], name: '全校均值',
        areaStyle: { color: 'rgba(45,140,110,0.2)' }, lineStyle: { color: '#2d8c6e', width: 2 }, itemStyle: { color: '#2d8c6e' }
      }]
    }]
  })

  window.addEventListener('resize', () => { bar.resize(); radar.resize() })
})
</script>
