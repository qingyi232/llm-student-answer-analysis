import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('casa_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res.data,
  err => {
    const msg = err.response?.data?.msg || '请求失败'
    if (err.response?.status === 401) {
      localStorage.removeItem('casa_token')
      localStorage.removeItem('casa_user')
      window.location.hash = '#/login'
    }
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export const authApi = {
  login: data => api.post('/auth/login', data),
  register: data => api.post('/auth/register', data),
  getInfo: () => api.get('/auth/info')
}

export const userApi = {
  getList: params => api.get('/users', { params }),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: id => api.delete(`/users/${id}`)
}

export const courseApi = {
  getList: () => api.get('/courses'),
  create: data => api.post('/courses', data),
  update: (id, data) => api.put(`/courses/${id}`, data),
  delete: id => api.delete(`/courses/${id}`),
  getStudents: id => api.get(`/courses/${id}/students`),
  enroll: (id, data) => api.post(`/courses/${id}/enroll`, data)
}

export const questionApi = {
  getList: params => api.get('/questions', { params }),
  getDetail: id => api.get(`/questions/${id}`),
  create: data => api.post('/questions', data),
  update: (id, data) => api.put(`/questions/${id}`, data),
  delete: id => api.delete(`/questions/${id}`)
}

export const assignmentApi = {
  getList: params => api.get('/assignments', { params }),
  getDetail: id => api.get(`/assignments/${id}`),
  create: data => api.post('/assignments', data),
  delete: id => api.delete(`/assignments/${id}`)
}

export const answerApi = {
  submit: data => api.post('/answers/submit', data),
  batchSubmit: data => api.post('/answers/batch-submit', data),
  getList: params => api.get('/answers', { params })
}

export const analysisApi = {
  analyze: data => api.post('/analysis/analyze', data),
  batchAnalyze: data => api.post('/analysis/batch', data),
  getResult: answerId => api.get(`/analysis/${answerId}`)
}

export const feedbackApi = {
  review: (id, data) => api.put(`/feedback/${id}/review`, data)
}

export const statsApi = {
  dashboard: () => api.get('/stats/dashboard'),
  scoreDistribution: () => api.get('/stats/score-distribution'),
  dimensionAvg: () => api.get('/stats/dimension-avg')
}

export const monitorApi = {
  getStatus: () => api.get('/monitor/status')
}

export const exportApi = {
  gradingCsv: async (assignmentId) => {
    const token = localStorage.getItem('casa_token')
    const params = assignmentId ? `?assignment_id=${assignmentId}` : ''
    const res = await fetch(`/api/export/grading-csv${params}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('export failed')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `grading_export_${new Date().toISOString().slice(0,10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  },
  feedbackReport: async (answerId, studentName) => {
    const token = localStorage.getItem('casa_token')
    const res = await fetch(`/api/export/feedback-report/${answerId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) throw new Error('export failed')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${studentName || 'feedback'}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }
}

export default api
