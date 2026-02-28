<template>
  <Toast :toasts="toasts" @remove="removeToast" @click="handleToastClick" />
</template>

<script setup lang="ts">
import { useToast as useToastComposable } from '@/composables/useToast'
import Toast from './Toast.vue'

const { toasts, removeToast } = useToastComposable()

const handleToastClick = (toast: any) => {
  if (toast.onClick) {
    toast.onClick()
  }
}
</script>
