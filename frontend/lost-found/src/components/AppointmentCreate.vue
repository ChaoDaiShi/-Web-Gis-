<template>
  <div class="appointment-create-page" :style="pageStyle">
    <AppTopBar />
    
    <div class="page-container">
      <div class="page-header">
        <h1>主动预约领取</h1>
        <p class="subtitle">选择物品后，在地图上标注双方约定的取回地点</p>
      </div>
      
      <div class="content-wrapper">
        <div class="left-panel">
          <div class="step-card">
            <div class="step-header">
              <span class="step-number">1</span>
              <h3>选择预约日期</h3>
            </div>
            <div class="step-content">
              <div class="form-group">
                <label>预约日期 *</label>
                <input 
                  type="date" 
                  v-model="selectedDate"
                  :min="minDate"
                  class="date-input"
                />
              </div>
              <div class="form-group">
                <label>预约时间 *</label>
                <input 
                  type="time" 
                  v-model="selectedTime"
                  class="time-input"
                />
              </div>
            </div>
          </div>
          
          <div class="step-card">
            <div class="step-header">
              <span class="step-number">2</span>
              <h3>选择要预约的物品</h3>
            </div>
            <div class="step-content">
              <div v-if="loadingItems" class="loading">加载物品列表中...</div>
              <div v-else-if="availableItems.length === 0" class="empty-items">
                <p>暂无可预约的物品</p>
                <p class="hint">只有拾到的物品（未被认领）才能预约领取</p>
              </div>
              <div v-else class="items-list">
                <div 
                  v-for="item in availableItems" 
                  :key="item.item_id"
                  :class="['item-card', { selected: selectedItem?.item_id === item.item_id }]"
                  @click="selectItem(item)"
                >
                  <div class="item-image" v-if="item.images && item.images.length">
                    <img :src="item.images[0]" alt="物品图片" />
                  </div>
                  <div class="item-image placeholder" v-else>
                    <span>📦</span>
                  </div>
                  <div class="item-info">
                    <h4>{{ item.title }}</h4>
                    <p class="item-desc">{{ item.description || '暂无描述' }}</p>
                    <p class="item-time">发布于 {{ formatTime(item.create_time) }}</p>
                  </div>
                  <div class="item-check" v-if="selectedItem?.item_id === item.item_id">
                    ✓
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="step-card" v-if="selectedItem">
            <div class="step-header">
              <span class="step-number">3</span>
              <h3>填写联系信息</h3>
            </div>
            <div class="step-content">
              <div class="form-group">
                <label>联系人姓名 *</label>
                <input 
                  type="text" 
                  v-model="contactName"
                  placeholder="请输入您的姓名"
                />
              </div>
              <div class="form-group">
                <label>联系电话 *</label>
                <input 
                  type="tel" 
                  v-model="contactPhone"
                  placeholder="请输入您的联系电话"
                  pattern="[0-9]{11}"
                />
              </div>
              <div class="form-group">
                <label>备注信息</label>
                <textarea 
                  v-model="note"
                  placeholder="可选，填写备注信息"
                  rows="3"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
        
        <div class="right-panel">
          <div class="map-card">
            <div class="map-header">
              <h3>在地图上标注取回地点</h3>
              <p class="hint">点击地图选择双方约定的取回位置</p>
            </div>
            <div class="map-container" ref="mapContainer"></div>
            <div class="location-info" v-if="selectedLocation">
              <div class="location-detail">
                <span class="label">取回地点：</span>
                <span class="address">{{ selectedLocation.address }}</span>
              </div>
              <div class="coords">
                经度: {{ selectedLocation.lng.toFixed(6) }} | 
                纬度: {{ selectedLocation.lat.toFixed(6) }}
              </div>
            </div>
            <div class="location-info placeholder" v-else>
              <p>请在地图上点击选择取回地点</p>
            </div>
            
            <div class="existing-markers" v-if="existingAppointments.length > 0">
              <h4>已有的预约取回点（仅相关方可见）</h4>
              <div class="markers-list">
                <div 
                  v-for="appt in existingAppointments" 
                  :key="appt.appointment_id"
                  class="marker-item"
                >
                  <span class="marker-status" :class="appt.status">
                    {{ getStatusText(appt.status) }}
                  </span>
                  <span class="marker-time">{{ formatDate(appt.appointment_time) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="action-buttons">
            <button class="btn-cancel" @click="handleCancel">取消</button>
            <button 
              class="btn-submit" 
              @click="handleSubmit"
              :disabled="!canSubmit || submitting"
            >
              {{ submitting ? '提交中...' : '提交预约' }}
            </button>
          </div>
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

const selectedDate = ref('');
const selectedTime = ref('');
const selectedItem = ref(null);
const contactName = ref('');
const contactPhone = ref('');
const note = ref('');
const selectedLocation = ref(null);
const submitting = ref(false);
const loadingItems = ref(true);
const availableItems = ref([]);
const existingAppointments = ref([]);
const mapContainer = ref(null);
const bgImage = ref('');
let map = null;
let marker = null;
let existingMarkers = [];

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
    selectedDate.value &&
    selectedTime.value &&
    selectedItem.value &&
    selectedLocation.value &&
    contactName.value.trim() &&
    contactPhone.value.trim()
  );
});

