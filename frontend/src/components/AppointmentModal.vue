<template>
  <div class="appointment-modal-overlay" @click.self="handleClose">
    <div class="appointment-modal">
      <div class="modal-header">
        <h2>我的预约</h2>
        <div class="header-actions">
          <button class="btn-return" @click="goToReturnAppointment">📅 预约归还</button>
          <button class="close-btn" @click="handleClose">×</button>
        </div>
      </div>
      
      <div class="modal-body">
        <div class="tabs">
          <button 
            :class="['tab-btn', { active: activeTab === 'all' }]"
            @click="activeTab = 'all'"
          >
            全部
          </button>
          <button 
            :class="['tab-btn', { active: activeTab === 'pending' }]"
            @click="activeTab = 'pending'"
          >
            待审核
          </button>
          <button 
            :class="['tab-btn', { active: activeTab === 'approved' }]"
            @click="activeTab = 'approved'"
          >
            已通过
          </button>
          <button 
            :class="['tab-btn', { active: activeTab === 'completed' }]"
            @click="activeTab = 'completed'"
          >
            已完成
          </button>
        </div>
        
        <div class="appointments-container">
          <div v-if="loading" class="loading">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>
          
          <div v-else-if="filteredAppointments.length === 0" class="empty">
            <div class="empty-icon">📅</div>
            <p>暂无预约记录</p>
          </div>
          
          <div v-else class="appointments-list">
            <div 
              v-for="appointment in filteredAppointments" 
              :key="appointment.appointment_id"
              class="appointment-card"
              @click="viewDetail(appointment)"
            >
              <div class="card-header">
                <h3>{{ appointment.item_title || '未知物品' }}</h3>
                <span :class="['status-badge', `status-${appointment.status}`]">
                  {{ getStatusText(appointment.status) }}
                </span>
              </div>
              
              <div class="card-body">
                <div class="info-row">
                  <span class="icon">🕐</span>
                  <span class="value">{{ formatTime(appointment.appointment_time) }}</span>
                </div>
                <div class="info-row">
                  <span class="icon">📍</span>
                  <span class="value">{{ appointment.location }}</span>
                </div>
                <div class="info-row">
                  <span class="icon">👤</span>
                  <span class="value">{{ appointment.contact_name }} {{ appointment.contact_phone }}</span>
                </div>
              </div>
              
              <div class="card-footer">
                <span class="create-time">{{ formatTime(appointment.create_time) }}</span>
                <div class="actions">
                  <button 
                    v-if="appointment.status === 'pending' || appointment.status === 'approved'"
                    class="btn-cancel"
                    @click.stop="handleCancel(appointment)"
                  >
                    取消
                  </button>
                  <button 
                    v-if="appointment.status === 'approved'"
                    class="btn-navigate"
                    @click.stop="navigateToLocation(appointment)"
                  >
                    导航
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="showDetailModal" class="detail-modal-overlay" @click.self="closeDetailModal">
        <div class="detail-modal">
          <div class="detail-header">
            <h3>预约详情</h3>
            <button class="close-btn" @click="closeDetailModal">×</button>
          </div>
          <div class="detail-body" v-if="currentDetail">
            <div class="detail-section">
              <h4>物品信息</h4>
              <p><strong>物品名称：</strong>{{ currentDetail.item_title }}</p>
              <p><strong>物品描述：</strong>{{ currentDetail.item_description || '暂无描述' }}</p>
            </div>
            
            <div class="detail-section">
              <h4>预约信息</h4>
              <p><strong>预约时间：</strong>{{ formatTime(currentDetail.appointment_time) }}</p>
              <p><strong>领取地点：</strong>{{ currentDetail.location }}</p>
              <p><strong>联系人：</strong>{{ currentDetail.contact_name }}</p>
              <p><strong>联系电话：</strong>{{ currentDetail.contact_phone }}</p>
              <p v-if="currentDetail.note"><strong>备注：</strong>{{ currentDetail.note }}</p>
            </div>
            
            <div class="detail-section">
              <h4>状态信息</h4>
              <p>
                <strong>当前状态：</strong>
                <span :class="['status-badge', `status-${currentDetail.status}`]">
                  {{ getStatusText(currentDetail.status) }}
                </span>
              </p>
              <p v-if="currentDetail.review_note">
                <strong>审核备注：</strong>{{ currentDetail.review_note }}
              </p>
            </div>
            
            <div class="map-container" ref="detailMapContainer"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter } from 'vue-router';

const emit = defineEmits(['close']);
const showToast = window.showToast;
const API_BASE = 'http://127.0.0.1:5000/api';
const router = useRouter();

const appointments = ref([]);
const loading = ref(true);
const activeTab = ref('all');
const showDetailModal = ref(false);
const currentDetail = ref(null);
const detailMapContainer = ref(null);
let detailMap = null;

const filteredAppointments = computed(() => {
  if (activeTab.value === 'all') {
    return appointments.value;
  }
  return appointments.value.filter(a => a.status === activeTab.value);
});

