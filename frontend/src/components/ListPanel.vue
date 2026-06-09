<!-- 列表面板 -->
<script setup>
import { ref, computed } from 'vue';
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

const emit = defineEmits(['update:filterStatus', 'update:expanded', 'itemClick', 'itemDoubleClick', 'add', 'modeSwitch', 'openNav']);

const filteredMarkers = computed(() => {
  if (props.filterStatus === 'all') {
    return props.markers;
  }
  return props.markers.filter(item => {
    const itemType = item.type ?? 0;
    if (props.filterStatus === 'lost') {
      return itemType === 0;
    } else if (props.filterStatus === 'found') {
      return itemType === 1;
    }
    return true;
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
function goToNavigation() {
  emit('openNav');
  showModeMenu.value = false;
}
function hasCoordinates(item) {
  // 辅助函数：检查单个值是否有效
  const isValidCoord = (val) => {
    if (val === undefined || val === null || val === '' || val === 0) return false;
    const num = Number(val);
    return !isNaN(num) && isFinite(num);
  };
  
  // 检查 lng/lat
  const hasLngLat = isValidCoord(item.lng) && isValidCoord(item.lat);
  
  // 检查 longitude/latitude
  const hasLongitudeLatitude = isValidCoord(item.longitude) && isValidCoord(item.latitude);
  
  return hasLngLat || hasLongitudeLatitude;
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
            <button @click="goToNavigation">校园路径</button>
          </div>
        </div>
      </div>
      <div class="header-bottom">
        <h3>标记列表</h3>
        <span v-if="currentCampus" class="campus-tag">{{ currentCampus.name }}</span>
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
        :key="item.item_id"
        class="item-card"
        :class="{ expanded: expanded, 'status-lost': item.type === 0, 'status-found': item.type === 1 }"
        @click="handleItemClick(item)"
        @dblclick.stop="handleItemDoubleClick(item)"
      >
        <div class="item-card-header">
          <div class="item-card-title">
            <span class="status-badge" :class="item.type === 0 ? 'badge-lost' : 'badge-found'">
              {{ item.type === 0 ? '丢失' : '拾到' }}
            </span>
            {{ item.title }}
          </div>
          <span class="location-badge" :class="hasCoordinates(item) ? 'has-location' : 'no-location'">
            {{ hasCoordinates(item) ? '有位置' : '无位置' }}
          </span>
        </div>
        <div>ID：{{ item.item_id }}</div>
        <div class="item-card-detail">
          <div>描述：{{ item.description || "无" }}</div>
          <div>时间：{{ item.create_time || "未知" }}</div>
        </div>
      </li>
    </ul>
    
    <button class="expand-arrow" @click="handleExpandClick" :title="expanded ? '收起详情' : '展开详情'">
      {{ expanded ? '◀' : '▶' }}
    </button>
  </aside>
</template>

<style scoped>
.item-card {
  position: relative;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: all 0.2s;
}

.item-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

.item-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.item-card-title {
  flex: 1;
  font-weight: 500;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.badge-lost {
  background: #fee2e2;
  color: #dc2626;
}

.badge-found {
  background: #dcfce7;
  color: #16a34a;
}

.location-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.location-badge.has-location {
  background: #dcfce7;
  color: #16a34a;
}

.location-badge.no-location {
  background: #f3f4f6;
  color: #6b7280;
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
  width: 28px;
  height: 52px;
  border: 0;
  border-radius: 0 6px 6px 0;
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: #fff;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 2px 2px 8px rgba(34, 197, 94, 0.4);
  transition: all 0.2s;
  z-index: 10;
}

.expand-arrow:hover {
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  box-shadow: 2px 2px 12px rgba(34, 197, 94, 0.6);
  transform: translateY(-50%) scale(1.05);
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
  gap: 8px;
}

.campus-tag {
  padding: 4px 10px;
  background: #eff6ff;
  color: #3b82f6;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
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
  padding: 12px 28px;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
  font-size: 15px;
  color: #333;
  transition: background 0.2s;
}

.mode-menu button:hover {
  background: #f5f5f5;
}
</style>
