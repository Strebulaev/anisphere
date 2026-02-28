<template>
  <nav class="breadcrumbs" aria-label="Навигация">
    <ol class="breadcrumbs-list">
      <li class="breadcrumb-item">
        <router-link to="/" class="breadcrumb-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          <span class="breadcrumb-text">Главная</span>
        </router-link>
      </li>

      <li
        v-for="(item, index) in items"
        :key="index"
        class="breadcrumb-item"
      >
        <svg class="breadcrumb-separator" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
        
        <router-link
          v-if="item.to && index !== items.length - 1"
          :to="item.to"
          class="breadcrumb-link"
        >
          <span class="breadcrumb-text">{{ item.label }}</span>
        </router-link>
        
        <span v-else class="breadcrumb-current">
          {{ item.label }}
        </span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
interface BreadcrumbItem {
  label: string
  to?: string
}

interface Props {
  items?: BreadcrumbItem[]
}

const props = withDefaults(defineProps<Props>(), {
  items: () => []
})
</script>

<style scoped>
.breadcrumbs {
  padding: 0.75rem 0;
}

.breadcrumbs-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.breadcrumb-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.2s var(--transition-smooth);
  padding: 0.25rem 0.375rem;
  border-radius: 0.375rem;
}

.breadcrumb-link:hover {
  color: var(--color-accent);
  background-color: var(--color-background-active);
}

.breadcrumb-link svg {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.breadcrumb-link:hover svg {
  color: var(--color-accent);
}

.breadcrumb-separator {
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.breadcrumb-text {
  white-space: nowrap;
}

.breadcrumb-current {
  color: var(--color-text);
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.25rem 0.375rem;
}

@media (max-width: 768px) {
  .breadcrumbs {
    padding: 0.5rem 0;
  }

  .breadcrumb-link,
  .breadcrumb-current {
    font-size: 0.8125rem;
    padding: 0.1875rem 0.25rem;
  }
}
</style>
