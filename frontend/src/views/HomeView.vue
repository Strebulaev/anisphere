<template>
    <div class="home">
      <!-- <section class="hero">
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
      </section> -->
  
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
          <p>© 2024 AniSphere.</p>
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
    background: var(--color-background-surface);
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
    color: var(--color-primary);
    text-decoration: none;
  }
  
  .nav-links {
    display: flex;
    gap: 1rem;
  }
  
  .nav-link {
    color: var(--color-text-secondary);
    text-decoration: none;
    padding: 0.5rem 0.75rem;
    border-radius: 0.375rem;
    transition: background-color 0.2s;
  }
  
  .nav-link:hover {
    background-color: var(--color-border);
  }
  
  .nav-link.active {
    color: var(--color-primary);
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
    color: var(--color-text-secondary);
    border-color: var(--color-border);
    background: var(--color-background-surface);
  }
  
  .btn-outline:hover {
    background-color: var(--color-border);
  }
  
  .btn-primary {
    background-color: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }
  
  .btn-primary:hover {
    background-color: #2563eb;
  }
  
  .btn-secondary {
    background-color: var(--color-border);
    color: var(--color-text-primary);
  }
  
  .btn-secondary:hover {
    background-color: var(--color-border);
  }
  
  .btn-lg {
    padding: 0.75rem 1.5rem;
    font-size: 1.125rem;
  }
  
  /* Hero секция */
  .hero {
    flex: 1;
    background: var(--color-background);
    padding: 4rem 0;
    text-align: center;
  }
  
  .hero-title {
    font-size: 2rem;
    font-weight: 800;
    color: var(--color-text-primary);
    margin-bottom: 1rem;
  }
  
  .hero-title span {
    color: var(--color-primary);
  }
  
  .hero-subtitle {
    font-size: 1.25rem;
    color: var(--color-text-secondary);
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
    background: var(--color-background-surface);
  }
  
  .section-title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-text-primary);
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
    background: var(--color-background);
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
    color: var(--color-text-primary);
    margin-bottom: 0.5rem;
  }
  
  .feature-card p {
    color: var(--color-text-secondary);
    line-height: 1.5;
  }
  
  /* Футер */
  .footer {
    background: var(--color-background-surface);
    color: var(--color-text-muted);
    padding: 1.5rem 0;
    text-align: center;
    margin-top: auto;
  }
  </style>
  @media (min-width: 768px) {
    .hero-title {
      font-size: 3rem;
    }
  }

  @media (min-width: 1024px) {
    .hero-title {
      font-size: 3.5rem;
    }
  }