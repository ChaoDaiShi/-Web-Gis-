<!-- 报修详情弹窗 -->
<script setup>
import { ref, computed, onMounted } from "vue";

const props = defineProps({
  visible: Boolean,
  repair: Object,
  currentUserId: [String, Number],
  currentUserRole: String
});

const emit = defineEmits(["close", "updated"]);

const API_BASE = "http://127.0.0.1:5000/api";
const isMaintainer = computed(() => props.currentUserRole === 'maintainer');
const acting = ref(false);

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

const currentStatus = computed(() => {
  if (!props.repair) return { text: '未知', class: '' };
  return statusMap[props.repair.status] || { text: '未知', class: '' };
});

const currentPriority = computed(() => {
  if (!props.repair) return { text: '未知', class: '' };
  return priorityMap[props.repair.priority] || { text: '未知', class: '' };
});

const canStart = computed(() => {
  return isMaintainer.value && props.repair && Number(props.repair.status) === 0;
});

const canComplete = computed(() => {
  return isMaintainer.value && props.repair && Number(props.repair.status) === 1;
});

function showToast(msg, type = 'info') {
  if (window.showToast) {
    window.showToast(msg, type);
  } else {
    console.log(`[toast ${type}]`, msg);
  }
}

async function handleStart() {
  if (!props.repair) return;
  if (!props.currentUserId) {
    showToast('请先登录', 'warning');
    return;
  }
  if (!confirm(`确认开始维修「${props.repair.title}」吗？`)) return;
  acting.value = true;
  try {
    const res = await fetch(`${API_BASE}/repair/${props.repair.repair_id}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: props.currentUserId })
    });
    const data = await res.json();
    if (data.success) {
      showToast('已开始维修', 'success');
      if (props.repair) {
        props.repair.status = 1;
      }
      emit('updated', { action: 'start', repair: props.repair });
    } else {
      showToast(data.message || '操作失败', 'error');
    }
  } catch (e) {
    showToast('操作失败: ' + e.message, 'error');
  } finally {
    acting.value = false;
  }
}

async function handleComplete() {
  if (!props.repair) return;
  if (!props.currentUserId) {
    showToast('请先登录', 'warning');
    return;
  }
  if (!confirm(`确认完成「${props.repair.title}」的维修吗？完成将从地图上移除该标记。`)) return;
  acting.value = true;
  try {
    const res = await fetch(`${API_BASE}/repair/${props.repair.repair_id}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: props.currentUserId,
        process_note: ''
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast('维修已完成，已从地图上移除', 'success');
      emit('updated', { action: 'complete', repair: props.repair });
      emit('close');
    } else {
      showToast(data.message || '操作失败', 'error');
    }
  } catch (e) {
    showToast('操作失败: ' + e.message, 'error');
  } finally {
    acting.value = false;
  }
}

function handleClose() {
  emit('close');
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content repair-detail-modal">
        <div class="modal-header">
          <h2>🔧 报修详情</h2>
          <button class="close-btn" @click="handleClose">×</button>
        </div>

        <div v-if="repair" class="modal-body">
          <div class="detail-row">
            <span class="detail-label">物品名称</span>
            <span class="detail-value title">{{ repair.title }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">状态</span>
            <span :class="['detail-value status-badge', currentStatus.class]">
              {{ currentStatus.text }}
            </span>
          </div>

          <div class="detail-row">
            <span class="detail-label">优先级</span>
            <span :class="['detail-value priority-badge', currentPriority.class]">
              {{ currentPriority.text }}优先级
            </span>
          </div>

          <div class="detail-row">
            <span class="detail-label">分类</span>
            <span class="detail-value">{{ repair.category_name || '未分类' }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">描述</span>
            <span class="detail-value">{{ repair.description || '无' }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">坐标</span>
            <span class="detail-value">📍 {{ repair.lng?.toFixed(6) }}, {{ repair.lat?.toFixed(6) }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">位置名称</span>
            <span class="detail-value">{{ repair.location_name || '无' }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">位置详情</span>
            <span class="detail-value">{{ repair.location_detail || '无' }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">报修人ID</span>
            <span class="detail-value">{{ repair.reporter_id }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">创建时间</span>
            <span class="detail-value">{{ repair.create_time || '未知' }}</span>
          </div>

          <div v-if="repair.images && repair.images.length > 0" class="detail-images">
            <span class="detail-label">图片</span>
            <div class="images-container">
              <img
                v-for="(img, index) in repair.images"
                :key="index"
                :src="typeof img === 'string' ? (img.startsWith('http') ? img : `http://127.0.0.1:5000${img}`) : ''"
                class="detail-image"
                :alt="`图片${index + 1}`"
              />
            </div>
          </div>

          <div v-if="isMaintainer" class="maintainer-actions">
            <div class="role-hint">🔧 维修工操作区</div>
            <div class="action-buttons">
              <button
                v-if="canStart"
                class="btn btn-primary"
                :disabled="acting"
                @click="handleStart"
              >
                🛠️ 开始维修
              </button>
              <button
                v-if="canComplete"
                class="btn btn-success"
                :disabled="acting"
                @click="handleComplete"
              >
                ✅ 完成维修
              </button>
              <div v-if="!canStart && !canComplete" class="action-tip">
                当前状态下无可执行操作
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="handleClose">关闭</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.repair-detail-modal {
  background: #fff;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  color: #fff;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #fff;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  max-height: 60vh;
}

.detail-row {
  display: flex;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-weight: 500;
  color: #666;
  min-width: 100px;
  font-size: 14px;
}

.detail-value {
  flex: 1;
  color: #333;
  font-size: 14px;
}

.detail-value.title {
  font-weight: 600;
  font-size: 16px;
  color: #dc3545;
}

.status-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  display: inline-block;
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

.priority-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  display: inline-block;
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

.detail-images {
  flex-direction: column;
  align-items: flex-start;
}

.images-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}

.detail-image {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.maintainer-actions {
  margin-top: 16px;
  padding: 14px;
  background: linear-gradient(135deg, #fff7ed 0%, #fef3c7 100%);
  border: 1px dashed #f59e0b;
  border-radius: 8px;
}

.role-hint {
  font-size: 13px;
  font-weight: 600;
  color: #92400e;
  margin-bottom: 10px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-tip {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  padding: 6px 0;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: #fff;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  font-weight: 600;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.btn-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
  font-weight: 600;
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}
</style>
