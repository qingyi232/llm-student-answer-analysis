<template>
  <div>
    <div class="page-header">
      <h2>系统监控</h2>
      <el-button type="primary" plain @click="refresh"><el-icon><Refresh /></el-icon>刷新状态</el-button>
    </div>

    <el-row :gutter="20" style="margin-bottom:24px">
      <el-col :span="6" v-for="(item,i) in sysInfo" :key="i">
        <el-card>
          <div style="text-align:center">
            <div style="font-size:28px;margin-bottom:8px"><el-icon :size="28"><component :is="item.icon" /></el-icon></div>
            <div style="font-size:20px;font-weight:700;color:var(--primary)">{{ item.value }}</div>
            <div style="font-size:13px;color:var(--text-muted);margin-top:4px">{{ item.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-bottom:24px">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight:600">服务状态</span></template>
          <el-table :data="monitor.services || []" size="small">
            <el-table-column prop="name" label="服务名称" />
            <el-table-column label="状态" width="100">
              <template #default="{row}">
                <el-tag :type="row.status==='running'?'success':'danger'" size="small" round>
                  {{ row.status==='running'?'运行中':'异常' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="uptime" label="运行时长" width="120" />
            <el-table-column prop="load" label="负载" width="100">
              <template #default="{row}">
                <el-progress :percentage="row.load" :stroke-width="6"
                  :color="row.load>80?'#ef5350':row.load>50?'#ff9800':'#2d8c6e'" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight:600">最近操作日志</span></template>
          <el-timeline v-if="(monitor.logs||[]).length">
            <el-timeline-item v-for="(log,i) in monitor.logs" :key="i" :timestamp="log.time" placement="top"
              :type="log.type==='success'?'success':log.type==='warning'?'warning':'primary'">
              <p style="font-size:14px">{{ log.content }}</p>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无操作日志" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header><span style="font-weight:600">LLM 分析引擎状态</span></template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="引擎版本">DeepSeek Chat + CASA-v1.0</el-descriptions-item>
        <el-descriptions-item label="评价框架">KLE 三维评价 (知识-逻辑-表达)</el-descriptions-item>
        <el-descriptions-item label="引擎状态">
          <el-tag :type="monitor.llm_status==='running'?'success':'danger'" size="small">
            {{ monitor.llm_status==='running'?'在线':'离线' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="平均分析耗时">{{ monitor.avg_analysis_time || 0 }} 秒</el-descriptions-item>
        <el-descriptions-item label="累计分析量">{{ monitor.total_analyzed || 0 }} 份</el-descriptions-item>
        <el-descriptions-item label="分析完成率">{{ monitor.analysis_rate || 0 }}%</el-descriptions-item>
        <el-descriptions-item label="支持题型">论述题 / 简答题 / 案例分析题</el-descriptions-item>
        <el-descriptions-item label="支持学科">语文 / 数学 / 历史 / 地理</el-descriptions-item>
        <el-descriptions-item label="系统运行时长">{{ monitor.uptime || '--' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { monitorApi } from '../../api'

const monitor = ref({})

const sysInfo = computed(() => [
  { icon: 'Monitor', label: 'API 服务', value: monitor.value.api_status === 'running' ? '正常' : '异常' },
  { icon: 'Coin', label: '数据库', value: monitor.value.db_status === 'running' ? '正常' : '异常' },
  { icon: 'Cpu', label: 'LLM 引擎', value: monitor.value.llm_status === 'running' ? '在线' : '离线' },
  { icon: 'Timer', label: '平均分析耗时', value: (monitor.value.avg_analysis_time || 0) + 's' },
])

const refresh = async () => {
  const res = await monitorApi.getStatus()
  monitor.value = res.data
}

onMounted(refresh)
</script>
