<template>
  <div class="pagination" v-if="totalPages > 1">
    <div class="pagination-info">
      Страница {{ currentPage }} из {{ totalPages }}
      <span class="pagination-total">(всего {{ totalItems }})</span>
    </div>

    <div class="pagination-controls">
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="pagination-btn pagination-btn-prev"
        type="button"
        aria-label="Предыдущая страница"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        <span>Предыдущая</span>
      </button>

      <div class="pagination-pages">
        <template v-for="page in visiblePages" :key="page">
          <button
            v-if="page !== '...'"
            @click="goToPage(page as number)"
            :class="['pagination-page', { active: page === currentPage }]"
            type="button"
          >
            {{ page }}
          </button>
          <span v-else class="pagination-ellipsis">...</span>
        </template>
      </div>

      <button
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="pagination-btn pagination-btn-next"
        type="button"
        aria-label="Следующая страница"
      >
        <span>Следующая</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  currentPage: number
  totalPages: number
  totalItems?: number
  maxVisible?: number
}

const props = withDefaults(defineProps<Props>(), {
  totalItems: 0,
  maxVisible: 5
})

const emit = defineEmits<{
  'update:currentPage': [page: number]
}>()

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const { currentPage, totalPages, maxVisible } = props
  const halfVisible = Math.floor(maxVisible / 2)

  if (totalPages <= maxVisible) {
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)

    let startPage = Math.max(2, currentPage - halfVisible)
    let endPage = Math.min(totalPages - 1, currentPage + halfVisible)

    if (currentPage - halfVisible <= 2) {
      endPage = Math.min(totalPages - 1, maxVisible - 1)
    }

    if (currentPage + halfVisible >= totalPages - 1) {
      startPage = Math.max(2, totalPages - maxVisible + 2)
    }

    if (startPage > 2) {
      pages.push('...')
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i)
    }

    if (endPage < totalPages - 1) {
      pages.push('...')
    }

    pages.push(totalPages)
  }

  return pages
})

const goToPage = (page: number) => {
  if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
    emit('update:currentPage', page)
  }
}
</script>

<style scoped>
.pagination {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
  padding: 1.5rem 0;
}

.pagination-info {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
  text-align: center;
}

.pagination-total {
  color: var(--color-text-tertiary);
  font-weight: 400;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pagination-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  white-space: nowrap;
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  background-color: var(--color-background-active);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(58, 134, 255, 0.2);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination-btn svg {
  flex-shrink: 0;
}

.pagination-pages {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.pagination-page {
  min-width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background-color: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.pagination-page:hover {
  border-color: var(--color-accent);
  background-color: var(--color-background-active);
}

.pagination-page.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
  font-weight: 700;
}

.pagination-ellipsis {
  min-width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  font-size: 1.25rem;
  font-weight: 700;
}

@media (max-width: 768px) {
  .pagination {
    gap: 0.75rem;
    padding: 1rem 0;
  }

  .pagination-info {
    font-size: 0.8125rem;
  }

  .pagination-controls {
    flex-wrap: wrap;
    justify-content: center;
  }

  .pagination-btn span:not(.pagination-btn svg) {
    display: none;
  }

  .pagination-btn {
    padding: 0.5rem;
  }

  .pagination-page {
    min-width: 36px;
    height: 36px;
    font-size: 0.8125rem;
  }

  .pagination-ellipsis {
    min-width: 36px;
    height: 36px;
    font-size: 1.125rem;
  }
}
</style>
