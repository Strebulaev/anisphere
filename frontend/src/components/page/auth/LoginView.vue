<template>
    <div class="auth-page">
      <div class="container auth-container">
        <div class="auth-card">
          <h2>Вход в аккаунт</h2>
          <p class="auth-subtitle">Войдите чтобы использовать все возможности</p>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <form @submit.prevent="handleLogin" class="auth-form">
            <div class="form-group">
              <label for="username">Имя пользователя</label>
              <input
                v-model="form.username"
                type="text"
                id="username"
                placeholder="Введите имя пользователя"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="password">Пароль</label>
              <input
                v-model="form.password"
                type="password"
                id="password"
                placeholder="Введите пароль"
                required
              />
            </div>
            
            <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
              {{ loading ? 'Вход...' : 'Войти' }}
            </button>
          </form>

          <div class="auth-divider">
            <span>или</span>
          </div>

          <button @click="handleGoogleLogin" class="btn btn-google btn-block">
            <svg class="google-icon" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Войти через Google
          </button>

          <div class="auth-footer">
            <p>Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link></p>
            <router-link to="/" class="back-link">← На главную</router-link>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { useAuthStore } from '@/stores/auth'
  import apiClient from '@/api/client'

  const router = useRouter()
  const authStore = useAuthStore()
  const loading = ref(false)
  const error = ref('')
  const form = ref({
    username: '',
    password: ''
  })

  const handleLogin = async () => {
    loading.value = true
    error.value = ''

    const result = await authStore.login(form.value.username, form.value.password)

    if (result.success) {
      router.push('/')
    } else {
      error.value = 'Неверное имя пользователя или пароль'
    }

    loading.value = false
  }

  const handleGoogleLogin = async () => {
    try {
      const response = await apiClient.get('/users/google/')
      const { auth_url } = response.data
      // Перенаправляем на Google OAuth
      window.location.href = auth_url
    } catch (error) {
      console.error('Google OAuth error:', error)
      // Fallback to ID token approach if available
      alert('Ошибка инициализации Google OAuth')
    }
  }
  </script>
  
  <style scoped>
  .auth-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  }
  
  .auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 64px);
    padding: 2rem 1rem;
  }
  
  .auth-card {
    background: white;
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    width: 100%;
    max-width: 400px;
  }
  
  .auth-card h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.5rem;
  }
  
  .auth-subtitle {
    color: #6b7280;
    margin-bottom: 1.5rem;
  }
  
  .error-message {
    background: #fee2e2;
    color: #dc2626;
    padding: 0.75rem;
    border-radius: 0.375rem;
    margin-bottom: 1rem;
    font-size: 0.875rem;
    text-align: center;
  }
  
  .auth-form {
    margin-bottom: 1.5rem;
  }

  .auth-divider {
    display: flex;
    align-items: center;
    margin: 1.5rem 0;
    color: #6b7280;
  }

  .auth-divider::before,
  .auth-divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #e5e7eb;
  }

  .auth-divider span {
    padding: 0 1rem;
    font-size: 0.875rem;
  }

  .btn-google {
    background: white;
    color: #3c4043;
    border: 1px solid #dadce0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    transition: all 0.2s;
  }

  .btn-google:hover {
    background: #f8f9fa;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }

  .google-icon {
    width: 18px;
    height: 18px;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-group label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.375rem;
  }
  
  .form-group input {
    width: 100%;
    padding: 0.625rem 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 1rem;
    transition: border-color 0.2s;
  }
  
  .form-group input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  .btn-block {
    width: 100%;
    padding: 0.75rem;
    font-size: 1rem;
  }
  
  .auth-footer {
    text-align: center;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
  
  .auth-footer p {
    color: #6b7280;
    margin-bottom: 1rem;
  }
  
  .auth-footer a {
    color: #3b82f6;
    text-decoration: none;
  }
  
  .back-link {
    display: inline-block;
    color: #6b7280;
    text-decoration: none;
    font-size: 0.875rem;
  }
  </style>