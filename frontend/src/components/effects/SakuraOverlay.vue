<template>
  <div class="sakura-overlay" aria-hidden="true">
    <div 
      v-for="n in petalCount" 
      :key="n" 
      class="petal"
      :style="getPetalStyle(n)"
    >
      <svg viewBox="0 0 32 32" class="petal-svg">
        <path 
          d="M16 2C16 2 20 8 20 14C20 18 16 22 16 22C16 22 12 18 12 14C12 8 16 2 16 2Z" 
          fill="currentColor"
        />
        <path 
          d="M16 8C16 8 18 11 18 14C18 16 16 18 16 18C16 18 14 16 14 14C14 11 16 8 16 8Z" 
          fill="rgba(255,255,255,0.3)"
        />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
const petalCount = 20

const getPetalStyle = (n: number) => {
  const delay = Math.random() * -15
  const duration = 10 + Math.random() * 8
  const left = Math.random() * 100
  const size = 12 + Math.random() * 12
  const opacity = 0.25 + Math.random() * 0.2
  const blur = Math.random() > 0.7 ? 'blur(0.5px)' : 'none'
  
  return {
    '--delay': `${delay}s`,
    '--duration': `${duration}s`,
    '--left': `${left}%`,
    '--size': `${size}px`,
    '--opacity': opacity,
    '--blur': blur
  }
}
</script>

<style scoped>
.sakura-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9998;
  overflow: hidden;
  perspective: 1000px;
}

.petal {
  position: absolute;
  top: calc(var(--size) * -1);
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--accent);
  opacity: var(--opacity);
  filter: var(--blur);
  animation: sakura-fall var(--duration) linear infinite;
  animation-delay: var(--delay);
  will-change: transform, opacity;
}

.petal-svg {
  width: 100%;
  height: 100%;
}

@keyframes sakura-fall {
  0% {
    transform: translateY(-10vh) translateX(0) rotate(0deg) scale(0.8);
    opacity: 0;
  }
  5% {
    opacity: var(--opacity);
  }
  25% {
    transform: translateY(25vh) translateX(30px) rotate(90deg) scale(1);
  }
  50% {
    transform: translateY(50vh) translateX(-20px) rotate(180deg) scale(0.9);
  }
  75% {
    transform: translateY(75vh) translateX(25px) rotate(270deg) scale(1);
  }
  95% {
    opacity: var(--opacity);
  }
  100% {
    transform: translateY(110vh) translateX(-10px) rotate(360deg) scale(0.8);
    opacity: 0;
  }
}

/* Разные вариации анимации для разнообразия */
.petal:nth-child(odd) {
  animation-name: sakura-fall-alt;
}

@keyframes sakura-fall-alt {
  0% {
    transform: translateY(-10vh) translateX(0) rotate(0deg) scale(0.8);
    opacity: 0;
  }
  5% {
    opacity: var(--opacity);
  }
  25% {
    transform: translateY(25vh) translateX(-35px) rotate(-80deg) scale(1.1);
  }
  50% {
    transform: translateY(50vh) translateX(15px) rotate(-160deg) scale(0.85);
  }
  75% {
    transform: translateY(75vh) translateX(-30px) rotate(-240deg) scale(1.05);
  }
  95% {
    opacity: var(--opacity);
  }
  100% {
    transform: translateY(110vh) translateX(10px) rotate(-360deg) scale(0.75);
    opacity: 0;
  }
}

/* Третий тип анимации - более быстрый */
.petal:nth-child(3n) {
  animation-name: sakura-fall-fast;
  animation-duration: 8s;
}

@keyframes sakura-fall-fast {
  0% {
    transform: translateY(-10vh) translateX(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: var(--opacity);
  }
  100% {
    transform: translateY(110vh) translateX(50px) rotate(720deg);
    opacity: 0;
  }
}
</style>
