<template>
  <div class="fdisc-page">
    <!-- Навигация назад -->
    <div class="fdisc-nav">
      <button class="fdisc-back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Назад к чатам
      </button>
    </div>

    <!-- Обсуждение франшизы -->
    <div v-if="franchiseData" class="fdisc-chat-wrap">
      <FranchiseDiscussionChat
        :key="`fdisc-${franchiseId}-${topicSlug || 'general'}`"
        :franchise-id="franchiseId"
        :franchise-name="franchiseData.name"
        :franchise-poster="franchiseData.poster_image_url || franchiseData.poster_url || ''"
        :parts="sortedParts"
        :initial-topic-slug="topicSlug"
      />
    </div>

    <!-- Загрузка данных франшизы -->
    <div v-else-if="loading" class="fdisc-loading">
      Загрузка...
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="fdisc-error">
      Не удалось загрузить обсуждение
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient from '@/api/client'
import FranchiseDiscussionChat from '@/components/Chats/FranchiseDiscussionChat.vue'

const props = defineProps<{
  franchiseId: number
  topicSlug?: string | null
}>()

const router = useRouter()
const route = useRoute()

// Следим за изменениями URL
const currentFranchiseId = computed(() => Number(route.params.id))
const currentTopicSlug = computed(() => route.params.topicSlug || null)

interface FranchisePart {
  id: number
  title_ru: string
  title_en: string
  franchise_order: number
}

interface FranchiseData {
  id: number
  name: string
  poster_url: string
  poster_image_url: string
  entries: FranchisePart[]
}

const franchiseData = ref<FranchiseData | null>(null)
const loading = ref(true)
const error = ref(false)

const sortedParts = computed(() => 
  [...(franchiseData.value?.entries || [])].sort(
    (a, b) => a.franchise_order - b.franchise_order
  )
)

const goBack = () => {
  router.push('/chats')
}

const loadFranchise = async () => {
  loading.value = true
  error.value = false
  try {
    const res = await apiClient.get(`/anime/franchises/${currentFranchiseId.value}/`)
    franchiseData.value = res.data
  } catch (e) {
    console.error('Error loading franchise:', e)
    error.value = true
  } finally {
    loading.value = false
  }
}

// Загружаем при монтировании
onMounted(loadFranchise)

// Следим за сменой franchiseId в URL
watch(currentFranchiseId, (newId) => {
  if (newId) {
    loadFranchise()
  }
})
</script>

<style scoped>
.fdisc-page {
  min-height: 100vh;
  background: var(--surface-1);
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Фоновый узор */
.fdisc-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 10% 90%, rgba(255,126,179,0.03) 0%, transparent 40%),
    radial-gradient(circle at 90% 10%, rgba(168,197,226,0.03) 0%, transparent 40%);
  pointer-events: none;
}

/* Мобильная адаптация - отступ сверху под мобильную навигацию */
@media (max-width: 767px) {
  .fdisc-page {
    padding-top: 54px;
    box-sizing: border-box;
  }
}

.fdisc-nav {
  padding: 12px 16px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.fdisc-back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  font-size: .85rem;
  cursor: pointer;
  transition: all .15s var(--ease-petal);
}

.fdisc-back-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.fdisc-chat-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.fdisc-chat-wrap :deep(.franchise-chat) {
  height: calc(100vh - 60px);
}

.fdisc-loading,
.fdisc-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--text-tertiary);
  font-size: 1rem;
}

.fdisc-error {
  color: var(--danger);
}
</style>
