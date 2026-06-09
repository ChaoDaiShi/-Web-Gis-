<template>
  <div class="return-appointment-page" :style="pageStyle">
    <AppTopBar />
    
    <div class="page-container">
      <div class="page-header">
        <h1>预约归还</h1>
        <p class="subtitle">您拾到的物品已被认领，可以预约归还给失主</p>
      </div>
      
      <div class="content-wrapper">
        <div v-if="loading" class="loading">
          加载中...
        </div>
        
        <div v-else-if="owners.length === 0" class="empty">
          <p>暂无可预约归还的物品</p>
          <p class="hint">当您拾到的物品被认领通过后，可以在此预约归还</p>
        </div>
        
        <div v-else class="owners-list">
          <div 
            v-for="item in owners" 
            :key="item.item_id"
            class="owner-card"
          >
            <div class="card-header">
              <div class="item-info">
                <h3>{{ item.item_title }}</h3>
                <p class="item-desc">{{ item.item_description || '暂无描述' }}</p>
              </div>
              <span :class="['status-badge', item.has_pending_appointment ? 'pending' : 'available']">
                {{ item.has_pending_appointment ? '已预约' : '可预约' }}
              </span>
            </div>
            
            <div class="card-body">
              <div class="owner-info">
                <div class="owner-avatar" @click="goToUserProfile(item.owner_id)">
                  <img v-if="item.owner_avatar" :src="getAvatarUrl(item.owner_avatar)" alt="头像" />
                  <span v-else>{{ item.owner_name?.charAt(0) || '?' }}</span>
                </div>
                <div class="owner-details">
                  <p class="owner-name" @click="goToUserProfile(item.owner_id)">
                    {{ item.owner_name }}
                  </p>
                  <p class="owner-label">失主</p>
                  <p class="claim-time">认领时间：{{ formatTime(item.claim_time) }}</p>
                </div>
              </div>
              
              <div class="actions">
                <button 
                  v-if="!item.has_pending_appointment"
                  class="btn-appointment"
                  @click="openAppointmentForm(item)"
                >
                  📅 预定归还日期
                </button>
                <button 
                  v-else
                  class="btn-view"
                  @click="viewAppointment(item)"
                >
                  查看预约
                </button>
                <button 
                  class="btn-chat"
                  @click="startChat(item.owner_id)"
                >
                  💬 发消息
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 预约申请表弹窗 -->
    <div v-if="showAppointmentForm" class="appointment-modal-overlay" @click.self="closeAppointmentForm">
      <div class="appointment-modal">
        <div class="modal-header">
          <h2>预约归还申请</h2>
          <button class="close-btn" @click="closeAppointmentForm">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-section">
            <h3>物品信息</h3>
            <p><strong>物品名称：</strong>{{ currentItem?.item_title }}</p>
            <p><strong>归还给：</strong>{{ currentItem?.owner_name }}</p>
          </div>
          
          <div class="form-section">
            <h3>选择归还时间</h3>
            <div class="time-picker">
              <div class="form-group">
                <label>归还日期 *</label>
                <input 
                  type="date" 
                  v-model="appointmentDate"
                  :min="minDate"
                  class="date-input"
                />
              </div>
              <div class="form-group">
                <label>归还时间 *</label>
                <div class="time-selects">
                  <select v-model="appointmentHour" class="time-select">
                    <option value="">时</option>
                    <option v-for="h in 24" :key="h" :value="String(h-1).padStart(2, '0')">
                      {{ String(h-1).padStart(2, '0') }}
                    </option>
                  </select>
                  <span>:</span>
                  <select v-model="appointmentMinute" class="time-select">
                    <option value="">分</option>
                    <option v-for="m in 60" :key="m" :value="String(m-1).padStart(2, '0')">
                      {{ String(m-1).padStart(2, '0') }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          
          <div class="form-section">
            <h3>选择归还地点</h3>
            <p class="hint">点击地图选择归还地点</p>
            <div class="map-container" ref="mapContainer"></div>
            <div class="location-info" v-if="selectedLocation">
              <span class="label">归还地点：</span>
              <span class="address">{{ selectedLocation.address }}</span>
            </div>
            <div class="location-info placeholder" v-else>
              <span>请在地图上点击选择归还地点</span>
            </div>
          </div>
          
          <div class="form-section">
            <h3>备注信息</h3>
            <textarea 
              v-model="appointmentNote"
              placeholder="可选，填写备注信息"
              rows="3"
            ></textarea>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeAppointmentForm">取消</button>
          <button 
            class="btn-submit" 
            @click="submitAppointment"
            :disabled="!canSubmit || submitting"
          >
            {{ submitting ? '发送中...' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useRouter } from 'vue-router';
import AppTopBar from '../components/AppTopBar.vue';

const router = useRouter();
const showToast = window.showToast;
const API_BASE = 'http://127.0.0.1:5000/api';

const owners = ref([]);
const loading = ref(true);
const bgImage = ref('');

// 预约表单相关
const showAppointmentForm = ref(false);
const currentItem = ref(null);
const appointmentDate = ref('');
const appointmentHour = ref('');
const appointmentMinute = ref('');
const appointmentNote = ref('');
const selectedLocation = ref(null);
const submitting = ref(false);
const mapContainer = ref(null);
let map = null;
let marker = null;

const pageStyle = computed(() => {
  if (bgImage.value) {
    return {
      background: `url(${bgImage.value}) center/cover`,
      minHeight: '100vh'
    };
  }
  return {};
});

const minDate = computed(() => {
  const today = new Date();
  return today.toISOString().split('T')[0];
});

const canSubmit = computed(() => {
  return (
    appointmentDate.value &&
    appointmentHour.value &&
    appointmentMinute.value &&
    selectedLocation.value
  );
});

function getAvatarUrl(avatar) {
  if (!avatar) return '';
  if (avatar.startsWith('http')) return avatar;
  if (avatar.startsWith('/')) return `http://127.0.0.1:5000${avatar}`;
  return `http://127.0.0.1:5000/${avatar}`;
}

function formatTime(timeStr) {
  if (!timeStr) return '未知时间';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN');
}

async function loadOwners() {
  loading.value = true;
  try {
    const userId = localStorage.getItem('user_id');
    const res = await fetch(`${API_BASE}/return-appointments/available-owners?user_id=${userId}`);
    const data = await res.json();
    
    if (data.success) {
      owners.value = data.data || [];
    } else {
      showToast(data.message || '加载失败', 'error');
    }
  } catch (error) {
    console.error('加载失主列表失败:', error);
    showToast('网络错误', 'error');
  } finally {
    loading.value = false;
  }
}

function goToUserProfile(userId) {
  router.push(`/user/${userId}`);
}

function startChat(userId) {
  router.push(`/chat?target=${userId}`);
}

function openAppointmentForm(item) {
  currentItem.value = item;
  appointmentDate.value = '';
  appointmentHour.value = '';
  appointmentMinute.value = '';
  appointmentNote.value = '';
  selectedLocation.value = null;
  showAppointmentForm.value = true;
  
  setTimeout(() => {
    initMap();
  }, 100);
}

function closeAppointmentForm() {
  showAppointmentForm.value = false;
  currentItem.value = null;
  if (map) {
    map.destroy();
    map = null;
  }
  marker = null;
}

function viewAppointment(item) {
  router.push('/appointments');
}

function initMap() {
  if (!window.AMap || !mapContainer.value) {
    console.error('高德地图API未加载或容器不存在');
    return;
  }
  
  map = new AMap.Map(mapContainer.value, {
    zoom: 17,
    center: [103.9885, 30.5815],
    viewMode: '2D'
  });
  
  map.on('click', (e) => {
    const lng = e.lnglat.getLng();
    const lat = e.lnglat.getLat();
    
    if (marker) {
      marker.setPosition([lng, lat]);
    } else {
      marker = new AMap.Marker({
        position: [lng, lat],
        title: '归还地点'
      });
      marker.setMap(map);
    }
    
    AMap.plugin('AMap.Geocoder', () => {
      const geocoder = new AMap.Geocoder();
      geocoder.getAddress([lng, lat], (status, result) => {
        if (status === 'complete' && result.regeocode) {
          selectedLocation.value = {
            lng: lng,
            lat: lat,
            address: result.regeocode.formattedAddress
          };
        } else {
          selectedLocation.value = {
            lng: lng,
            lat: lat,
            address: `${lng.toFixed(6)}, ${lat.toFixed(6)}`
          };
        }
      });
    });
  });
}

async function submitAppointment() {
  if (!canSubmit.value) {
    showToast('请填写所有必填项', 'error');
    return;
  }
  
  const appointmentTime = `${appointmentHour.value}:${appointmentMinute.value}`;
  const fullTime = `${appointmentDate.value} ${appointmentTime}`;
  const appointmentDateObj = new Date(fullTime);
  const now = new Date();
  
  if (appointmentDateObj <= now) {
    showToast('预约时间必须晚于当前时间', 'error');
    return;
  }
  
  submitting.value = true;
  
  try {
    const userId = localStorage.getItem('user_id');
    const res = await fetch(`${API_BASE}/return-appointments/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        item_id: currentItem.value.item_id,
        finder_id: userId,
        owner_id: currentItem.value.owner_id,
        appointment_date: appointmentDate.value,
        appointment_time: appointmentTime,
        location: selectedLocation.value.address,
        longitude: selectedLocation.value.lng,
        latitude: selectedLocation.value.lat,
        note: appointmentNote.value.trim()
      })
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast('预约归还申请已发送！', 'success');
      closeAppointmentForm();
      loadOwners();
    } else {
      showToast(data.message || '发送失败', 'error');
    }
  } catch (error) {
    console.error('提交预约失败:', error);
    showToast('网络错误', 'error');
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  const bg = localStorage.getItem('bg_image');
  if (bg) {
    bgImage.value = bg;
  }
  
  loadOwners();
});

onBeforeUnmount(() => {
  if (map) {
    map.destroy();
  }
});
</script>

<style scoped>
.return-appointment-page {
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
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #333;
}

.subtitle {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.loading,
.empty {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  color: #999;
}

.empty .hint {
  font-size: 13px;
  margin-top: 8px;
}

.owners-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.owner-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.item-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #333;
}

.item-desc {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.status-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.status-badge.available {
  background: #e6f7ff;
  color: #1890ff;
}

.status-badge.pending {
  background: #fff7e6;
  color: #fa8c16;
}

.card-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.owner-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s;
}

.owner-avatar:hover {
  transform: scale(1.05);
}

.owner-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.owner-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.owner-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  cursor: pointer;
}

.owner-name:hover {
  color: #1890ff;
}

.owner-label {
  margin: 0;
  font-size: 12px;
  color: #52c41a;
  background: #f6ffed;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
  width: fit-content;
}

.claim-time {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.actions {
  display: flex;
  gap: 12px;
}

.btn-appointment,
.btn-view,
.btn-chat {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
}

.btn-appointment {
  background: linear-gradient(135deg, #52c41a, #389e0d);
  color: white;
}

.btn-appointment:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.btn-view {
  background: #1890ff;
  color: white;
}

.btn-view:hover {
  background: #40a9ff;
}

.btn-chat {
  background: #f5f5f5;
  color: #666;
}

.btn-chat:hover {
  background: #e8e8e8;
}

/* 预约弹窗样式 */
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
}

.appointment-modal {
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
  color: #333;
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

.form-section {
  margin-bottom: 24px;
}

.form-section h3 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #333;
}

.form-section p {
  margin: 8px 0;
  font-size: 14px;
  color: #666;
}

.form-section .hint {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.time-picker {
  display: flex;
  gap: 16px;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
}

.date-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.time-selects {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-select {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
}

.map-container {
  width: 100%;
  height: 250px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  margin-bottom: 12px;
}

.location-info {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 14px;
}

.location-info.placeholder {
  text-align: center;
  color: #999;
}

.location-info .label {
  color: #666;
}

.location-info .address {
  color: #333;
  font-weight: 500;
}

textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
}

.btn-cancel,
.btn-submit {
  flex: 1;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
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

.btn-submit {
  background: linear-gradient(135deg, #52c41a, #389e0d);
  color: white;
}

.btn-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, #389e0d, #52c41a);
}

.btn-submit:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}
</style>
