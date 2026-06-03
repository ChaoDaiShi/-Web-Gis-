<!-- 标记详情弹窗 -->
<script setup>
import { ref, watch } from 'vue';
import ClaimForm from './ClaimForm.vue';
import ReturnForm from './ReturnForm.vue';

const showToast = window.showToast;
const showConfirm = window.showConfirm;

const props = defineProps({
  show: Boolean,
  marker: {
    type: Object,
    default: null
  },
  showActionButtons: {
    type: Boolean,
    default: true
  },
  showPublisherInfo: {
    type: Boolean,
    default: true
  },
  showLocateButton: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['close', 'remove']);

const showClaimForm = ref(false);
const showReturnForm = ref(false);

const API_BASE = 'http://127.0.0.1:5000/api';

const publisherInfo = ref(null);
const loadingPublisher = ref(false);

function hasCoordinates(item) {
  return item && item.lng && item.lat && !isNaN(item.lng) && !isNaN(item.lat);
}

function getImages(marker) {
  if (!marker) return [];
  
  let images = [];
  
  if (marker.images && Array.isArray(marker.images)) {
    images = marker.images;
  } else if (marker.image_urls) {
    if (Array.isArray(marker.image_urls)) {
      images = marker.image_urls;
    } else if (typeof marker.image_urls === 'string') {
      try {
        const parsed = JSON.parse(marker.image_urls);
        images = Array.isArray(parsed) ? parsed : [];
      } catch {
        images = [];
      }
    }
  }
  
  return images.map(img => {
    if (typeof img === 'string') {
      if (img.startsWith('http://') || img.startsWith('https://')) {
        return img;
      }
      if (img.startsWith('/')) {
        return `http://127.0.0.1:5000${img}`;
      }
      return `http://127.0.0.1:5000/${img}`;
    }
    return '';
  }).filter(img => img);
}

function getStatusText(type) {
  return type === 0 ? '丢失物品' : '拾到物品';
}

function getStatusClass(type) {
  return type === 0 ? 'text-lost' : 'text-found';
}

function isApproved() {
  return props.marker?.audit_status === 'approved';
}

function isPendingAudit() {
  return props.marker?.audit_status === 'pending';
}

function formatAuditStatus(status) {
  if (status === 'approved') return '已通过';
  if (status === 'pending') return '待审核';
  if (status === 'rejected') return '已拒绝';
  return status || '未知';
}

async function loadPublisherInfo(userId) {
  if (!userId) {
    publisherInfo.value = null;
    return;
  }
  
  loadingPublisher.value = true;
  try {
    const res = await fetch(`${API_BASE}/profile?user_id=${userId}`);
    const data = await res.json();
    if (data.success && data.data) {
      publisherInfo.value = {
        username: data.data.username || '未知用户',
        avatar: data.data.avatar ? `http://127.0.0.1:5000${data.data.avatar}` : null,
        phone: data.data.phone || '',
        email: data.data.email || ''
      };
    } else {
      publisherInfo.value = null;
    }
  } catch (e) {
    console.error('加载发布者信息失败:', e);
    publisherInfo.value = null;
  } finally {
    loadingPublisher.value = false;
  }
}

watch(() => props.show, (newVal) => {
  if (newVal && props.marker) {
    loadPublisherInfo(props.marker.publisher_id);
  } else {
    publisherInfo.value = null;
  }
});

watch(() => props.marker, (newVal) => {
  if (newVal && props.show) {
    loadPublisherInfo(newVal.publisher_id);
  }
});

function handleClose() {
  emit('close');
}

function canClaim() {
  if (!isApproved()) return false;
  const currentUserId = localStorage.getItem("user_id");
  if (!currentUserId) return false;
  
  const itemType = props.marker?.type;
  const publisherId = props.marker?.publisher_id;
  
  return itemType === 1 && String(publisherId) !== String(currentUserId);
}

function handleClaim() {
  if (!canClaim()) {
    showToast('只能申请认领其他用户拾到的物品', "warning");
    return;
  }
  
  showClaimForm.value = true;
}

function canReturn() {
  if (!isApproved()) return false;
  const currentUserId = localStorage.getItem("user_id");
  if (!currentUserId) return false;
  
  const itemType = props.marker?.type;
  const publisherId = props.marker?.publisher_id;
  
  return itemType === 0 && String(publisherId) !== String(currentUserId);
}

function handleReturn() {
  if (!canReturn()) {
    showToast('只能申请归还其他用户丢失的物品', "warning");
    return;
  }
  
  showReturnForm.value = true;
}

function canDelete() {
  const currentUserId = localStorage.getItem("user_id");
  if (!currentUserId) return false;
  
  const publisherId = props.marker?.publisher_id;
  
  return String(publisherId) === String(currentUserId);
}

async function handleDelete() {
  if (!canDelete()) {
    showToast('只能删除自己发布的物品', "warning");
    return;
  }
  
  if (!props.marker || !props.marker.id) return;
  
  const confirmed = await window.showConfirm({title: '确认移除', message: '确定要从列表中移除这个物品吗？', type: 'danger', confirmText: '确认移除'});
  if (!confirmed) {
    return;
  }
  
  emit('remove', props.marker.id);
  handleClose();
}

function handleClaimFormCancel() {
  showClaimForm.value = false;
}

function handleClaimFormSuccess() {
  showClaimForm.value = false;
  showToast('认领申请提交成功，请等待审核', "success");
  handleClose();
}

function handleReturnFormCancel() {
  showReturnForm.value = false;
}

function handleReturnFormSuccess() {
  showReturnForm.value = false;
  showToast('归还申请提交成功，请等待审核', "success");
  handleClose();
}

function getInitial() {
  return publisherInfo.value?.username ? publisherInfo.value.username.charAt(0).toUpperCase() : '?';
}
</script>

<template>
  <div class="marker-detail-modal-mask" :style="{ display: show ? 'flex' : 'none' }">
    <div class="marker-detail-modal">
      <div class="modal-header">
        <h3>{{ marker?.title || '详情' }}</h3>
        <button class="close-btn" @click="handleClose">×</button>
      </div>
      
      <div class="modal-body">
        <div v-if="isPendingAudit()" class="audit-notice">
          该物品正在审核中，仅您可见；审核通过后其他用户才能看到并认领/归还。
        </div>

        <div v-if="getImages(marker).length" class="detail-images">
          <img 
            v-for="(img, index) in getImages(marker)" 
            :key="index" 
            :src="img" 
            :alt="`图片${index + 1}`" 
          />
        </div>
        
        <div class="info-section">
          <div class="info-row">
            <span class="info-label">状态：</span>
            <span :class="getStatusClass(marker?.type)">
              {{ getStatusText(marker?.type) }}
            </span>
            <span v-if="marker?.audit_status" class="audit-tag" :class="marker.audit_status">
              {{ formatAuditStatus(marker.audit_status) }}
            </span>
          </div>
          
          <div class="info-row">
            <span class="info-label">描述：</span>
            <span>{{ marker?.detail || '无' }}</span>
          </div>
          
          <div class="info-row">
            <span class="info-label">发布时间：</span>
            <span>{{ marker?.time || '未知' }}</span>
          </div>
          
          <div v-if="marker?.phone" class="info-row">
            <span class="info-label">联系方式：</span>
            <span>{{ marker.phone }}</span>
          </div>
        </div>
        
        <div v-if="hasCoordinates(marker)" class="location-section">
          <div class="section-title">位置信息</div>
          <div class="location-content">
            <div class="location-coords">
              <span class="coord-label">经度：</span>
              <span>{{ marker.lng }}</span>
              <span class="coord-label" style="margin-left: 16px;">纬度：</span>
              <span>{{ marker.lat }}</span>
            </div>
            <button 
              v-if="showLocateButton"
              class="btn location-btn" 
              @click="() => { $emit('locate', marker); handleClose(); }"
            >
              📍 定位到地图
            </button>
          </div>
        </div>
        <div v-else class="no-location">
          <span>🔍 暂无位置信息</span>
        </div>
        
        <div v-if="showPublisherInfo" class="publisher-section">
          <div class="section-title">发布者信息</div>
          <div v-if="loadingPublisher" class="loading-publisher">
            加载中...
          </div>
          <div v-else-if="publisherInfo" class="publisher-info">
            <div class="publisher-avatar">
              <img v-if="publisherInfo.avatar" :src="publisherInfo.avatar" alt="头像" />
              <span v-else>{{ getInitial() }}</span>
            </div>
            <div class="publisher-details">
              <div class="publisher-name">{{ publisherInfo.username }}</div>
              <div v-if="publisherInfo.phone" class="publisher-contact">
                📞 {{ publisherInfo.phone }}
              </div>
              <div v-if="publisherInfo.email" class="publisher-contact">
                ✉️ {{ publisherInfo.email }}
              </div>
            </div>
          </div>
          <div v-else class="no-publisher">
            暂无发布者信息
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <template v-if="showActionButtons">
          <button 
            v-if="canClaim()" 
            class="btn claim" 
            @click="handleClaim"
          >申请认领</button>
          <button 
            v-else-if="canReturn()" 
            class="btn claim" 
            @click="handleReturn"
          >归还物品</button>
          <button 
            v-else 
            class="btn claim disabled" 
            disabled
          >申请认领</button>
        </template>
        <button v-if="canDelete()" class="btn delete" @click="handleDelete">删除</button>
        <button class="btn primary" @click="handleClose">关闭</button>
      </div>
    </div>
  </div>
  
  <ClaimForm 
    :show="showClaimForm"
    :item="marker"
    @cancel="handleClaimFormCancel"
    @success="handleClaimFormSuccess"
  />
  
  <ReturnForm 
    :show="showReturnForm"
    :item="marker"
    @close="handleReturnFormCancel"
    @success="handleReturnFormSuccess"
  />
</template>

<style scoped>
.marker-detail-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.marker-detail-modal {
  width: min(500px, 90vw);
  max-height: 80vh;
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
  justify-content: space-between;
  position: relative;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  position: absolute;
  right: 12px;
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
  padding: 16px 20px;
}

.detail-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  max-height: 200px;
  overflow-y: auto;
}