function getStatusText(status) {
  const statusMap = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
    completed: '已完成',
    cancelled: '已取消'
  };
  return statusMap[status] || status;
}

function formatTime(timeStr) {
  if (!timeStr) return '未知时间';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN');
}

async function loadAppointments() {
  loading.value = true;
  try {
    const userId = localStorage.getItem('user_id');
    const res = await fetch(`${API_BASE}/appointments/my?user_id=${userId}`);
    const data = await res.json();
    
    if (data.success) {
      appointments.value = data.data || [];
    } else {
      showToast(data.message || '加载失败', 'error');
    }
  } catch (error) {
    console.error('加载预约列表失败:', error);
    showToast('网络错误', 'error');
  } finally {
    loading.value = false;
  }
}

async function handleCancel(appointment) {
  if (!confirm('确定要取消这个预约吗？')) {
    return;
  }
  
  try {
    const userId = localStorage.getItem('user_id');
    const res = await fetch(`${API_BASE}/appointments/${appointment.appointment_id}/cancel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: userId })
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast('预约已取消', 'success');
      loadAppointments();
    } else {
      showToast(data.message || '取消失败', 'error');
    }
  } catch (error) {
    console.error('取消预约失败:', error);
    showToast('网络错误', 'error');
  }
}

function navigateToLocation(appointment) {
  if (!appointment.longitude || !appointment.latitude) {
    showToast('位置信息不完整', 'error');
    return;
  }
  
  const url = `https://uri.amap.com/navigation?to=${appointment.longitude},${appointment.latitude},${encodeURIComponent(appointment.location)}&mode=car&policy=1&src=myapp&coordinate=gaode`;
  window.open(url, '_blank');
}

function viewDetail(appointment) {
  currentDetail.value = appointment;
  showDetailModal.value = true;
  
  setTimeout(() => {
    initDetailMap();
  }, 100);
}

function initDetailMap() {
  if (!window.AMap || !detailMapContainer.value || !currentDetail.value) {
    return;
  }
  
  if (detailMap) {
    detailMap.destroy();
  }
  
  detailMap = new AMap.Map(detailMapContainer.value, {
    zoom: 17,
    center: [currentDetail.value.longitude, currentDetail.value.latitude],
    viewMode: '2D'
  });
  
  new AMap.Marker({
    position: [currentDetail.value.longitude, currentDetail.value.latitude],
    title: '领取地点'
  }).setMap(detailMap);
}

function closeDetailModal() {
  showDetailModal.value = false;
  currentDetail.value = null;
  if (detailMap) {
    detailMap.destroy();
    detailMap = null;
  }
}

function handleClose() {
  emit('close');
}

function goToReturnAppointment() {
  emit('close');
  router.push('/return-appointment');
}

onMounted(() => {
  loadAppointments();
});

onBeforeUnmount(() => {
  if (detailMap) {
    detailMap.destroy();
  }
});
</script>

<style scoped>
.appointment-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.appointment-modal {
  background: white;
  border-radius: 16px;
  width: 95%;
  max-width: 600px;
  max-height: 85vh;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: white;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-return {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-return:hover {
  background: rgba(255, 255, 255, 0.3);
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  font-size: 24px;
  color: white;
  cursor: pointer;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.modal-body {
  padding: 20px;
  max-height: calc(85vh - 70px);
  overflow-y: auto;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid #e8e8e8;
  background: white;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
  color: #666;
}

.tab-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: white;
}

.appointments-container {
  min-height: 200px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #999;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.appointments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.appointment-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.appointment-card:hover {
  background: white;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header h3 {
  margin: 0;
  font-size: 15px;
  color: #333;
  font-weight: 600;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status-pending {
  background: #fff7e6;
  color: #fa8c16;
}

.status-approved {
  background: #e6f7ff;
  color: #1890ff;
}

.status-rejected {
  background: #fff1f0;
  color: #f5222d;
}

.status-completed {
  background: #f6ffed;
  color: #52c41a;
}

.status-cancelled {
  background: #f5f5f5;
  color: #999;
}

.card-body {
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  margin: 6px 0;
  font-size: 13px;
}

.info-row .icon {
  margin-right: 8px;
  font-size: 14px;
}

.info-row .value {
  color: #666;
  flex: 1;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #e8e8e8;
}

.create-time {
  font-size: 11px;
  color: #999;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn-cancel,
.btn-navigate {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-cancel:hover {
  background: #e8e8e8;
}

.btn-navigate {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-navigate:hover {
  opacity: 0.9;
}

.detail-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100;
}

.detail-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
}

.detail-header h3 {
  margin: 0;
  font-size: 16px;
}

.detail-body {
  padding: 20px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.detail-section p {
  margin: 6px 0;
  font-size: 13px;
  color: #666;
}

.map-container {
  width: 100%;
  height: 200px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}
</style>