function formatTime(timeStr) {
  if (!timeStr) return '未知时间';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN');
}

function formatDate(timeStr) {
  if (!timeStr) return '未知';
  const date = new Date(timeStr);
  return date.toLocaleDateString('zh-CN');
}

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

async function loadAvailableItems() {
  loadingItems.value = true;
  try {
    const res = await fetch(`${API_BASE}/appointments/available-items`);
    const data = await res.json();
    
    if (data.success) {
      availableItems.value = (data.data || []).map(item => {
        let images = [];
        if (item.images) {
          if (Array.isArray(item.images)) {
            images = item.images;
          } else if (typeof item.images === 'string') {
            try {
              const parsed = JSON.parse(item.images);
              images = Array.isArray(parsed) ? parsed : [];
            } catch {
              images = [];
            }
          }
        }
        return {
          ...item,
          images: images.map(img => {
            if (img.startsWith('http')) return img;
            if (img.startsWith('/')) return `http://127.0.0.1:5000${img}`;
            return `http://127.0.0.1:5000/${img}`;
          })
        };
      });
    } else {
      showToast(data.message || '加载物品失败', 'error');
    }
  } catch (error) {
    console.error('加载物品列表失败:', error);
    showToast('网络错误', 'error');
  } finally {
    loadingItems.value = false;
  }
}

function selectItem(item) {
  selectedItem.value = item;
  loadExistingAppointments(item.item_id);
  
  if (map && item.longitude && item.latitude) {
    map.setCenter([item.longitude, item.latitude]);
    
    new AMap.Marker({
      position: [item.longitude, item.latitude],
      title: '物品位置',
      icon: new AMap.Icon({
        size: new AMap.Size(25, 34),
        image: 'https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-red.png',
        imageSize: new AMap.Size(25, 34)
      })
    }).setMap(map);
  }
}

async function loadExistingAppointments(itemId) {
  try {
    const userId = localStorage.getItem('user_id');
    const res = await fetch(`${API_BASE}/appointments/item/${itemId}?user_id=${userId}`);
    const data = await res.json();
    
    if (data.success) {
      existingAppointments.value = data.data || [];
      renderExistingMarkers();
    }
  } catch (error) {
    console.error('加载已有预约失败:', error);
  }
}