.detail-images img {
  max-width: 140px;
  max-height: 140px;
  object-fit: cover;
  border-radius: 8px;
}

.info-section {
  margin-top: 12px;
}

.audit-notice {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.audit-tag {
  margin-left: 8px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
}

.audit-tag.pending {
  background: #fef3c7;
  color: #92400e;
}

.audit-tag.approved {
  background: #dcfce7;
  color: #166534;
}

.audit-tag.rejected {
  background: #fee2e2;
  color: #991b1b;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  line-height: 1.7;
  font-size: 14px;
  margin-bottom: 6px;
}

.info-label {
  color: #6b7280;
  min-width: 70px;
}

.text-lost {
  color: #dc2626;
  font-weight: 600;
}

.text-found {
  color: #2563eb;
  font-weight: 600;
}

.location-section {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 8px;
}

.location-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.location-coords {
  font-size: 13px;
  color: #374151;
}

.coord-label {
  color: #6b7280;
}

.location-btn {
  padding: 6px 12px;
  font-size: 13px;
  background: #0ea5e9;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.location-btn:hover {
  background: #0284c7;
}

.no-location {
  text-align: center;
  padding: 16px;
  color: #9ca3af;
  font-size: 14px;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 16px;
}

.publisher-section {
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
}

.loading-publisher {
  text-align: center;
  padding: 12px;
  color: #6b7280;
  font-size: 14px;
}

.publisher-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.publisher-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #111827;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  overflow: hidden;
  flex-shrink: 0;
}

.publisher-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.publisher-details {
  flex: 1;
  min-width: 0;
}

.publisher-name {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
  margin-bottom: 4px;
}

.publisher-contact {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-publisher {
  text-align: center;
  padding: 12px;
  color: #9ca3af;
  font-size: 14px;
}

.modal-footer {
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border: 1px solid #9ca3af;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}

.btn.claim {
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: #fff;
  border-color: #33ccff;
}

.btn.claim:hover {
  background: linear-gradient(135deg, #0099cc 0%, #006699 100%);
}

.btn.claim.disabled {
  background: #d1d5db;
  border-color: #d1d5db;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn.delete {
  background: #dc2626;
  color: #fff;
  border-color: #dc2626;
}

.btn.delete:hover {
  background: #b91c1c;
}

.btn.primary {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.btn.primary:hover {
  background: #1d4ed8;
}
</style>
