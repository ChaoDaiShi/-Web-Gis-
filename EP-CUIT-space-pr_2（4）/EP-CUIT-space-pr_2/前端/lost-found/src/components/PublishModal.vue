<script setup>
import { ref, watch, nextTick } from 'vue';

const props = defineProps({
  show: Boolean,
  pendingLocation: {
    type: Object,
    default: null
  },
  categories: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['close', 'submit', 'clearLocation', 'selectLocation']);

const API_BASE = 'http://127.0.0.1:5000/api';

const pubTitle = ref('');
const pubDetail = ref('');
const pubPhone = ref('');
const pubType = ref('lost');
const pubImages = ref([]);
const pubCategory = ref(1);
const localPendingLocation = ref(null);
const isSubmitting = ref(false);

const imageInputRef = ref(null);

watch(() => props.show, (newVal) => {
  if (newVal) {
    pubTitle.value = '';
    pubDetail.value = '';
    pubPhone.value = '';
    pubType.value = 'lost';
    pubImages.value = [];
    localPendingLocation.value = props.pendingLocation;
    if (props.categories.length > 0) {
      const otherCategory = props.categories.find(cat => cat.name === '其他');
      pubCategory.value = otherCategory ? otherCategory.category_id : props.categories[0].category_id;
    }
  }
});

watch(() => props.pendingLocation, (newVal) => {
  localPendingLocation.value = newVal;
});

const showImageFeedback = ref(false);
const feedbackMessage = ref('');

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
  
  const remaining = 5 - pubImages.value.length;
  const toAdd = validFiles.slice(0, remaining);
  
  const newImages = [...pubImages.value];
  toAdd.forEach(file => {
    newImages.push(file);
  });
  pubImages.value = newImages;
  
  if (toAdd.length < validFiles.length) {
    showFeedback(`已添加 ${toAdd.length} 张图片（最多5张）`);
  } else {
    showFeedback(`已添加 ${toAdd.length} 张图片`);
  }
  
  target.value = '';
  console.log('当前图片数量:', pubImages.value.length);
}

