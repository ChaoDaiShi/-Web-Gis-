<script setup>
import { ref, onMounted, watch } from "vue";

const props = defineProps({
  visible: Boolean,
  initialLng: Number,
  initialLat: Number,
});

const emit = defineEmits(["close", "submit"]);

const API_BASE = 'http://127.0.0.1:5000/api';

const title = ref("");
const description = ref("");
const categoryId = ref(1);
const priority = ref(1);
const categories = ref([]);
const images = ref([]);
const isSubmitting = ref(false);

const lng = ref(props.initialLng || 0);
const lat = ref(props.initialLat || 0);

const imageInputRef = ref(null);
const showImageFeedback = ref(false);
const feedbackMessage = ref('');

watch(() => props.visible, (newVal) => {
  if (newVal) {
    title.value = "";
    description.value = "";
    categoryId.value = 1;
    priority.value = 1;
    images.value = [];
    lng.value = props.initialLng || 0;
    lat.value = props.initialLat || 0;
  }
});

watch(() => props.initialLng, (newVal) => {
  lng.value = newVal || 0;
});

watch(() => props.initialLat, (newVal) => {
  lat.value = newVal || 0;
});

async function loadCategories() {
  try {
    const res = await fetch("http://127.0.0.1:5000/api/repair/categories");
    const data = await res.json();
    if (data.success && data.data) {
      categories.value = data.data;
    }
  } catch (e) {
    console.error("加载报修分类失败:", e);
  }
}

function showFeedback(message) {
  feedbackMessage.value = message;
  showImageFeedback.value = true;
  setTimeout(() => {
    showImageFeedback.value = false;
  }, 2000);
}

function handleImageUpload(event) {
  const target = event.target;
  const files = Array.from(target.files || []);
  const validFiles = files.filter(file => file.type.startsWith('image/'));
  
  if (validFiles.length === 0) {
    showFeedback('请选择图片文件');
    target.value = '';
    return;
  }
  
  const remaining = 5 - images.value.length;
  const toAdd = validFiles.slice(0, remaining);
  
  const newImages = [...images.value];
  toAdd.forEach(file => {
    newImages.push(file);
  });
  images.value = newImages;
  
  if (toAdd.length < validFiles.length) {
    showFeedback(`已添加 ${toAdd.length} 张图片（最多5张）`);
  } else {
    showFeedback(`已添加 ${toAdd.length} 张图片`);
  }
  
  target.value = '';
}

function getImageUrl(img) {
  if (!img || typeof img !== 'object' || !img.type || !img.type.startsWith('image/')) {
    return '';
  }
  try {
    if (typeof URL !== 'undefined' && URL.createObjectURL) {
      return URL.createObjectURL(img);
    }
  } catch (e) {
    console.error('Failed to create object URL:', e);
  }
  return '';
}

function removeImage(index) {
  images.value.splice(index, 1);
}

function triggerImageUpload() {
  const input = imageInputRef.value || document.getElementById('repairImageInput');
  if (input) {
    input.click();
  } else {
    console.error('图片上传输入框未找到');
  }
}

async function handleSubmit(event) {
  if (event) {
    event.preventDefault();
  }
  
  if (isSubmitting.value) {
    return;
  }

  const repairTitle = title.value.trim();
  const repairDescription = description.value.trim();

  if (!repairTitle) {
    alert("请填写维修物品");
    return;
  }

  if (!repairDescription) {
    alert("请填写问题描述");
    return;
  }

  if (!lng.value || !lat.value) {
    alert("请先在地图上选择位置");
    return;
  }

  isSubmitting.value = true;

  const formData = new FormData();
  formData.append('title', repairTitle);
  formData.append('description', repairDescription);
  formData.append('repair_category_id', categoryId.value.toString());
  formData.append('reporter_id', (localStorage.getItem("user_id") || '1').toString());
  formData.append('priority', priority.value.toString());
  formData.append('lng', lng.value.toString());
  formData.append('lat', lat.value.toString());

  for (let i = 0; i < images.value.length; i++) {
    formData.append('images', images.value[i]);
  }

  try {
    const res = await fetch('http://127.0.0.1:5000/api/repair', {
      method: 'POST',
      body: formData,
    });

    const result = await res.json();
    
    if (result.success) {
      alert("报修提交成功！");
      emit("submit", result);
      handleClose();
      return;
    } else {
      alert("提交失败: " + (result.message || '未知错误'));
    }
  } catch (error) {
    console.error("提交报修失败:", error);
    alert("提交失败，请稍后重试");
  } finally {
    isSubmitting.value = false;
  }
}

function handleClose() {
  images.value = [];
  emit("close");
}

