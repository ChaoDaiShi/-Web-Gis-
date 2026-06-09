<template>
  <div class="appointment-manage-page">
    <AppTopBar />
    
    <div class="page-container">
      <div class="page-header">
        <h1>预约审核管理</h1>
        <div class="tabs">
          <button 
            :class="['tab-btn', { active: activeTab === 'pending' }]"
            @click="activeTab = 'pending'"
          >
            待审核 ({{ pendingCount }})
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
          <button 
            :class="['tab-btn', { active: activeTab === 'rejected' }]"
            @click="activeTab = 'rejected'"
          >
            已拒绝
          </button>
        </div>
      </div>
      
      <div class="appointments-container">
        <div v-if="loading" class="loading">加载中...</div>
        
        <div v-else-if="filteredAppointments.length === 0" class="empty">
          <p>暂无预约记录</p>
        </div>
        
        <div v-else class="appointments-table">
          <table>
            <thead>
              <tr>
                <th>预约ID</th>
                <th>物品信息</th>
                <th>预约人</th>
                <th>预约时间</th>
                <th>领取地点</th>
                <th>联系方式</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="appointment in filteredAppointments" :key="appointment.appointment_id">
                <td>{{ appointment.appointment_id }}</td>
                <td>
                  <div class="item-info">
                    <p class="item-title">{{ appointment.item_title }}</p>
                    <p class="item-desc">{{ appointment.item_description }}</p>
                  </div>
                </td>
                <td>
                  <div class="user-info">
                    <img v-if="appointment.avatar_url" :src="appointment.avatar_url" class="avatar" />
                    <span>{{ appointment.username }}</span>
                  </div>
                </td>
                <td>{{ formatTime(appointment.appointment_time) }}</td>
                <td>
                  <div class="location-info">
                    <p>{{ appointment.location }}</p>
                    <button class="btn-map" @click="viewOnMap(appointment)">查看地图</button>
                  </div>
                </td>
                <td>
                  <p>{{ appointment.contact_name }}</p>
                  <p class="phone">{{ appointment.contact_phone }}</p>
                </td>
                <td>
                  <span :class="['status-badge', `status-${appointment.status}`]">
                    {{ getStatusText(appointment.status) }}
                  </span>
                </td>
                <td>
                  <div class="action-btns">
                    <button 
                      v-if="appointment.status === 'pending'"
                      class="btn-approve"
                      @click="handleApprove(appointment)"
                    >
                      通过
                    </button>
                    <button 
                      v-if="appointment.status === 'pending'"
                      class="btn-reject"
                      @click="handleReject(appointment)"
                    >
                      拒绝
                    </button>
                    <button 
                      v-if="appointment.status === 'approved'"
                      class="btn-complete"
                      @click="handleComplete(appointment)"
                    >
                      完成领取
                    </button>
                    <button 
                      class="btn-detail"
                      @click="viewDetail(appointment)"
                    >
                      详情
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <div v-if="showMapModal" class="map-modal-overlay" @click.self="closeMapModal">
      <div class="map-modal">
        <div class="modal-header">
          <h2>领取地点</h2>
          <button class="close-btn" @click="closeMapModal">×</button>
        </div>
        <div class="modal-body">
          <div class="map-container" ref="mapContainer"></div>
          <p class="location-text">{{ currentMapLocation }}</p>
        </div>
      </div>
    </div>
    
    <div v-if="showRejectModal" class="reject-modal-overlay" @click.self="closeRejectModal">
      <div class="reject-modal">
        <div class="modal-header">
          <h2>拒绝预约</h2>
          <button class="close-btn" @click="closeRejectModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>拒绝原因 *</label>
            <textarea v-model="rejectReason" placeholder="请输入拒绝原因" rows="4"></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" @click="closeRejectModal">取消</button>
            <button class="btn-confirm" @click="confirmReject" :disabled="!rejectReason.trim()">
              确认拒绝
            </button>
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
            <p><strong>物品名称：</strong>{{ currentDetail.item?.title }}</p>
            <p><strong>物品描述：</strong>{{ currentDetail.item?.description || '暂无' }}</p>
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
            <h3>审核信息</h3>
            <p>
              <strong>状态：</strong>
              <span :class="['status-badge', `status-${currentDetail.status}`]">
                {{ getStatusText(currentDetail.status) }}
              </span>
            </p>
            <p v-if="currentDetail.review_time">
              <strong>审核时间：</strong>{{ formatTime(currentDetail.review_time) }}
            </p>
            <p v-if="currentDetail.review_note">
              <strong>审核备注：</strong>{{ currentDetail.review_note }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import AppTopBar from '../components/AppTopBar.vue';

const showToast = window.showToast;
const API_BASE = 'http://127.0.0.1:5000/api';

const appointments = ref([]);
const loading = ref(true);
const activeTab = ref('pending');
const showMapModal = ref(false);
const showRejectModal = ref(false);
const showDetailModal = ref(false);
const currentMapLocation = ref('');
const rejectReason = ref('');
const currentAppointment = ref(null);
const currentDetail = ref(null);
const mapContainer = ref(null);
let map = null;

const pendingCount = computed(() => {
  return appointments.value.filter(a => a.status === 'pending').length;
});

const filteredAppointments = computed(() => {
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
    const res = await fetch(`${API_BASE}/appointments/list?status=all`);
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

async function handleApprove(appointment) {
  if (!confirm('确定通过该预约申请吗？')) {
    return;
  }
  
  try {
    const adminId = localStorage.getItem('admin_id') || 1;
    const res = await fetch(`${API_BASE}/appointments/${appointment.appointment_id}/approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reviewer_id: adminId })
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast('审核通过', 'success');
      loadAppointments();
    } else {
      showToast(data.message || '操作失败', 'error');
    }
  } catch (error) {
    console.error('审核失败:', error);
    showToast('网络错误', 'error');
  }
}

function handleReject(appointment) {
  currentAppointment.value = appointment;
  rejectReason.value = '';
  showRejectModal.value = true;
}

async function confirmReject() {
  if (!rejectReason.value.trim()) {
    showToast('请输入拒绝原因', 'error');
    return;
  }
  
  try {
    const adminId = localStorage.getItem('admin_id') || 1;
    const res = await fetch(`${API_BASE}/appointments/${currentAppointment.value.appointment_id}/reject`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        reviewer_id: adminId,
        review_note: rejectReason.value.trim()
      })
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast('已拒绝', 'success');
      closeRejectModal();
      loadAppointments();
    } else {
      showToast(data.message || '操作失败', 'error');
    }
  } catch (error) {
    console.error('拒绝失败:', error);
    showToast('网络错误', 'error');
  }
}

async function handleComplete(appointment) {
  if (!confirm('确认物品已成功领取吗？')) {
    return;
  }
  
  try {
    const adminId = localStorage.getItem('admin_id') || 1;
    const res = await fetch(`${API_BASE}/appointments/${appointment.appointment_id}/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reviewer_id: adminId })
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast('领取完成', 'success');
      loadAppointments();
    } else {
      showToast(data.message || '操作失败', 'error');
    }
  } catch (error) {
    console.error('完成失败:', error);
    showToast('网络错误', 'error');
  }
}

function viewOnMap(appointment) {
  currentMapLocation.value = appointment.location;
  showMapModal.value = true;
  
  setTimeout(() => {
    if (!window.AMap || !mapContainer.value) return;
    
    if (map) {
      map.destroy();
    }
    
    map = new AMap.Map(mapContainer.value, {
      zoom: 17,
      center: [appointment.longitude, appointment.latitude],
      viewMode: '2D'
    });
    
    new AMap.Marker({
      position: [appointment.longitude, appointment.latitude],
      title: '领取地点'
    }).setMap(map);
  }, 100);
}

async function viewDetail(appointment) {
  try {
    const res = await fetch(`${API_BASE}/appointments/${appointment.appointment_id}`);
    const data = await res.json();
    
    if (data.success) {
      currentDetail.value = data.data;
      showDetailModal.value = true;
    } else {
      showToast(data.message || '获取详情失败', 'error');
    }
  } catch (error) {
    console.error('获取详情失败:', error);
    showToast('网络错误', 'error');
  }
}

function closeMapModal() {
  showMapModal.value = false;
  if (map) {
    map.destroy();
    map = null;
  }
}

function closeRejectModal() {
  showRejectModal.value = false;
  currentAppointment.value = null;
  rejectReason.value = '';
}

function closeDetailModal() {
  showDetailModal.value = false;
  currentDetail.value = null;
}

onMounted(() => {
  loadAppointments();
});

onBeforeUnmount(() => {
  if (map) {
    map.destroy();
  }
});
</script>

<style scoped>
.appointment-manage-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-container {
  max-width: 1400px;
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

.appointments-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  background: #f5f7fa;
  padding: 12px;
  text-align: left;
  font-weight: 500;
  color: #333;
  border-bottom: 2px solid #e8e8e8;
}

td {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
}

.item-info .item-title {
  font-weight: 500;
  margin: 0 0 4px 0;
}

.item-info .item-desc {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.location-info p {
  margin: 0 0 4px 0;
  font-size: 13px;
}

.btn-map {
  padding: 4px 8px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.phone {
  font-size: 12px;
  color: #999;
  margin: 4px 0 0 0;
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

.action-btns {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-approve,
.btn-reject,
.btn-complete,
.btn-detail {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-approve {
  background: #52c41a;
  color: white;
}

.btn-reject {
  background: #f5222d;
  color: white;
}

.btn-complete {
  background: #1890ff;
  color: white;
}

.btn-detail {
  background: #f5f5f5;
  color: #666;
}

.map-modal-overlay,
.reject-modal-overlay,
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

.map-modal,
.reject-modal,
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

.map-container {
  width: 100%;
  height: 400px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.location-text {
  margin-top: 12px;
  font-size: 14px;
  color: #666;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel,
.btn-confirm {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: none;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-confirm {
  background: #f5222d;
  color: white;
}

.btn-confirm:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
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
</style>
