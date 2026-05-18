<script setup>import { ref, computed } from 'vue';
const showModeMenu = ref(false);
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
const emit = defineEmits(['update:filterStatus', 'update:expanded', 'itemClick', 'itemDoubleClick', 'add', 'modeSwitch']);
const filteredMarkers = computed(() => {
 if (props.filterStatus === 'all') {
 return props.markers;
 }
 else if (props.filterStatus === 'lost') {
 return props.markers.filter(m => m.status === 0);
 }
 else if (props.filterStatus === 'found') {
 return props.markers.filter(m => m.status === 1);
 }
 return props.markers;
});
const lostCount = computed(() => props.markers.filter(m => m.status === 0).length);
const foundCount = computed(() => props.markers.filter(m => m.status === 1).length);
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
function handleModeSwitch(mode) {
  emit('modeSwitch', mode);
  showModeMenu.value = false;
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
        <div class="mode-switch">
          <button class="mode-btn" @click="showModeMenu = !showModeMenu">
            服务 ▼
          </button>
          <div v-if="showModeMenu" class="mode-menu">
            <button @click="handleModeSwitch('lostFound')">失物招领</button>
            <button @click="handleModeSwitch('repair')">报修申请</button>
          </div>
        </div>
      </div>
      <div class="header-bottom">
        <h3>标记列表</h3>
        <button class="add-btn" @click="handleAdd">+ 添加</button>
      </div>
      <div class="list-tip">双击黄色区域展开详细列表（{{ markers.length }}/{{ markers.length }}）</div>
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
        :class="{ expanded: expanded, 'status-lost': item.status === 0, 'status-found': item.status === 1 }"
        @click="handleItemClick(item)"
        @dblclick.stop="handleItemDoubleClick(item)"
      >
        <div class="item-card-title">
          <span class="status-badge" :class="item.status === 0 ? 'badge-lost' : 'badge-found'">
            {{ item.status === 0 ? '丢失' : '拾到' }}
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
.header-top {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 8px;
}

.header-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mode-switch {
  position: relative;
  display: inline-block;
}

.mode-btn {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.mode-btn:hover {
  background: #45a049;
}

.mode-menu {
  position: absolute;
  left: 0;
  top: 100%;
  margin-top: 4px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  z-index: 100;
  min-width: 140px;
  max-width: 200px;
  overflow: hidden;
}

.mode-menu button {
  display: block;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  color: #333;
  transition: background 0.2s;
}

.mode-menu button:hover {
  background: #f5f5f5;
}
</style>