onMounted(() => {
  loadCategories();
});
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="handleClose">
    <div class="modal">
      <div class="modal-header">
        <h3>报修申请</h3>
        <button class="close-btn" @click="handleClose">×</button>
      </div>
      
      <div class="modal-body">
        <div class="form-item">
          <label>位置信息</label>
          <div class="location-info">
            <span>📍 经度: {{ lng.toFixed(6) }}</span>
            <span>纬度: {{ lat.toFixed(6) }}</span>
          </div>
        </div>
        
        <div class="form-item">
          <label>维修物品</label>
          <input 
            v-model="title" 
            type="text" 
            placeholder="请输入维修物品"
            class="input-field"
          />
        </div>
        
        <div class="form-item">
          <label>报修类型</label>
          <select v-model="categoryId" class="input-field">
            <option 
              v-for="cat in categories" 
              :key="cat.repair_category_id" 
              :value="cat.repair_category_id"
            >
              {{ cat.icon || '📋' }} {{ cat.name }}
            </option>
          </select>
        </div>
        
        <div class="form-item">
          <label>优先级</label>
          <div class="priority-buttons">
            <button 
              :class="['priority-btn', 'low', { active: priority === 1 }]"
              @click="priority = 1"
            >
              低
            </button>
            <button 
              :class="['priority-btn', 'medium', { active: priority === 2 }]"
              @click="priority = 2"
            >
              中
            </button>
            <button 
              :class="['priority-btn', 'high', { active: priority === 3 }]"
              @click="priority = 3"
            >
              高
            </button>
          </div>
        </div>
        
        <div class="form-item">
          <label>问题描述</label>
          <textarea 
            v-model="description" 
            placeholder="请详细描述问题"
            class="input-field textarea"
            rows="4"
          ></textarea>
        </div>
        
        <div class="form-item">
          <label>图片</label>
          <div class="image-upload-area">
            <div 
              v-if="images.length === 0" 
              class="upload-placeholder"
              @click="triggerImageUpload"
            >
              <div class="upload-box">
                <span class="plus-icon">+</span>
                <span class="upload-text">添加图片</span>
              </div>
              <span class="upload-hint">最多上传5张图片</span>
            </div>
            <div v-else class="image-list">
              <div 
                v-for="(img, index) in images" 
                :key="index" 
                class="image-item"
              >
                <img :src="getImageUrl(img)" alt="图片" />
                <button class="remove-btn" @click="removeImage(index)">×</button>
              </div>
              <div 
                v-if="images.length < 5" 
                class="add-more" 
                @click="triggerImageUpload"
              >
                <span class="plus-icon">+</span>
              </div>
            </div>
          </div>
          <input
            ref="imageInputRef"
            type="file"
            accept="image/*"
            multiple
            style="display: none"
            @change="handleImageUpload"
          />
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="cancel-btn" @click="handleClose">取消</button>
        <button 
          class="submit-btn" 
          @click="handleSubmit"
          :disabled="isSubmitting"
          type="button"
        >
          {{ isSubmitting ? '提交中...' : '提交报修' }}
        </button>
      </div>
      
      <div v-if="showImageFeedback" class="image-feedback">
        {{ feedbackMessage }}
      </div>
    </div>
  </div>
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

.modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e5e5;
  background: #fef3c7;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #92400e;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #92400e;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.1);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.input-field {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.input-field:focus {
  outline: none;
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
}

.textarea {
  resize: vertical;
  min-height: 80px;
}

.location-info {
  display: flex;
  gap: 16px;
  padding: 8px 12px;
  background: #fef9e7;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
}

.priority-buttons {
  display: flex;
  gap: 8px;
}

.priority-btn {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.priority-btn.low {
  color: #166534;
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.priority-btn.low.active {
  background: #22c55e;
  color: white;
  border-color: #22c55e;
}

.priority-btn.medium {
  color: #92400e;
  border-color: #fde68a;
  background: #fffbeb;
}

.priority-btn.medium.active {
  background: #f59e0b;
  color: white;
  border-color: #f59e0b;
}

.priority-btn.high {
  color: #991b1b;
  border-color: #fecaca;
  background: #fef2f2;
}

.priority-btn.high.active {
  background: #ef4444;
  color: white;
  border-color: #ef4444;
}

.image-upload-area {
  border: none;
  overflow: hidden;
}

.upload-placeholder {
  padding: 0;
  text-align: left;
  cursor: pointer;
  background: transparent;
  transition: all 0.2s;
  display: inline-block;
}

.upload-placeholder:hover .upload-box {
  border-color: #3b82f6;
}

.upload-box {
  width: 100px;
  height: 100px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s;
}

.plus-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #d1d5db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 8px;
  transition: background-color 0.2s;
}

.upload-placeholder:hover .plus-icon {
  background: #3b82f6;
}

.upload-text {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.upload-hint {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
  display: block;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
}

.image-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 6px;
  overflow: hidden;
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-more {
  width: 80px;
  height: 80px;
  border: 2px dashed #d1d5db;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: #fafafa;
}

.add-more:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.add-more .plus-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #d1d5db;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  margin-bottom: 4px;
  transition: background-color 0.2s;
}

.add-more:hover .plus-icon {
  background: #3b82f6;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e5e5e5;
  background: #fafafa;
}

.cancel-btn {
  padding: 10px 20px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn:hover {
  background: #f5f5f5;
}

.submit-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  background: #f59e0b;
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.submit-btn:hover {
  background: #d97706;
}

.submit-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

.image-feedback {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #333;
  color: white;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  z-index: 1001;
}
</style>