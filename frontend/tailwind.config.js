/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Фоновые цвета
        background: {
          DEFAULT: '#0A0A0A',
          secondary: '#111111',
          surface: '#1A1A1A',
          active: '#222222',
        },
        
        // Текстовые цвета
        text: {
          DEFAULT: '#373737',
          primary: 'rgba(255, 255, 255, 0.9)',
          secondary: '#CCCCCC',
          tertiary: '#888888',
          disabled: '#666666',
        },
        
        // Акцентные цвета
        accent: {
          DEFAULT: '#3A86FF',
          hover: '#2A76FF',
          active: '#1A66FF',
        },
        
        accentPink: {
          DEFAULT: '#FF2A6D',
          hover: '#FF1A5D',
        },
        
        accentTeal: {
          DEFAULT: '#00D4AA',
        },
        
        accentOrange: {
          DEFAULT: '#FFB347',
        },
        
        // Разделители
        divider: {
          DEFAULT: '#2A2A2A',
          weak: '#333333',
          light: '#444444',
        },
        
        // Статусы просмотра
        status: {
          watching: '#3A86FF',
          completed: '#00D4AA',
          planned: '#FFB347',
          dropped: '#FF2A6D',
          onhold: '#888888',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['Orbitron', 'sans-serif'],
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
        'card': '8px',
        'button': '8px',
        'modal': '12px',
      },
      boxShadow: {
        'card': '0 4px 20px rgba(0, 0, 0, 0.08)',
        'card-hover': '0 20px 50px rgba(0, 0, 0, 0.15)',
        'modal': '-4px 0 24px rgba(0, 0, 0, 0.5)',
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
      },
      backdropBlur: {
        'nav': '10px',
        'panel': '12px',
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0.0, 0.2, 1)',
      },
    },
  },
  plugins: [],
}