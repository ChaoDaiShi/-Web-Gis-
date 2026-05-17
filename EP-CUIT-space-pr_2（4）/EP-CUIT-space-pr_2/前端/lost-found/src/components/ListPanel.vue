<script setup>import { computed } from 'vue';
const props = defineProps({
 markers: {
 type: Array,
 default: () => []
 },
 filterStatus: {
 type: String,
 default: 'all'
 },
 expanded: {
 type: Boolean,
 default: false
 }
});
const emit = defineEmits(['update:filterStatus', 'update:expanded', 'itemClick', 'itemDoubleClick', 'add']);
const filteredMarkers = computed(() => {
 let result = [];
 if (props.filterStatus === 'all') {
 result = [...props.markers];
 }
 else if (props.filterStatus === 'lost') {
 result = props.markers.filter(m => m.type === 0);
 }
 else if (props.filterStatus === 'found') {
 result = props.markers.filter(m => m.type === 1);
 } else {
 result = [...props.markers];
 }
 
 const currentUserId = localStorage.getItem('user_id');
 
 result.sort((a, b) => {
 const getPriority = (item) => {
 const isOwn = String(item.publisher_id) === String(currentUserId);
 const isLost = item.type === 0;
 
 if (isOwn && isLost) return 1;
 if (isOwn && !isLost) return 2;
 if (!isOwn && isLost) return 3;
 return 4;
 };
 
 return getPriority(a) - getPriority(b);
 });
 
 return result;
});
const lostCount = computed(() => props.markers.filter(m => m.type === 0).length);
const foundCount = computed(() => props.markers.filter(m => m.type === 1).length);
function handleFilterChange(status) {
 emit('update:filterStatus', status);
}
function handleDoubleClick() {
 emit('update:expanded', !props.expanded);
}
function handleItemClick(item) {
 emit('itemClick', item);
}
function handleItemDoubleClick(item) {
 emit('itemDoubleClick', item);
}
function handleAdd() {
 emit('add');
}
function hasCoordinates(item) {
 return item.latitude !== undefined && item.latitude !== null && item.latitude !== '';
}
</script>

<template>
  <aside
    class="list-panel"
    :class="{ expanded: expanded }"
    title="双击展开/收起详情"
    @dblclick="handleDoubleClick"
  >
    <div class="list-header">
      <div class="header-top">
        <span>标记列表</span>
        <button class="add-btn" @click="handleAdd">+ 添加</button>
      </div>
      <div class="list-tip">双击黄色区域展开详细列表（{{ filteredMarkers.length }}/50）</div>
      <div class="filter-tabs">
        <button
          :class="{ active: filterStatus === 'all' }"
          @click="handleFilterChange('all')"
        >
          全部 ({{ markers.length }})
        </button>
        <button
          :class="{ active: filterStatus === 'lost' }"
          @click="handleFilterChange('lost')"
        >
          丢失 ({{ lostCount }})
        </button>
        <button
          :class="{ active: filterStatus === 'found' }"
          @click="handleFilterChange('found')"
        >
          拾到 ({{ foundCount }})
        </button>
      </div>
    </div>
    <ul class="item-list">
      <li
        v-for="item in filteredMarkers"
        :key="item.id"
        class="item-card"
        :class="{ expanded: expanded, 'status-lost': item.type === 0, 'status-found': item.type === 1 }"
        @click="handleItemClick(item)"
        @dblclick.stop="handleItemDoubleClick(item)"
      >
        <div class="item-card-title">
          <span class="status-badge" :class="item.type === 0 ? 'badge-lost' : 'badge-found'">
            {{ item.type === 0 ? '丢失' : '拾到' }}
          </span>
          {{ item.title }}
          <span v-if="!hasCoordinates(item)" style="color: #999; font-size: 12px;">(无位置)</span>
        </div>
        <div>ID：{{ item.id }}</div>
        <div class="item-card-detail">
          <div>描述：{{ item.detail || "无" }}</div>
          <div>时间：{{ item.time || "未知" }}</div>
        </div>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
</style>