<script setup>
defineProps({
  text: {
    type: String,
    default: '加载中...'
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  }
});
</script>

<template>
  <div class="loading-spinner" :class="size">
    <div class="spinner"></div>
    <span v-if="text" class="loading-text">{{ text }}</span>
  </div>
</template>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.spinner {
  border-radius: 50%;
  border-style: solid;
  animation: spin 1s linear infinite;
}

.loading-spinner.sm .spinner {
  width: 24px;
  height: 24px;
  border-width: 2px;
  border-color: #2563eb transparent #2563eb transparent;
}

.loading-spinner.md .spinner {
  width: 40px;
  height: 40px;
  border-width: 3px;
  border-color: #2563eb transparent #2563eb transparent;
}

.loading-spinner.lg .spinner {
  width: 60px;
  height: 60px;
  border-width: 4px;
  border-color: #2563eb transparent #2563eb transparent;
}

.loading-text {
  font-size: 14px;
  color: #6b7280;
}

.loading-spinner.sm .loading-text {
  font-size: 12px;
}

.loading-spinner.lg .loading-text {
  font-size: 16px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>