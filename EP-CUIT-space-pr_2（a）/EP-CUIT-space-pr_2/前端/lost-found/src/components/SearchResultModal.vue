<script setup>defineProps({
 show: Boolean,
 results: {
 type: Array,
 default: () => []
 },
 keyword: {
 type: String,
 default: ''
 }
});
const emit = defineEmits(['close', 'select']);
function handleClose() {
 emit('close');
}
function handleSelect(item) {
 emit('select', item);
}
function getStatusText(status) {
 return status === 0 ? '丢失' : '拾到';
}
function getStatusClass(status) {
 return status === 0 ? 'status-lost' : 'status-found';
}
function hasCoordinates(item) {
 return item.lng && item.lat && !isNaN(item.lng) && !isNaN(item.lat);
}
</script>

<template>
  <div class="search-result-modal-mask" :style="{ display: show ? 'flex' : 'none' }">
    <div class="search-result-modal">
      <div class="modal-header">
        <h3>搜索结果</h3>
        <span class="result-count">找到 {{ results.length }} 个匹配结果</span>
        <button class="close-btn" @click="handleClose">×</button>
      </div>
      
      <div class="modal-body">
        <div v-if="results.length === 0" class="empty-state">
          <p>未找到匹配结果</p>
          <p class="hint">请尝试其他关键词</p>
        </div>
        
        <div v-else class="results-list">
          <div
            v-for="item in results"
            :key="item.id"
            class="result-item"
            :class="{ 'has-coords': hasCoordinates(item) }"
            @click="handleSelect(item)"
          >
            <div class="item-header">
              <span class="status-tag" :class="getStatusClass(item.status)">
                {{ getStatusText(item.status) }}
              </span>
              <span class="similarity">相似度: {{ Math.round(item.similarity * 100) }}%</span>
            </div>
            <h4 class="item-title">{{ item.title }}</h4>
            <p class="item-detail">{{ item.detail || '无描述' }}</p>
            <div class="item-info">
              <span>ID: {{ item.id }}</span>
              <span v-if="hasCoordinates(item)" class="has-location">📍 有位置</span>
              <span v-else class="no-location">🔍 无位置</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn" @click="handleClose">关闭</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-result-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.search-result-modal {
  width: min(600px, 90vw);
  max-height: 70vh;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.result-count {
  font-size: 14px;
  color: #6b7280;
}

.close-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: #f3f4f6;
  color: #374151;
  font-size: 20px;
  cursor: pointer;
  line-height: 1;
}

.close-btn:hover {
  background: #e5e7eb;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.empty-state .hint {
  margin-top: 8px;
  font-size: 14px;
  color: #9ca3af;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  background: #fff;
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.result-item.has-coords {
  border-left: 3px solid #3b82f6;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.status-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 500;
}

.status-lost {
  background: #fee2e2;
  color: #dc2626;
}

.status-found {
  background: #dbeafe;
  color: #2563eb;
}

.similarity {
  font-size: 12px;
  color: #6b7280;
  margin-left: auto;
}

.item-title {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.item-detail {
  margin: 0 0 8px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #9ca3af;
}

.has-location {
  color: #22c55e;
}

.no-location {
  color: #9ca3af;
}

.modal-footer {
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.btn {
  padding: 8px 16px;
  border: 1px solid #9ca3af;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}

.btn:hover {
  background: #f3f4f6;
}
</style>
