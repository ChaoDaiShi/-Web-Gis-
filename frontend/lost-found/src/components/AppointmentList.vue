<template>
  <div class="appointment-list-page" :style="pageStyle">
    <AppTopBar />
    
    <div class="page-container">
      <div class="page-header">
        <h1>我的预约</h1>
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
      </div>
      
      <div class="appointments-container">
        <div v-if="loading" class="loading">
          加载中...
        </div>
        
        <div v-else-if="filteredAppointments.length === 0" class="empty">
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
                <span class="label">预约时间：</span>
                <span class="value">{{ formatTime(appointment.appointment_time) }}</span>
              </div>
              <div class="info-row">
                <span class="label">领取地点：</span>
                <span class="value">{{ appointment.location }}</span>
              </div>
              <div class="info-row">
                <span class="label">联系人：</span>
                <span class="value">{{ appointment.contact_name }}</span>
              </div>
              <div class="info-row">
                <span class="label">联系电话：</span>
                <span class="value">{{ appointment.contact_phone }}</span>
              </div>
            </div>
            
            <div class="card-footer">
              <span class="create-time">提交时间：{{ formatTime(appointment.create_time) }}</span>
              <div class="actions">
                <button 
                  v-if="appointment.status === 'pending' || appointment.status === 'approved'"
                  class="btn-cancel"
                  @click.stop="handleCancel(appointment)"
                >
                  取消预约
                </button>
                <button 
                  v-if="appointment.status === 'approved'"
                  class="btn-navigate"
                  @click.stop="navigateToLocation(appointment)"
                >
                  导航前往
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showDetailModal" class="detail-modal-overlay" @click.self="closeDetailModal">
      <div class="detail-modal">
        <div class="modal-header">
          <h2>预约详情</h2>
          <button class="close-btn" @click="closeDetailModal">×</button>
        </div>
        <div class="modal-body" v-if="currentDetail">
          <div class="detail-section">
            <h3>物品信息</h3>
            <p><strong>物品名称：</strong>{{ currentDetail.item_title }}</p>
            <p><strong>物品描述：</strong>{{ currentDetail.item_description || '暂无描述' }}</p>
          </div>
          
          <div class="detail-section">
            <h3>预约信息</h3>
            <p><strong>预约时间：</strong>{{ formatTime(currentDetail.appointment_time) }}</p>
            <p><strong>领取地点：</strong>{{ currentDetail.location }}</p>
            <p><strong>联系人：</strong>{{ currentDetail.contact_name }}</p>
            <p><strong>联系电话：</strong>{{ currentDetail.contact_phone }}</p>
            <p v-if="currentDetail.note"><strong>备注：</strong>{{ currentDetail.note }}</p>
          </div>
          
          <div class="detail-section">
            <h3>状态信息</h3>
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
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import AppTopBar from '../components/AppTopBar.vue';

const router = useRouter();
const showToast = window.showToast;
const API_BASE = 'http://127.0.0.1:5000/api';

const appointments = ref([]);
const loading = ref(true);
const activeTab = ref('all');
const showDetailModal = ref(false);
const currentDetail = ref(null);
const detailMapContainer = ref(null);
let detailMap = null;

const bgImage = ref('');
const pageStyle = computed(() => {
  if (bgImage.value) {
    return {
      background: `url(${bgImage.value}) center/cover`,
      minHeight: '100vh'
    };
  }
  return {};
});

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

onMounted(() => {
  loadAppointments();
  
  const bg = localStorage.getItem('bg_image');
  if (bg) {
    bgImage.value = bg;
  }
});

onBeforeUnmount(() => {
  if (detailMap) {
    detailMap.destroy();
  }
});
</script>

<style scoped>
.appointment-list-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.page-header h1 {
  margin: 0 0 20px 0;
  font-size: 24px;
  color: #333;
}

.tabs {
  display: flex;
  gap: 12px;
}

.tab-btn {
  padding: 8px 20px;
  border: 1px solid #d9d9d9;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.tab-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.tab-btn.active {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

.appointments-container {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.loading,
.empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

.appointments-list {
  display: grid;
  gap: 16px;
}

.appointment-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.appointment-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
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
  margin: 8px 0;
  font-size: 14px;
}

.info-row .label {
  color: #999;
  min-width: 80px;
}

.info-row .value {
  color: #333;
  flex: 1;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.create-time {
  font-size: 12px;
  color: #999;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn-cancel,
.btn-navigate {
  padding: 6px 16px;
  border-radius: 4px;
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
  background: #1890ff;
  color: white;
}

.btn-navigate:hover {
  background: #40a9ff;
}

.detail-modal-overlay {
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
}

.detail-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
}

.modal-body {
  padding: 24px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.detail-section p {
  margin: 8px 0;
  font-size: 14px;
  color: #666;
}

.map-container {
  width: 100%;
  height: 300px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}
</style>
