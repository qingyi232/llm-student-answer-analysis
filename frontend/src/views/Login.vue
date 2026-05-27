<template>
  <div class="login-page">
    <div class="login-left">
      <div class="left-content">
        <div class="brand-logo"><el-icon :size="48" color="#2d8c6e"><EditPen /></el-icon></div>
        <h1 class="brand-title">CASA</h1>
        <p class="brand-subtitle">学生主观题智能分析与反馈生成系统</p>
        <div class="feature-list">
          <div class="feature-item">
            <div class="feature-icon" style="background:#e8f5f0;color:#2d8c6e"><el-icon :size="20"><DataAnalysis /></el-icon></div>
            <div><div class="feature-title">知识-逻辑-表达 三维评价</div><div class="feature-desc">基于 KLE 框架多维度精准分析</div></div>
          </div>
          <div class="feature-item">
            <div class="feature-icon" style="background:#fef5e4;color:#e8a838"><el-icon :size="20"><Cpu /></el-icon></div>
            <div><div class="feature-title">秒级智能批阅</div><div class="feature-desc">大模型驱动，快速完成分析反馈</div></div>
          </div>
          <div class="feature-item">
            <div class="feature-icon" style="background:#e8f0fe;color:#5c9ced"><el-icon :size="20"><ChatLineSquare /></el-icon></div>
            <div><div class="feature-title">个性化反馈生成</div><div class="feature-desc">精准错因定位与针对性改进建议</div></div>
          </div>
        </div>
      </div>
      <img class="left-bg-img" src="https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&h=600&fit=crop" alt="education" />
    </div>

    <div class="login-right">
      <div class="login-form-wrap">
        <h2 class="form-title">欢迎使用</h2>
        <p class="form-desc">请输入账号密码登录系统</p>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" style="width:100%;height:44px;font-size:15px;border-radius:8px" @click="handleLogin">
              登录系统
            </el-button>
          </el-form-item>
        </el-form>

        <div class="quick-login">
          <p class="quick-title">快速体验</p>
          <div class="quick-btns">
            <el-button size="small" round @click="quickLogin('admin','123456')">管理员登录</el-button>
            <el-button size="small" round @click="quickLogin('teacher1','123456')">教师登录</el-button>
            <el-button size="small" round @click="quickLogin('student1','123456')">学生登录</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await authApi.login(form)
    localStorage.setItem('casa_token', res.data.token)
    localStorage.setItem('casa_user', JSON.stringify(res.data.user))
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}

const quickLogin = (username, password) => {
  form.username = username
  form.password = password
  handleLogin()
}
</script>

<style scoped>
.login-page { display: flex; height: 100vh; background: #fff; }

.login-left {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.left-bg-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.15;
}

.left-content {
  position: relative;
  z-index: 2;
  padding: 60px;
  max-width: 520px;
}

.brand-logo { font-size: 48px; margin-bottom: 12px; }
.brand-title { font-size: 42px; font-weight: 800; color: var(--primary); margin-bottom: 8px; letter-spacing: 2px; }
.brand-subtitle { font-size: 16px; color: var(--text-secondary); margin-bottom: 48px; line-height: 1.6; }

.feature-list { display: flex; flex-direction: column; gap: 24px; }
.feature-item { display: flex; align-items: flex-start; gap: 16px; }
.feature-icon {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.feature-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.feature-desc { font-size: 13px; color: var(--text-muted); }

.login-right {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  border-left: 1px solid var(--border-light);
}

.login-form-wrap { width: 360px; }
.form-title { font-size: 26px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.form-desc { font-size: 14px; color: var(--text-muted); margin-bottom: 36px; }

.quick-login { margin-top: 32px; text-align: center; }
.quick-title { font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }
.quick-btns { display: flex; gap: 8px; justify-content: center; }

@media (max-width: 900px) {
  .login-left { display: none; }
  .login-right { width: 100%; border-left: none; }
}
</style>
