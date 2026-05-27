<template>
  <div>
    <div class="page-header">
      <h2>学习分析</h2>
    </div>

    <el-row :gutter="16" style="margin-bottom:24px">
      <el-col :span="6" v-for="(s,i) in statCards" :key="i">
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
          <template #header><span style="font-weight:600">三维能力分析</span></template>
          <div ref="radarRef" style="height:300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight:600">成绩分布</span></template>
          <div ref="pieRef" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header><span style="font-weight:600">答题记录</span></template>
      <el-table :data="answers" stripe size="small">
        <el-table-column prop="question_title" label="题目" min-width="200" show-overflow-tooltip />
        <el-table-column prop="submit_time" label="提交时间" width="170" />
        <el-table-column prop="word_count" label="字数" width="70" align="center" />
        <el-table-column label="总分" width="80" align="center">
          <template #default="{row}">
            <span v-if="row.analysis" class="score-badge" :class="scoreClass(row.analysis.overall_score)">
              {{ row.analysis.overall_score }}
            </span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="知识" width="70" align="center">
          <template #default="{row}"><span style="color:var(--primary);font-weight:600">{{ row.analysis?.knowledge_score || '--' }}</span></template>
        </el-table-column>
        <el-table-column label="逻辑" width="70" align="center">
          <template #default="{row}"><span style="color:var(--accent);font-weight:600">{{ row.analysis?.logic_score || '--' }}</span></template>
        </el-table-column>
        <el-table-column label="表达" width="70" align="center">
          <template #default="{row}"><span style="color:#5c9ced;font-weight:600">{{ row.analysis?.expression_score || '--' }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{row}">
            <el-tag :type="row.status==='completed'?'success':'warning'" size="small" round>
              {{ row.status==='completed'?'已批阅':'待批阅' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { answerApi, statsApi } from '../../api'
import * as echarts from 'echarts'

const answers = ref([])
const dimData = ref({ knowledge: 0, logic: 0, expression: 0 })
const distData = ref({})
const dashData = ref({})
const radarRef = ref()
const pieRef = ref()

const scoreClass = (s) => {
  const pct = (s / 10) * 100
  if (pct >= 90) return 'excellent'
  if (pct >= 75) return 'good'
  if (pct >= 60) return 'average'
  return 'poor'
}

const statCards = computed(() => [
  { icon: 'EditPen', label: '已提交', value: dashData.value.total_answers || 0, bg: '#e8f5f0' },
  { icon: 'CircleCheck', label: '已批阅', value: dashData.value.completed_answers || 0, bg: '#fef5e4' },
  { icon: 'TrendCharts', label: '平均分', value: dashData.value.average_score || 0, bg: '#e8f0fe' },
  { icon: 'Reading', label: '已选课程', value: dashData.value.enrolled_courses || 0, bg: '#fce8f0' },
])

onMounted(async () => {
  const [ansRes, dimRes, distRes, dashRes] = await Promise.all([
    answerApi.getList(),
    statsApi.dimensionAvg(),
    statsApi.scoreDistribution(),
    statsApi.dashboard()
  ])
  answers.value = ansRes.data
  dimData.value = dimRes.data
  distData.value = distRes.data
  dashData.value = dashRes.data

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
        value: [dimData.value.knowledge, dimData.value.logic, dimData.value.expression],
        name: '我的能力',
        areaStyle: { color: 'rgba(45,140,110,0.2)' },
        lineStyle: { color: '#2d8c6e', width: 2 },
        itemStyle: { color: '#2d8c6e' }
      }]
    }]
  })

  const pie = echarts.init(pieRef.value)
  const dist = distData.value
  const colorMap = { '0-59': '#ef5350', '60-69': '#ff9800', '70-79': '#ffc107', '80-89': '#66bb6a', '90-100': '#2d8c6e' }
  const pieData = Object.entries(dist).map(([k, v]) => ({
    name: k + '分',
    value: v,
    itemStyle: { color: colorMap[k] || '#999' }
  }))
  pie.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}次 ({d}%)' },
    legend: { bottom: 0, itemWidth: 14, itemHeight: 14, textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '45%'],
      data: pieData,
      label: { show: true, formatter: '{b}\n{c}次', fontSize: 12 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' } }
    }]
  })

  window.addEventListener('resize', () => { radar.resize(); pie.resize() })
})
</script>
