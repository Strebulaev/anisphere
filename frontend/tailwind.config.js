/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      screens: {
        // Мобильные устройства
        'xs': { 'raw': '(min-width: 320px)' },
        'sm': { 'raw': '(min-width: 375px)' },
        'md': { 'raw': '(min-width: 414px)' },
        'lg': { 'raw': '(min-width: 428px)' },
        'xl': { 'raw': '(min-width: 480px)' },
        
        // Планшеты
        'tablet-sm': { 'raw': '(min-width: 600px)' },
        'tablet': { 'raw': '(min-width: 768px)' },
        'tablet-lg': { 'raw': '(min-width: 834px)' },
        'tablet-xl': { 'raw': '(min-width: 1024px)' },
        
        // Ноутбуки
        'laptop-sm': { 'raw': '(min-width: 1152px)' },
        'laptop': { 'raw': '(min-width: 1280px)' },
        'laptop-lg': { 'raw': '(min-width: 1366px)' },
        'laptop-xl': { 'raw': '(min-width: 1440px)' },
        
        // Десктопы
        'desktop-sm': { 'raw': '(min-width: 1536px)' },
        'desktop': { 'raw': '(min-width: 1600px)' },
        'desktop-lg': { 'raw': '(min-width: 1680px)' },
        'desktop-xl': { 'raw': '(min-width: 1920px)' },
        'desktop-2xl': { 'raw': '(min-width: 2560px)' },
        'desktop-3xl': { 'raw': '(min-width: 3840px)' },
      },
      colors: {
        // Фоновые цвета — глубокая ночь с оттенками сакуры
        background: {
          DEFAULT: '#090613',
          secondary: '#0f0b1a',
          surface: '#151023',
          active: '#1c162c',
        },
        
        // Текстовые цвета
        text: {
          DEFAULT: '#b8aec8',
          primary: '#f5f0f8',
          secondary: '#b8aec8',
          tertiary: '#6d607a',
          disabled: '#443a54',
        },
        
        // Акцентные цвета — нежная сакура
        accent: {
          DEFAULT: '#ff7eb3',
          hover: '#ff94ab',
          active: '#e86a9e',
        },
        
        accentPink: {
          DEFAULT: '#ff7eb3',
          hover: '#ff94ab',
        },
        
        accentTeal: {
          DEFAULT: '#a8c5e2',
        },
        
        accentOrange: {
          DEFAULT: '#ffcba4',
        },
        
        // Разделители
        divider: {
          DEFAULT: '#2a2244',
          weak: '#231c38',
          light: '#1c162c',
        },
        
        // Статусы просмотра
        status: {
          watching: '#ff7eb3',
          completed: '#8ed4a8',
          planned: '#ffd592',
          dropped: '#ff8a8a',
          onhold: '#b8aec8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans JP', 'Zen Kaku Gothic New', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        display: ['Syne', 'Inter', 'Noto Sans JP', 'sans-serif'],
        jp: ['Noto Sans JP', 'Zen Kaku Gothic New', 'sans-serif'],
      },
      fontSize: {
        'h1': ['32px', { lineHeight: '1.2', fontWeight: '700' }],
        'h2': ['24px', { lineHeight: '1.3', fontWeight: '600' }],
        'h3': ['20px', { lineHeight: '1.3', fontWeight: '600' }],
        'h4': ['18px', { lineHeight: '1.4', fontWeight: '500' }],
        'base': ['16px', { lineHeight: '1.5', fontWeight: '400' }],
        'secondary': ['14px', { lineHeight: '1.5', fontWeight: '400' }],
        'small': ['12px', { lineHeight: '1.5', fontWeight: '400' }],
        'micro': ['10px', { lineHeight: '1.5', fontWeight: '400' }],
      },
      spacing: {
        'xs': '4px',
        'sm': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '24px',
        '2xl': '32px',
        '3xl': '48px',
      },
      borderRadius: {
        'card': '12px',
        'button': '10px',
        'modal': '16px',
      },
      boxShadow: {
        'card': '0 4px 20px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255,126,179,0.08)',
        'card-hover': '0 8px 32px rgba(0, 0, 0, 0.6), 0 0 20px rgba(255,126,179,0.15)',
        'modal': '0 24px 80px rgba(0, 0, 0, 0.85), 0 0 0 1px rgba(255,126,179,0.12)',
        'glow': '0 0 20px rgba(255,126,179,0.3)',
        'glow-sm': '0 0 10px rgba(255,126,179,0.15)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'fade-out': 'fadeOut 0.15s ease-in',
        'slide-down': 'slideDown 0.2s ease',
        'slide-up': 'slideUp 0.2s ease',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 120s linear infinite',
        'spin-medium': 'spin 10s linear infinite',
        'spin-fast': 'spin 6s linear infinite',
        'shimmer': 'shimmer 1.5s ease-in-out infinite',
        'glitch': 'glitch 0.3s ease-in-out',
        'float': 'floatPetal 4s ease-in-out infinite',
        'bloom': 'bloomIn 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%, 100%': { backgroundPosition: '200% 0' },
          '50%': { backgroundPosition: '-200% 0' },
        },
        glitch: {
          '0%, 100%': { transform: 'translate(0)' },
          '20%': { transform: 'translate(-2px, 2px)' },
          '40%': { transform: 'translate(-2px, -2px)' },
          '60%': { transform: 'translate(2px, 2px)' },
          '80%': { transform: 'translate(2px, -2px)' },
        },
        floatPetal: {
          '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
          '25%': { transform: 'translateY(-4px) rotate(2deg)' },
          '50%': { transform: 'translateY(-2px) rotate(-1deg)' },
          '75%': { transform: 'translateY(-6px) rotate(1deg)' },
        },
        bloomIn: {
          '0%': { opacity: '0', transform: 'scale(0.9) translateY(10px)' },
          '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
      },
      backdropBlur: {
        'nav': '12px',
        'panel': '16px',
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.22, 1, 0.36, 1)',
        'petal': 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
}