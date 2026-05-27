<template>
  <el-container style="height:100vh">
    <el-aside :width="isCollapse?'64px':'220px'" style="background:#fff;border-right:1px solid var(--border-light);overflow:hidden">
      <div class="logo-area" :class="{collapsed:isCollapse}">
        <div class="logo-icon"><el-icon :size="24" color="#2d8c6e"><EditPen /></el-icon></div>
        <span v-if="!isCollapse" class="logo-text">CASA 智能分析</span>
      </div>
      <el-menu :default-active="currentPath" :collapse="isCollapse" router :collapse-transition="false" style="background:#fff">
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>

        <template v-if="user.role==='teacher'">
          <el-menu-item-group>
            <template #title><span v-if="!isCollapse" style="color:var(--text-muted);font-size:12px">教学管理</span></template>
            <el-menu-item index="/courses"><el-icon><Reading /></el-icon><template #title>课程管理</template></el-menu-item>
            <el-menu-item index="/questions"><el-icon><Document /></el-icon><template #title>题库管理</template></el-menu-item>
            <el-menu-item index="/assignments"><el-icon><Notebook /></el-icon><template #title>作业管理</template></el-menu-item>
          </el-menu-item-group>
          <el-menu-item-group>
            <template #title><span v-if="!isCollapse" style="color:var(--text-muted);font-size:12px">智能批阅</span></template>
            <el-menu-item index="/grading"><el-icon><Cpu /></el-icon><template #title>AI 批阅中心</template></el-menu-item>
          </el-menu-item-group>
        </template>

        <template v-if="user.role==='student'">
          <el-menu-item-group>
            <template #title><span v-if="!isCollapse" style="color:var(--text-muted);font-size:12px">学习中心</span></template>
            <el-menu-item index="/student-assignments"><el-icon><Notebook /></el-icon><template #title>我的作业</template></el-menu-item>
            <el-menu-item index="/my-feedback"><el-icon><ChatDotRound /></el-icon><template #title>反馈报告</template></el-menu-item>
            <el-menu-item index="/my-analysis"><el-icon><TrendCharts /></el-icon><template #title>学习分析</template></el-menu-item>
          </el-menu-item-group>
        </template>

        <template v-if="user.role==='admin'">
          <el-menu-item-group>
            <template #title><span v-if="!isCollapse" style="color:var(--text-muted);font-size:12px">系统管理</span></template>
            <el-menu-item index="/admin-users"><el-icon><User /></el-icon><template #title>用户管理</template></el-menu-item>
            <el-menu-item index="/admin-stats"><el-icon><PieChart /></el-icon><template #title>数据统计</template></el-menu-item>
            <el-menu-item index="/admin-monitor"><el-icon><Monitor /></el-icon><template #title>系统监控</template></el-menu-item>
          </el-menu-item-group>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="height:56px;background:#fff;border-bottom:1px solid var(--border-light);display:flex;align-items:center;justify-content:space-between;padding:0 24px">
        <div style="display:flex;align-items:center;gap:16px">
          <el-icon :size="18" style="cursor:pointer;color:var(--text-secondary)" @click="isCollapse=!isCollapse"><Fold v-if="!isCollapse"/><Expand v-else/></el-icon>
          <span style="font-size:15px;color:var(--text-secondary)">{{ currentTitle }}</span>
        </div>
        <div style="display:flex;align-items:center;gap:16px">
          <el-tag :type="roleTagType" size="small" round>{{ roleLabel }}</el-tag>
          <el-dropdown @command="handleCommand">
            <span style="display:flex;align-items:center;gap:8px;cursor:pointer;color:var(--text-primary);font-size:14px">
              <el-avatar :size="32" style="background:var(--primary)">{{ user.real_name?.charAt(0) }}</el-avatar>
              {{ user.real_name }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout"><el-icon><SwitchButton /></el-icon>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main style="padding:24px;background:var(--bg);overflow-y:auto">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const isCollapse = ref(false)

const user = computed(() => {
  try { return JSON.parse(localStorage.getItem('casa_user') || '{}') } catch { return {} }
})

const currentPath = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '工作台')

const roleLabel = computed(() => {
  const map = { admin: '管理员', teacher: '教师', student: '学生' }
  return map[user.value.role] || ''
})

const roleTagType = computed(() => {
  const map = { admin: 'danger', teacher: 'warning', student: 'success' }
  return map[user.value.role] || 'info'
})

const handleCommand = (cmd) => {
  if (cmd === 'logout') {
    localStorage.removeItem('casa_token')
    localStorage.removeItem('casa_user')
    router.push('/login')
  }
}
</script>

<style scoped>
.logo-area {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-light);
  overflow: hidden;
  white-space: nowrap;
}
.logo-area.collapsed { justify-content: center; padding: 0; }
.logo-icon { font-size: 24px; }
.logo-text { font-size: 15px; font-weight: 700; color: var(--primary); letter-spacing: 0.5px; }
</style>
