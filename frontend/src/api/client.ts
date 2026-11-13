import axios from 'axios'

// Базовый URL — через vite proxy идёт на backend
const api = axios.create({ baseURL: '/api' })

// Прокидываем JWT-токен из localStorage в каждый запрос
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401 — разлогиниваем
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
