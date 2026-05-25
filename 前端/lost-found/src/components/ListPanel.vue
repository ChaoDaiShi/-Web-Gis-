<!-- 列表面板 -->
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
 let result;
 if (props.filterStatus === 'all') {
 result = props.markers;
 } else if (props.filterStatus === 'lost') {
 result = props.markers.filter(m => m.type === 0);
 } else if (props.filterStatus === 'found') {
 result = props.markers.filter(m => m.type === 1);
 } else {
 result = props.markers;
 }
 
 const currentUserId = localStorage.getItem('user_id');
 return [...result].sort((a, b) => {
 const isCurrentUserA = String(a.publisher_id) === String(currentUserId);
 const isCurrentUserB = String(b.publisher_id) === String(currentUserId);
 const isLostA = a.type === 0;
 const isLostB = b.type === 0;
 
 const priorityA = isCurrentUserA ? (isLostA ? 0 : 1) : (isLostA ? 2 : 3);
 const priorityB = isCurrentUserB ? (isLostB ? 0 : 1) : (isLostB ? 2 : 3);
 
 return priorityA - priorityB;
 });
});
const lostCount = computed(() => props.markers.filter(m => m.type === 0).length);
const foundCount = computed(() => props.markers.filter(m => m.type === 1).length);
function handleFilterChange(status) {
 emit('update:filterStatus', status);
}
function handleExpandClick() {
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
      <div class="list-tip">点击箭头展开详细列表</div>
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
    
    <button class="expand-arrow" @click="handleExpandClick" :title="expanded ? '收起详情' : '展开详情'">
      {{ expanded ? '◀' : '▶' }}
    </button>
  </aside>
</template>

<style scoped>
.list-panel {
  position: relative;
}

.item-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  margin: 0;
  list-style: none;
}

.item-list::-webkit-scrollbar {
  width: 8px;
}

.item-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.item-list::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #888 0%, #666 100%);
  border-radius: 4px;
  transition: background 0.3s;
}

.item-list::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #666 0%, #444 100%);
}

.expand-arrow {
  position: absolute;
  right: -16px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 64px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-left: none;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
  font-size: 16px;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
  transition: all 0.2s;
  z-index: 10;
}

.expand-arrow:hover {
  background: #f5f5f5;
  color: #333;
}

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