function renderExistingMarkers() {
  existingMarkers.forEach(m => m.setMap(null));
  existingMarkers = [];
  
  if (!map || existingAppointments.value.length === 0) return;
  
  existingAppointments.value.forEach(appt => {
    if (appt.longitude && appt.latitude) {
      const m = new AMap.Marker({
        position: [appt.longitude, appt.latitude],
        title: `预约取回点 - ${getStatusText(appt.status)}`,
        icon: new AMap.Icon({
          size: new AMap.Size(25, 34),
          image: 'https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-default.png',
          imageSize: new AMap.Size(25, 34)
        }),
        label: {
          content: `<div style="background:#fff;padding:2px 6px;border-radius:4px;font-size:12px;border:1px solid #ccc;">${getStatusText(appt.status)}</div>`,
          offset: new AMap.Pixel(-15, -45)
        }
      });
      m.setMap(map);
      existingMarkers.push(m);
    }
  });
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
        title: '取回地点',
        icon: new AMap.Icon({
          size: new AMap.Size(25, 34),
          image: 'https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-default.png',
          imageSize: new AMap.Size(25, 34)
        })
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

async function handleSubmit() {
  if (!canSubmit.value) {
    showToast('请填写所有必填项', 'error');
    return;
  }
  
  const appointmentTime = `${selectedDate.value} ${selectedTime.value}`;
  const appointmentDate = new Date(appointmentTime);
  const now = new Date();
  
  if (appointmentDate <= now) {
    showToast('预约时间必须晚于当前时间', 'error');
    return;
  }
  
  submitting.value = true;
  
  try {
    const userId = localStorage.getItem('user_id');
    const res = await fetch(`${API_BASE}/appointments/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        item_id: selectedItem.value.item_id,
        user_id: userId,
        appointment_time: appointmentTime,
        location: selectedLocation.value.address,
        longitude: selectedLocation.value.lng,
        latitude: selectedLocation.value.lat,
        contact_name: contactName.value.trim(),
        contact_phone: contactPhone.value.trim(),
        note: note.value.trim()
      })
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast('预约申请提交成功！', 'success');
      router.push('/appointments');
    } else {
      showToast(data.message || '提交失败', 'error');
    }
  } catch (error) {
    console.error('提交预约失败:', error);
    showToast('网络错误，请稍后重试', 'error');
  } finally {
    submitting.value = false;
  }
}

function handleCancel() {
  router.back();
}

onMounted(() => {
  const bg = localStorage.getItem('bg_image');
  if (bg) {
    bgImage.value = bg;
  }
  
  loadAvailableItems();
  
  setTimeout(() => {
    initMap();
  }, 100);
});

onBeforeUnmount(() => {
  if (map) {
    map.destroy();
  }
});
</script>

<style scoped>
.appointment-create-page {
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
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #333;
}

.subtitle {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.content-wrapper {
  display: flex;
  gap: 20px;
}

.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-panel {
  width: 500px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.step-number {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #1890ff, #40a9ff);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.step-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.step-content {
  padding-left: 40px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.3s;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: #1890ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.date-input,
.time-input {
  max-width: 200px;
}

.loading,
.empty-items {
  text-align: center;
  padding: 24px;
  color: #999;
}

.empty-items .hint {
  font-size: 12px;
  margin-top: 8px;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.item-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 2px solid #e8e8e8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.item-card:hover {
  border-color: #1890ff;
}

.item-card.selected {
  border-color: #1890ff;
  background: #e6f7ff;
}

.item-image {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-image.placeholder {
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #333;
}

.item-desc {
  margin: 0 0 4px 0;
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-time {
  margin: 0;
  font-size: 11px;
  color: #999;
}

.item-check {
  width: 24px;
  height: 24px;
  background: #1890ff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.map-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.map-header {
  margin-bottom: 12px;
}

.map-header h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #333;
}

.map-header .hint {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.map-container {
  width: 100%;
  height: 350px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.location-info {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.location-info.placeholder {
  text-align: center;
  color: #999;
}

.location-info.placeholder p {
  margin: 0;
}

.location-detail {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.location-detail .label {
  color: #666;
  font-size: 13px;
}

.location-detail .address {
  color: #333;
  font-size: 13px;
  font-weight: 500;
}

.coords {
  font-size: 11px;
  color: #999;
}

.existing-markers {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
}

.existing-markers h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #666;
}

.markers-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.marker-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
}

.marker-status {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.marker-status.pending {
  background: #fff7e6;
  color: #fa8c16;
}

.marker-status.approved {
  background: #e6f7ff;
  color: #1890ff;
}

.marker-status.completed {
  background: #f6ffed;
  color: #52c41a;
}

.marker-time {
  color: #999;
}

.action-buttons {
  display: flex;
  gap: 12px;
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
  background: linear-gradient(135deg, #1890ff, #40a9ff);
  color: white;
}

.btn-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, #40a9ff, #1890ff);
}

.btn-submit:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .content-wrapper {
    flex-direction: column;
  }
  
  .right-panel {
    width: 100%;
  }
}
</style>