function removeImage(index) {
  pubImages.value.splice(index, 1);
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

function triggerImageUpload() {
  const input = imageInputRef.value || document.getElementById('publishImageInput');
  if (input) {
    input.click();
  } else {
    console.error('图片上传输入框未找到');
  }
}

function clearLocation() {
  localPendingLocation.value = null;
  emit('clearLocation');
}

function selectLocation() {
  emit('selectLocation');
}

async function handleSubmit() {
  const title = pubTitle.value.trim();
  const detail = pubDetail.value.trim();
  const phone = pubPhone.value.trim();

  if (!title || !detail) {
    showToast('标题和描述不能为空', 'warning');
    return;
  }

  isSubmitting.value = true;

  const userId = localStorage.getItem('user_id');
  const type = pubType.value === 'lost' ? 0 : 1;
  const status = 0;

  const formData = new FormData();
  formData.append('user_id', userId || '');
  formData.append('title', title);
  formData.append('detail', detail);
  formData.append('phone', phone);
  formData.append('lng', localPendingLocation.value?.lng || '');
  formData.append('lat', localPendingLocation.value?.lat || '');
  formData.append('type', type);
  formData.append('status', status);
  formData.append('category_id', pubCategory.value);

  pubImages.value.forEach((file) => {
    formData.append('images', file);
  });

  try {
    const res = await fetch(`${API_BASE}/map/publish`, {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (data.success) {
      showToast('发布成功', 'success');
      setTimeout(() => {
        emit('submit', data);
        handleClose();
      }, 1000);
    } else {
      showToast(data.message || '发布失败', 'error');
    }
  } catch (error) {
    console.error(error);
    showToast('发布接口异常', 'error');
  } finally {
    isSubmitting.value = false;
  }
}

function handleClose() {
  pubImages.value = [];
  emit('close');
}
</script>

<template>
  <div class="publish-modal-mask" :style="{ display: show ? 'flex' : 'none' }">
    <div class="publish-modal">
      <div class="modal-header">
        <h3>发布信息</h3>
        <button class="close-btn" type="button" @click="handleClose" title="关闭">×</button>
      </div>
      
      <div class="modal-body">
        <div class="form-row">
          <label for="pubTitle">标题</label>
          <input id="pubTitle" v-model="pubTitle" type="text" placeholder="请输入标题" />
        </div>
        
        <div class="form-row">
          <label for="pubDetail">描述</label>
          <textarea id="pubDetail" v-model="pubDetail" placeholder="请输入详细描述"></textarea>
        </div>
        
        <div class="form-row">
          <label>类型</label>
          <div class="type-buttons">
            <button
              :class="{ active: pubType === 'lost' }"
              @click="pubType = 'lost'"
            >
              丢失物品
            </button>
            <button
              :class="{ active: pubType === 'found' }"
              @click="pubType = 'found'"
            >
              拾到物品
            </button>
          </div>
        </div>
        
        <div class="form-row">
          <label for="pubCategory">分类</label>
          <select id="pubCategory" v-model="pubCategory">
            <option v-for="cat in categories" :key="cat.category_id" :value="cat.category_id">
              {{ cat.name }}
            </option>
          </select>
        </div>
        
        <div class="form-row">
          <label>位置</label>
          <div class="location-hint">
            <span v-if="localPendingLocation">已选择位置</span>
            <span v-else class="hint-text">点击下方按钮选择位置（非必填）</span>
            <div class="location-actions">
              <button v-if="localPendingLocation" class="btn btn-sm" @click="clearLocation">清除位置</button>
              <button v-else class="btn btn-sm primary" @click="selectLocation">选择位置</button>
            </div>
          </div>
        </div>
        
        <div class="form-row">
          <label>图片</label>
          <div class="image-upload">
            <input 
              id="publishImageInput"
              ref="imageInputRef"
              type="file" 
              multiple 
              accept="image/*" 
              @change="handleImageUpload" 
              style="display: none" 
            />
            <div class="upload-grid">
              <div 
                v-for="(img, index) in pubImages" 
                :key="index" 
                class="uploaded-image"
                v-show="img && typeof img === 'object' && img.type && img.type.startsWith('image/')"
              >
                <img :src="getImageUrl(img)" :alt="`图片${index + 1}`" />
                <button class="remove-btn" type="button" @click.stop="removeImage(index)">×</button>
              </div>
              <div 
                v-if="pubImages.length < 5" 
                class="add-image-box"
                @click="triggerImageUpload"
              >
                <span class="plus-icon">+</span>
                <span class="add-text">添加图片</span>
              </div>
            </div>
            <transition name="fade">
              <div v-if="showImageFeedback" class="upload-feedback">{{ feedbackMessage }}</div>
            </transition>
            <div class="upload-tip">最多上传5张图片</div>
          </div>
        </div>
        
        <div class="form-row">
          <label for="pubPhone">联系方式</label>
          <input id="pubPhone" v-model="pubPhone" type="text" placeholder="请输入联系方式" />
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn" type="button" @click="handleClose" :disabled="isSubmitting">取消</button>
        <button class="btn primary" type="button" @click="handleSubmit" :disabled="isSubmitting">
          {{ isSubmitting ? '发布中...' : '发布' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.publish-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.publish-modal {
  width: min(500px, 90vw);
  max-height: 85vh;
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

.form-row {
  margin-bottom: 14px;
}

.form-row label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-row input,
.form-row textarea,
.form-row select {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-row textarea {
  min-height: 84px;
  resize: vertical;
}

.type-buttons {
  display: flex;
  gap: 10px;
}

.type-buttons button {
  flex: 1;
  border: 1px solid #9ca3af;
  border-radius: 8px;
  padding: 10px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.type-buttons button:hover {
  border-color: #6b7280;
}

.type-buttons button.active {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.location-hint {
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.location-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.btn.btn-sm.primary {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.hint-text {
  color: #6b7280;
  font-size: 13px;
}

.btn.btn-sm {
  padding: 4px 10px;
  font-size: 13px;
}

.image-upload {
  margin-top: 6px;
}

.upload-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.uploaded-image {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.add-image-box {
  width: 80px;
  height: 80px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #f9fafb;
}

.add-image-box:hover {
  border-color: #2563eb;
  background: #eff6ff;
}

.plus-icon {
  font-size: 28px;
  color: #9ca3af;
  line-height: 1;
  margin-bottom: 4px;
}

.add-image-box:hover .plus-icon {
  color: #2563eb;
}

.add-text {
  font-size: 12px;
  color: #9ca3af;
}

.add-image-box:hover .add-text {
  color: #2563eb;
}

.upload-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #9ca3af;
}

.uploaded-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #dc2626;
  color: #fff;
  border: 2px solid #fff;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.upload-feedback {
  margin-top: 8px;
  padding: 8px 12px;
  background: #dcfce7;
  color: #166534;
  border-radius: 6px;
  font-size: 13px;
  text-align: center;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.modal-footer {
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn {
  padding: 10px 18px;
  border: 1px solid #9ca3af;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.primary {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.btn.primary:hover:not(:disabled) {
  background: #1d4ed8;
}
</style>
