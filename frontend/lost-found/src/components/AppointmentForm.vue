<template>
  <div class="appointment-form-overlay" @click.self="handleClose">
    <div class="appointment-form-modal">
      <div class="modal-header">
        <h2>预约领取物品</h2>
        <button class="close-btn" @click="handleClose">×</button>
      </div>
      
      <div class="modal-body">
        <div class="item-info" v-if="itemInfo">
          <h3>物品信息</h3>
          <p><strong>物品名称：</strong>{{ itemInfo.title }}</p>
          <p><strong>物品描述：</strong>{{ itemInfo.description || '暂无描述' }}</p>
          <p><strong>发布时间：</strong>{{ formatTime(itemInfo.create_time) }}</p>
        </div>
        
        <form @submit.prevent="handleSubmit">
          <div class="form-section">
            <h3>预约信息</h3>
            
            <div class="form-group">
              <label for="appointment_time">预约时间 *</label>
              <input 
                type="datetime-local" 
                id="appointment_time" 
                v-model="formData.appointment_time"
                :min="minDateTime"
                required
              />
            </div>
            
            <div class="form-group">
              <label>领取地点 * <span class="hint">(点击地图标注)</span></label>
              <div class="map-container" ref="mapContainer"></div>
              <input 
                type="text" 
                v-model="formData.location"
                placeholder="请点击地图选择领取地点"
                readonly
                class="location-input"
              />
              <p class="coord-info" v-if="formData.longitude && formData.latitude">
                坐标：{{ formData.longitude.toFixed(6) }}, {{ formData.latitude.toFixed(6) }}
              </p>
            </div>
            
            <div class="form-group">
              <label for="contact_name">联系人姓名 *</label>
              <input 
                type="text" 
                id="contact_name" 
                v-model="formData.contact_name"
                placeholder="请输入联系人姓名"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="contact_phone">联系电话 *</label>
              <input 
                type="tel" 
                id="contact_phone" 
                v-model="formData.contact_phone"
                placeholder="请输入联系电话"
                pattern="[0-9]{11}"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="note">备注信息</label>
              <textarea 
                id="note" 
                v-model="formData.note"
                placeholder="请输入备注信息（选填）"
                rows="3"
              ></textarea>
            </div>
          </div>
          
          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="handleClose">取消</button>
            <button type="submit" class="btn-submit" :disabled="submitting">
              {{ submitting ? '提交中...' : '提交预约' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter } from 'vue-router';

const props = defineProps({
  itemId: {
    type: Number,
    required: true
  },
  itemInfo: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close', 'success']);
const router = useRouter();
const showToast = window.showToast;

const API_BASE = 'http://127.0.0.1:5000/api';
const mapContainer = ref(null);
let map = null;
let marker = null;

const formData = ref({
  appointment_time: '',
  location: '',
  longitude: null,
  latitude: null,
  contact_name: '',
  contact_phone: '',
  note: ''
});

const submitting = ref(false);

const minDateTime = computed(() => {
  const now = new Date();
  now.setMinutes(now.getMinutes() + 30);
  return now.toISOString().slice(0, 16);
});

function formatTime(timeStr) {
  if (!timeStr) return '未知时间';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN');
}

function initMap() {
  if (!window.AMap) {
    console.error('高德地图API未加载');
    return;
  }
  
  const center = props.itemInfo && props.itemInfo.longitude 
    ? [props.itemInfo.longitude, props.itemInfo.latitude]
    : [103.9885, 30.5815];
  
  map = new AMap.Map(mapContainer.value, {
    zoom: 17,
    center: center,
    viewMode: '2D'
  });
  
  if (props.itemInfo && props.itemInfo.longitude) {
    new AMap.Marker({
      position: [props.itemInfo.longitude, props.itemInfo.latitude],
      title: '物品位置',
      icon: new AMap.Icon({
        size: new AMap.Size(25, 34),
        image: 'https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-red.png',
        imageSize: new AMap.Size(25, 34)
      })
    }).setMap(map);
  }
  
  map.on('click', (e) => {
    const lng = e.lnglat.getLng();
    const lat = e.lnglat.getLat();
    
    formData.value.longitude = lng;
    formData.value.latitude = lat;
    
    if (marker) {
      marker.setPosition([lng, lat]);
    } else {
      marker = new AMap.Marker({
        position: [lng, lat],
        title: '领取地点',
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
          formData.value.location = result.regeocode.formattedAddress;
        } else {
          formData.value.location = `${lng.toFixed(6)}, ${lat.toFixed(6)}`;
        }
      });
    });
  });
}

async function handleSubmit() {
  if (!formData.value.longitude || !formData.value.latitude) {
    showToast('请在地图上选择领取地点', 'error');
    return;
  }
  
  if (!formData.value.appointment_time) {
    showToast('请选择预约时间', 'error');
    return;
  }
  
  const appointmentDate = new Date(formData.value.appointment_time);
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
        item_id: props.itemId,
        user_id: userId,
        appointment_time: formData.value.appointment_time,
        location: formData.value.location,
        longitude: formData.value.longitude,
        latitude: formData.value.latitude,
        contact_name: formData.value.contact_name,
        contact_phone: formData.value.contact_phone,
        note: formData.value.note
      })
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast('预约申请提交成功！', 'success');
      emit('success');
      handleClose();
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

function handleClose() {
  if (map) {
    map.destroy();
    map = null;
  }
  emit('close');
}

onMounted(() => {
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
.appointment-form-overlay {
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

.appointment-form-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
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
  font-size: 20px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
}

.item-info {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.item-info h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.item-info p {
  margin: 8px 0;
  font-size: 14px;
  color: #666;
}

.form-section {
  margin-bottom: 24px;
}

.form-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.hint {
  font-weight: normal;
  color: #999;
  font-size: 12px;
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

.location-input {
  background: #f5f7fa;
  cursor: not-allowed;
}

.map-container {
  width: 100%;
  height: 300px;
  border-radius: 8px;
  margin-bottom: 12px;
  border: 1px solid #d9d9d9;
}

.coord-info {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel,
.btn-submit {
  padding: 10px 24px;
  border-radius: 6px;
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
  background: #1890ff;
  color: white;
}

.btn-submit:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-submit:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}
</style>
