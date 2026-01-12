import axios from 'axios'
import { getApiBase } from '../config/runtimeConfig'

const api = axios.create({
  baseURL: getApiBase(),
  withCredentials: true
})

api.interceptors.request.use((config) => {
  config.baseURL = getApiBase()
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
