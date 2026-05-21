<script setup>
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

const emit = defineEmits(['itemClick', 'refresh', 'update:expanded', 'itemDoubleClick', 'modeSwitch', 'add']);

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

function handleDoubleClick() {
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
  <div 
    class="list-panel repair-list" 
    :class="{ expanded: expanded }"
    title="双击展开/收起详情"
    @dblclick="handleDoubleClick"
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
          </div>
        </div>
      </div>
      <div class="header-bottom">
        <h3>报修列表</h3>
        <button class="add-btn" @click="handleAdd">+ 添加</button>
      </div>
    </div>
    
    <div class="list-tip">双击黄色区域展开详细列表（{{ repairs.length }}/{{ repairs.length }}）</div>
    
    <div class="filter-tabs">
      <button 
        v-for="tab in [{ key: 'all', label: '全部' }, { key: '0', label: '待处理' }, { key: '1', label: '处理中' }, { key: '2', label: '已完成' }]"
        :key="tab.key"
        :class="['filter-tab', { active: filterStatus === tab.key }]"
        @click="filterStatus = tab.key"
      >
        {{ tab.label }}
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
          <span class="repair-location">📍 {{ repair.lng?.toFixed(4) }}, {{ repair.lat?.toFixed(4) }}</span>
        </div>
        
        <div class="repair-time">
          {{ repair.create_time }}
        </div>
      </div>
      
      <div v-if="filteredRepairs.length === 0" class="empty-state">
        <p>暂无报修记录</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.repair-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.repair-list-header {
  padding: 8px 16px;
  border-bottom: 1px solid #e5e5e5;
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

.add-btn {
  background: #FF9800;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.2s;
}

.add-btn:hover {
  background: #F57C00;
}

.repair-list-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.refresh-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px 8px;
  border-radius: 4px;
}

.refresh-btn:hover {
  background: #f0f0f0;
}

.filter-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  border-bottom: 1px solid #e5e5e5;
}

.filter-tab {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  color: #666;
  transition: all 0.2s;
}

.filter-tab:hover {
  background: #f0f0f0;
}

.filter-tab.active {
  background: #22c55e;
  color: #fff;
}

.repair-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.repair-item {
  padding: 12px;
  margin-bottom: 8px;
  background: #fff;
  border-radius: 6px;
  border-left: 4px solid #22c55e;
  cursor: pointer;
  transition: all 0.2s;
}

.repair-item:hover {
  background: #f9f9f9;
  transform: translateX(2px);
}

.repair-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.repair-title {
  font-weight: 500;
  color: #333;
}

.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
}

.status-pending {
  background: #fff3cd;
  color: #856404;
}

.status-processing {
  background: #cce5ff;
  color: #004085;
}

.status-completed {
  background: #d4edda;
  color: #155724;
}

.status-closed {
  background: #f8d7da;
  color: #721c24;
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
  font-size: 11px;
  color: #666;
}

.repair-time {
  font-size: 11px;
  color: #999;
}

.repair-detail {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ddd;
  background: #fafafa;
  padding: 12px;
  border-radius: 4px;
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-section {
  display: flex;
  margin-bottom: 6px;
  font-size: 12px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  color: #666;
  font-weight: 500;
  min-width: 70px;
}

.detail-value {
  color: #333;
  flex: 1;
}

.detail-images {
  margin-top: 8px;
}

.images-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.detail-image {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid #ddd;
}

.detail-image:hover {
  border-color: #22c55e;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.list-tip {
  font-size: 11px;
  color: #999;
  padding: 4px 16px;
  text-align: center;
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

.repair-item.expanded {
  border-left-color: #dc3545;
  background: #fff5f5;
}
</style>