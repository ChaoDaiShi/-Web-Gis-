<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  labelKey: { type: String, default: 'label' },
  valueKey: { type: String, default: 'value' },
  size: { type: Number, default: 200 }
})

const COLORS = ['#667eea', '#f5576c', '#4facfe', '#43e97b', '#fa8231', '#a855f7', '#14b8a6', '#94a3b8']

const segments = computed(() => {
  const raw = props.items || []
  const normalized = raw.map((item, i) => ({
    label: item[props.labelKey] ?? item.category ?? item.status ?? `项${i + 1}`,
    value: Number(item[props.valueKey] ?? item.count ?? item.action_count ?? 0)
  })).filter((x) => x.value > 0)

  const total = normalized.reduce((s, x) => s + x.value, 0)
  if (!total) return []

  let angle = 0
  return normalized.map((item, i) => {
    const sweep = (item.value / total) * 360
    const seg = {
      ...item,
      percent: ((item.value / total) * 100).toFixed(1),
      start: angle,
      end: angle + sweep,
      color: COLORS[i % COLORS.length]
    }
    angle += sweep
    return seg
  })
})

const hasData = computed(() => segments.value.length > 0)

function polar(cx, cy, r, deg) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function arcPath(cx, cy, r, start, end) {
  if (end - start >= 359.99) {
    return `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} Z`
  }
  const s = polar(cx, cy, r, start)
  const e = polar(cx, cy, r, end)
  const large = end - start > 180 ? 1 : 0
  return `M ${cx} ${cy} L ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y} Z`
}
</script>

<template>
  <div class="pie-wrap">
    <svg v-if="hasData" :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" class="pie-svg">
      <g v-for="(seg, i) in segments" :key="i">
        <path
          :d="arcPath(size / 2, size / 2, size / 2 - 4, seg.start, seg.end)"
          :fill="seg.color"
          stroke="#fff"
          stroke-width="2"
        />
      </g>
      <circle :cx="size / 2" :cy="size / 2" :r="size / 5" fill="#fff" />
    </svg>
    <div v-else class="pie-empty">暂无数据</div>
    <ul v-if="hasData" class="pie-legend">
      <li v-for="(seg, i) in segments" :key="'l-' + i">
        <span class="dot" :style="{ background: seg.color }" />
        <span class="name">{{ seg.label }}</span>
        <span class="val">{{ seg.value }} ({{ seg.percent }}%)</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.pie-wrap {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  justify-content: center;
}
.pie-svg { flex-shrink: 0; }
.pie-empty {
  width: 200px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 14px;
  background: #f0f2f5;
  border-radius: 50%;
}
.pie-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
  min-width: 140px;
}
.pie-legend li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}
.name { color: #555; flex: 1; }
.val { color: #2c3e50; font-weight: 600; }
</style>
