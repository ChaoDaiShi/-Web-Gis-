<!-- 报修列表 --><script setup>
import { ref } from 'vue';
const showModeMenu = ref(false);

const props = defineProps({
  repairs: {
    type: Array,
    default: () => []
  },
  expanded: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['itemClick', 'refresh', 'update:expanded', 'itemDoubleClick', 'modeSwitch', 'add', 'openNav']);

const filterStatus = ref('all');
const filteredRepairs = ref([]);

const statusMap = {
  0: { text: '待处理', class: 'status-pending' },
  1: { text: '处理中', class: 'status-processing' },
  2: { text: '已完成', class: 'status-completed' },
  3: { text: '已关闭', class: 'status-closed' }
};

const priorityMap = {
  1: { text: '低', class: 'priority-low' },
  2: { text: '中', class: 'priority-medium' },
  3: { text: '高', class: 'priority-high' }
};

function updateFilter() {
  if (filterStatus.value === 'all') {
    filteredRepairs.value = props.repairs;
  } else {
    filteredRepairs.value = props.repairs.filter(r => r.status === parseInt(filterStatus.value));
  }
}

function handleItemClick(repair) {
  emit('itemDoubleClick', repair);
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

function handleExpandClick() {
  emit('update:expanded', !props.expanded);
}

function handleContextMenu(e) {
  e.preventDefault();
}

import { watch } from 'vue';
watch(() => props.repairs, () => {
  updateFilter();
}, { immediate: true });

watch(filterStatus, () => {
  updateFilter();
});
</script>

<template>
  <aside 
    class="repair-list" 
    :class="{ expanded: expanded }"
    @contextmenu="handleContextMenu"
  >
    <div class="repair-list-header">
      <div class="header-top">
        <div class="mode-switch">
          <button class="mode-btn" @click="showModeMenu = !showModeMenu">
            服务 ▼
          </button>
          <div v-if="showModeMenu" class="mode-menu">
            <button @click="handleModeSwitch('lostFound')">失物招领</button>
            <button @click="handleModeSwitch('repair')">报修申请</button>
            <button @click="goToNavigation()">校园路径</button>
          </div>
        </div>
      </div>
      <div class="header-bottom">
        <h3>报修申请</h3>
        <button class="add-btn" @click="handleAdd">+ 添加</button>
      </div>
    </div>
    
    <div class="list-tip">点击箭头展开详细列表</div>
    
    <div class="filter-tabs">
      <button 
        v-for="tab in [{ key: 'all', label: '全部', count: repairs.length }, { key: '0', label: '待处理', count: repairs.filter(r => r.status === 0).length }, { key: '1', label: '处理中', count: repairs.filter(r => r.status === 1).length }, { key: '2', label: '已完成', count: repairs.filter(r => r.status === 2).length }]"
        :key="tab.key"
        :class="['filter-tab', { active: filterStatus === tab.key }]"
        @click="filterStatus = tab.key"
      >
        {{ tab.label }} ({{ tab.count }})
      </button>
    </div>
    
    <div class="repair-items">
      <div 
        v-for="repair in filteredRepairs" 
        :key="repair.repair_id"
        class="repair-item"
        @click="handleItemClick(repair)"
      >
        <div class="repair-header">
          <span class="repair-title">{{ repair.title }}</span>
          <span :class="['status-badge', statusMap[repair.status]?.class]">
            {{ statusMap[repair.status]?.text }}
          </span>
        </div>
        
        <div class="repair-info">
          <span :class="['priority-badge', priorityMap[repair.priority]?.class]">
            {{ priorityMap[repair.priority]?.text }}优先级
          </span>
          <span class="repair-location">📍 {{ repair.location || '未知位置' }}</span>
        </div>
        
        <div class="repair-time">
          {{ repair.create_time }}
        </div>
      </div>
      
      <div v-if="filteredRepairs.length === 0" class="empty-state">
        <p>暂无报修记录</p>
      </div>
    </div>
    
    <button class="expand-arrow" @click="handleExpandClick" :title="expanded ? '收起详情' : '展开详情'">
      {{ expanded ? '◀' : '▶' }}
    </button>
  </aside>
</template>

<style scoped>
.repair-list {
  width: var(--list-width);
  background: linear-gradient(135deg, #fffef5 0%, #fff9c4 100%);
  border-radius: 8px;
  transition: width 0.25s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.repair-list-inner {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.repair-list-header {
  position: sticky;
  top: 0;
  background: #fef3c7;
  color: #92400e;
  padding: 12px 16px;
  font-weight: 700;
  border-bottom: 1px solid #fde68a;
  z-index: 10;
}

.header-top {
  display: flex;
  justify-content: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.header-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.repair-list-header h3 {
  margin: 0;
  font-size: 16px;
}

.add-btn {
  background: #FF9800;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #F57C00;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(245, 124, 0, 0.4);
}

.list-tip {
  font-size: 11px;
  color: #999;
  padding: 4px 16px;
  text-align: center;
}

.filter-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  border-bottom: 1px solid #fde68a;
}

.filter-tab {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  transition: all 0.2s;
}

.filter-tab:hover {
  background: rgba(255, 255, 255, 0.8);
}

.filter-tab.active {
  background: #22c55e;
  color: #fff;
}

.repair-items {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.repair-items::-webkit-scrollbar {
  width: 8px;
}

.repair-items::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.repair-items::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #888 0%, #666 100%);
  border-radius: 4px;
  transition: background 0.3s;
}

.repair-items::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #666 0%, #444 100%);
}

.repair-item {
  padding: 12px;
  margin-bottom: 8px;
  background: #fff;
  border-radius: 8px;
  border-left: 4px solid #22c55e;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.repair-item:hover {
  background: #fffbeb;
  transform: translateX(2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.repair-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.repair-title {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-processing {
  background: #dbeafe;
  color: #1e40af;
}

.status-completed {
  background: #dcfce7;
  color: #166534;
}

.status-closed {
  background: #fee2e2;
  color: #991b1b;
}

.repair-info {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
}

.priority-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.priority-low {
  background: #dcfce7;
  color: #166534;
}

.priority-medium {
  background: #fef3c7;
  color: #92400e;
}

.priority-high {
  background: #fee2e2;
  color: #991b1b;
}

.repair-location {
  font-size: 12px;
  color: #6b7280;
}

.repair-time {
  font-size: 11px;
  color: #9ca3af;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.mode-switch {
  position: relative;
  display: inline-block;
  z-index: 11;
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

.expand-arrow {
  position: absolute;
  right: -16px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 52px;
  border: 0;
  border-radius: 0 6px 6px 0;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fff;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 2px 2px 8px rgba(245, 158, 11, 0.4);
  transition: all 0.2s;
  z-index: 10;
}

.expand-arrow:hover {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  box-shadow: 2px 2px 12px rgba(245, 158, 11, 0.6);
  transform: translateY(-50%) scale(1.05);
}
</style>