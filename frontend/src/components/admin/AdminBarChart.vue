<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  labelKey: { type: String, default: 'label' },
  valueKey: { type: String, default: 'value' }
})

const COLORS = ['#3498db', '#9b59b6', '#e74c3c', '#2ecc71', '#f39c12', '#1abc9c']

const bars = computed(() => {
  const raw = props.items || []
  const normalized = raw.map((item, i) => ({
    label: item[props.labelKey] ?? item.date ?? item.username ?? `项${i + 1}`,
    value: Number(item[props.valueKey] ?? item.count ?? item.action_count ?? 0)
  }))
  const max = Math.max(...normalized.map((x) => x.value), 1)
  return normalized.map((item, i) => ({
    ...item,
    width: `${(item.value / max) * 100}%`,
    color: COLORS[i % COLORS.length]
  }))
})

const hasData = computed(() => bars.value.some((b) => b.value > 0))
</script>

<template>
  <div class="bar-chart">
    <div v-if="!hasData" class="bar-empty">暂无数据</div>
    <div v-for="(bar, i) in bars" :key="i" class="bar-row">
      <span class="bar-label" :title="bar.label">{{ bar.label }}</span>
      <div class="bar-track">
        <div class="bar-fill" :style="{ width: bar.width, background: bar.color }" />
      </div>
      <span class="bar-value">{{ bar.value }}</span>
    </div>
  </div>
</template>

<style scoped>
.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-empty { color: #999; font-size: 14px; text-align: center; padding: 24px; }
.bar-row {
  display: grid;
  grid-template-columns: 88px 1fr 40px;
  align-items: center;
  gap: 10px;
}
.bar-label {
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bar-track {
  height: 22px;
  background: #e8ecf1;
  border-radius: 4px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 4px;
  min-width: 4px;
  transition: width 0.4s ease;
}
.bar-value {
  font-size: 13px;
  font-weight: 600;
  color: #2c3e50;
  text-align: right;
}
</style>
