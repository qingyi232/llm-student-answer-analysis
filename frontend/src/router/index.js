import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '工作台' } },
      { path: 'courses', name: 'Courses', component: () => import('../views/teacher/Courses.vue'), meta: { title: '课程管理', role: 'teacher' } },
      { path: 'questions', name: 'Questions', component: () => import('../views/teacher/Questions.vue'), meta: { title: '题库管理', role: 'teacher' } },
      { path: 'assignments', name: 'Assignments', component: () => import('../views/teacher/Assignments.vue'), meta: { title: '作业管理', role: 'teacher' } },
      { path: 'grading', name: 'Grading', component: () => import('../views/teacher/Grading.vue'), meta: { title: '智能批阅', role: 'teacher' } },
      { path: 'student-assignments', name: 'StudentAssignments', component: () => import('../views/student/MyAssignments.vue'), meta: { title: '我的作业', role: 'student' } },
      { path: 'answer/:assignmentId', name: 'AnswerSheet', component: () => import('../views/student/AnswerSheet.vue'), meta: { title: '答题', role: 'student' } },
      { path: 'my-feedback', name: 'MyFeedback', component: () => import('../views/student/MyFeedback.vue'), meta: { title: '反馈报告', role: 'student' } },
      { path: 'my-analysis', name: 'MyAnalysis', component: () => import('../views/student/MyAnalysis.vue'), meta: { title: '学习分析', role: 'student' } },
      { path: 'admin-users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue'), meta: { title: '用户管理', role: 'admin' } },
      { path: 'admin-stats', name: 'AdminStats', component: () => import('../views/admin/Statistics.vue'), meta: { title: '系统统计', role: 'admin' } },
      { path: 'admin-monitor', name: 'AdminMonitor', component: () => import('../views/admin/Monitor.vue'), meta: { title: '系统监控', role: 'admin' } },
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.path !== '/login') {
    const token = localStorage.getItem('casa_token')
    if (!token) return next('/login')
  }
  next()
})

export default router
