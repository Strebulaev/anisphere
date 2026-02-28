<template>
    <div class="home">
      <!-- Hero секция -->
      <section class="hero">
        <div class="container">
          <h1 class="hero-title">Твоя вселенная <span>аниме</span></h1>
          <p class="hero-subtitle">
            Создавай плейлисты, находи озвучки, обсуждай с комьюнити. Всё в одном месте.
          </p>
          <div class="hero-actions">
            <router-link to="/anime" class="btn btn-primary btn-lg">Смотреть аниме</router-link>
            <router-link to="/register" class="btn btn-secondary btn-lg">Присоединиться</router-link>
          </div>
        </div>
      </section>
  
      <!-- Функции -->
      <section class="features">
        <div class="container">
          <h2 class="section-title">Возможности</h2>
          <div class="features-grid">
            <div class="feature-card">
              <div class="feature-icon">📁</div>
              <h3>Умные плейлисты</h3>
              <p>Создавай коллекции с живыми ссылками на просмотр. Автоматическое определение аниме по ссылке.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">🎙️</div>
              <h3>База озвучек</h3>
              <p>Полная информация о русских озвучках, актёрах и студиях. Отмечай любимые озвучки.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">🎬</div>
              <h3>Reactor лента</h3>
              <p>Короткие видео, мемы, реакции от сообщества. Свой TikTok для аниме-тематики.</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">👥</div>
              <h3>Сообщества</h3>
              <p>Группы по интересам, обсуждения, совместные плейлисты. Найди своих!</p>
            </div>
          </div>
        </div>
      </section>
  
      <!-- Футер -->
      <footer class="footer">
        <div class="container">
          <p>© 2026 AniSphere.</p>
        </div>
      </footer>
    </div>
  </template>
  
  <script setup lang="ts">

  </script>
  
  <style scoped>
  .home {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  /* Навигация */
  .navbar {
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  
  .container {
    margin: 0 auto;
    padding: 0 max(var(--space-lg), 2vw);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .nav-left {
    display: flex;
    align-items: center;
    gap: 2rem;
  }
  
  .logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: #3b82f6;
    text-decoration: none;
  }
  
  .nav-links {
    display: flex;
    gap: 1rem;
  }
  
  .nav-link {
    color: #4b5563;
    text-decoration: none;
    padding: 0.5rem 0.75rem;
    border-radius: 0.375rem;
    transition: background-color 0.2s;
  }
  
  .nav-link:hover {
    background-color: #f3f4f6;
  }
  
  .nav-link.active {
    color: #3b82f6;
    font-weight: 600;
  }
  
  .nav-right {
    display: flex;
    gap: 0.75rem;
  }
  
  /* Кнопки */
  .btn {
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-weight: 500;
    text-decoration: none;
    display: inline-block;
    transition: all 0.2s;
    border: 1px solid transparent;
    cursor: pointer;
  }
  
  .btn-outline {
    color: #4b5563;
    border-color: #d1d5db;
    background: white;
  }
  
  .btn-outline:hover {
    background-color: #111111;
  }
  
  .btn-primary {
    background-color: #3b82f6;
    color: white;
    border-color: #3b82f6;
  }
  
  .btn-primary:hover {
    background-color: #2563eb;
  }
  
  .btn-secondary {
    background-color: #e5e7eb;
    color: #374151;
  }
  
  .btn-secondary:hover {
    background-color: #d1d5db;
  }
  
  .btn-lg {
    padding: 0.75rem 1.5rem;
    font-size: 1.125rem;
  }
  
  /* Hero секция */
  .hero {
    flex: 1;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    padding: 4rem 0;
    text-align: center;
  }
  
  .hero-title {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 1rem;
  }
  
  .hero-title span {
    color: #3b82f6;
  }
  
  .hero-subtitle {
    font-size: 1.25rem;
    color: #6b7280;
    max-width: 600px;
    margin: 0 auto 2rem;
    line-height: 1.6;
  }
  
  .hero-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }
  
  /* Функции */
  .features {
    padding: 4rem 0;
    background: white;
  }
  
  .section-title {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin: 0 auto;
  }
  
  .feature-card {
    background: #222222;
    padding: 1.5rem;
    border-radius: 0.75rem;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  
  .feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  }
  
  .feature-icon {
    font-size: 2rem;
    margin-bottom: 1rem;
  }
  
  .feature-card h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.5rem;
  }
  
  .feature-card p {
    color: #6b7280;
    line-height: 1.5;
  }
  
  /* Футер */
  .footer {
    background: #ffffff;
    color: #9ca3af;
    padding: 1.5rem 0;
    text-align: center;
    margin-top: auto;
  }
  </style>
