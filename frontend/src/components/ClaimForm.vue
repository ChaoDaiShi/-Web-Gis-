<!-- 认领表单 -->
<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";

const showToast = window.showToast;
const showConfirm = window.showConfirm;

const props = defineProps({
  show: Boolean,
  item: {
    type: Object,
    default: null
  },
  username: {
    type: String,
    default: ""
  },
  avatarUrl: {
    type: String,
    default: ""
  }
});

const emit = defineEmits(['submit', 'cancel', 'success']);

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");

const formData = ref({
  item_id: "",
  username: "",
  applicant_name: "",
  applicant_phone: "",
  claim_reason: "",
  item_description: "",
  proof_images: []
});

const isFormModified = ref(false);
let originalFormData = "";

const verificationCode = ref('');
const generatedCode = ref('');

const isSubmitting = ref(false);
const MAX_IMAGES = 5;
const previewImages = ref([]);

const DRAFT_KEY_PREFIX = 'claim_form_draft_';

function generateCode() {
  generatedCode.value = Math.random().toString().substring(2, 7);
}

function getDraftKey() {
  const itemId = props.item?.id || props.item?.item_id || 'no_item';
  return `${DRAFT_KEY_PREFIX}${itemId}`;
}

function saveDraft() {
  const draftData = {
    formData: { ...formData.value },
    timestamp: Date.now()
  };
  localStorage.setItem(getDraftKey(), JSON.stringify(draftData));
  console.log('草稿已保存:', getDraftKey());
}

function loadDraft() {
  const draftStr = localStorage.getItem(getDraftKey());
  if (draftStr) {
    try {
      const draftData = JSON.parse(draftStr);
      return draftData.formData;
    } catch (e) {
      console.error('加载草稿失败:', e);
      return null;
    }
  }
  return null;
}

function clearDraft() {
  localStorage.removeItem(getDraftKey());
  console.log('草稿已清除:', getDraftKey());
}

async function checkAndRestoreDraft() {
  const draft = loadDraft();
  if (draft) {
    const confirmed = await window.showConfirm({title: '恢复申请', message: '检测到未完成的认领申请，是否恢复？', type: 'info', confirmText: '恢复'});
    if (confirmed) {
      Object.assign(formData.value, draft);
      console.log('草稿已恢复:', formData.value);
    }
    clearDraft();
  }
}

function handleBeforeUnload(e) {
  if (isFormModified.value) {
    e.preventDefault();
    e.returnValue = '';
    saveDraft();
  }
}

watch(() => props.show, (newShow) => {
  if (newShow) {
    formData.value.item_id = props.item?.id || props.item?.item_id || '';
    const storedUsername = localStorage.getItem('username') || '';
    formData.value.username = props.username || storedUsername;
    generateCode();
    
    setTimeout(() => {
      originalFormData = JSON.stringify(formData.value);
      checkAndRestoreDraft();
    }, 100);
  }
});

watch(() => props.item, (newItem) => {
  if (newItem) {
    formData.value.item_id = newItem.id || newItem.item_id || '';
  }
}, { immediate: true });

watch(formData, (newVal) => {
  if (originalFormData) {
    isFormModified.value = JSON.stringify(newVal) !== originalFormData;
  }
}, { deep: true });

async function submitClaim() {
  if (!validateForm()) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    const formDataToSubmit = new FormData();
    formDataToSubmit.append('username', formData.value.username);
    formDataToSubmit.append('applicant_name', formData.value.applicant_name);
    formDataToSubmit.append('applicant_phone', formData.value.applicant_phone);
    formDataToSubmit.append('claim_reason', formData.value.claim_reason);
    formDataToSubmit.append('item_description', formData.value.item_description);
    formDataToSubmit.append('user_id', userId);
    if (formData.value.item_id) {
      formDataToSubmit.append('item_id', formData.value.item_id);
    }
    
    previewImages.value.forEach((image, index) => {
      formDataToSubmit.append(`proof_images[${index}]`, image.file);
    });
    
    console.log('DEBUG: 准备提交表单');
    console.log('DEBUG: API地址:', `${API_BASE}/my/claim-forms`);
    console.log('DEBUG: 图片数量:', previewImages.value.length);
    console.log('DEBUG: FormData内容:');
    for (let [key, value] of formDataToSubmit.entries()) {
      console.log(`  ${key}:`, typeof value === 'object' ? `[File: ${value.name}]` : value);
    }
    
    const response = await fetch(`${API_BASE}/admin/claim-forms`, {
      method: "POST",
      body: formDataToSubmit,
    });
    
    console.log('DEBUG: 请求已发送，响应状态:', response.status);
    
    const data = await response.json();
    
    if (data.success) {
      clearDraft();
      isFormModified.value = false;
      emit('success');
    } else {
      showToast("提交失败: " + (data.message || "请重试"), "error");
    }
  } catch (error) {
    console.error("提交认领申请失败:", error);
    showToast("提交失败，请检查网络连接后重试", "error");
  } finally {
    isSubmitting.value = false;
  }
}

function validateForm() {
  if (!formData.value.applicant_phone?.trim()) {
    showToast("请输入联系方式（电话/QQ/微信/邮箱）", "warning");
    return false;
  }
  
  if (!formData.value.claim_reason?.trim()) {
    showToast("请输入认领理由", "warning");
    return false;
  }
  
  if (!formData.value.item_description?.trim()) {
    showToast("请输入物品特征描述", "warning");
    return false;
  }
  
  if (!verificationCode.value?.trim()) {
    showToast("请输入验证码", "warning");
    return false;
  }
  
  if (verificationCode.value !== generatedCode.value) {
    showToast("验证码输入错误，请重试", "error");
    generateCode();
    verificationCode.value = '';
    return false;
  }
  
  return true;
}

function resetForm() {
  formData.value = {
    item_id: props.item?.id || props.item?.item_id || '',
    username: "",
    applicant_name: "",
    applicant_phone: "",
    claim_reason: "",
    item_description: "",
    proof_images: []
  };
  previewImages.value = [];
  verificationCode.value = '';
  isFormModified.value = false;
  originalFormData = "";
}

function handleImageUpload(event) {
  const files = event.target.files;
  if (files.length > 0) {
    const remainingSlots = MAX_IMAGES - previewImages.value.length;
    const filesToAdd = Array.from(files).slice(0, remainingSlots);
    
    filesToAdd.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImages.value.push({
          file: file,
          preview: e.target.result
        });
      };
      reader.readAsDataURL(file);
    });
    
    event.target.value = '';
  }
}

function removeImage(index) {
  previewImages.value.splice(index, 1);
}

async function handleCancel() {
  if (isFormModified.value) {
    const choice = await window.showConfirm({title: '保存草稿', message: '表单内容已修改，是否保存草稿？', type: 'warning', confirmText: '保存'});
    if (choice) {
      saveDraft();
      showToast("草稿已保存，下次打开时可以恢复", "success");
    }
  }
  resetForm();
  emit('cancel');
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload);
});

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload);
});
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="claim-modal-overlay">
      <div class="claim-modal">
        <div class="modal-header">
          <h2>认领申请表单</h2>
          <button class="close-btn" @click="handleCancel">&times;</button>
        </div>
        
        <div class="modal-body">
          <div v-if="item" class="item-preview">
            <div class="preview-title">📦 认领物品: {{ item.title }}</div>
            <div class="preview-info">物品ID: {{ item.id || item.item_id }}</div>
          </div>
          <div v-else class="item-preview no-item">
            <div class="preview-title">📋 自主认领申请</div>
            <div class="preview-info">请填写以下信息提交认领申请</div>
          </div>
          
          <form @submit.prevent="submitClaim" class="claim-form">
            <div class="form-section">
              <h3>认领人信息</h3>
              <div class="form-group">
                <label for="username">用户名</label>
                <input 
                  id="username"
                  v-model="formData.username" 
                  type="text" 
                  placeholder="您的用户名"
                  maxlength="20"
                />
              </div>
              
              <div class="form-group">
                <label for="applicant_name">认领人姓名</label>
                <input 
                  id="applicant_name"
                  v-model="formData.applicant_name" 
                  type="text" 
                  placeholder="请输入您的真实姓名（选填）"
                  maxlength="20"
                />
              </div>
              
              <div class="form-group">
                <label for="applicant_phone">联系方式 *</label>
                <input 
                  id="applicant_phone"
                  v-model="formData.applicant_phone" 
                  type="text" 
                  placeholder="请输入电话/QQ/微信/邮箱"
                  maxlength="50"
                />
              </div>
            </div>
            
            <div class="form-section">
              <h3>认领信息</h3>
              <div class="form-group">
                <label for="claim_reason">认领理由 *</label>
                <textarea 
                  id="claim_reason"
                  v-model="formData.claim_reason" 
                  placeholder="请详细说明您认领该物品的理由，例如物品特征、遗失时间地点等"
                  rows="3"
                  maxlength="500"
                ></textarea>
                <div class="char-count">{{ formData.claim_reason.length }}/500</div>
              </div>
              
              <div class="form-group">
                <label for="item_description">物品特征描述 *</label>
                <textarea 
                  id="item_description"
                  v-model="formData.item_description" 
                  placeholder="请详细描述该物品的特征，如颜色、尺寸、品牌、特殊标记等"
                  rows="3"
                  maxlength="500"
                ></textarea>
                <div class="char-count">{{ formData.item_description.length }}/500</div>
              </div>
            </div>
            
            <div class="form-section">
              <h3>证明材料（选填）</h3>
              <div class="form-group">
                <label>上传证明图片</label>
                <div class="image-preview-grid">
                  <div 
                    v-for="(image, index) in previewImages" 
                    :key="index" 
                    class="preview-item"
                  >
                    <img :src="image.preview" :alt="'图片' + (index + 1)" class="preview-image" />
                    <button class="delete-btn" @click="removeImage(index)">✕</button>
                  </div>
                  <div 
                    v-if="previewImages.length < MAX_IMAGES" 
                    class="upload-area-wrapper"
                  >
                    <input 
                      type="file" 
                      accept="image/*"
                      @change="handleImageUpload"
                      class="file-input"
                    />
                    <div class="upload-area">
                      <div class="upload-icon">+</div>
                      <div class="upload-text">添加图片</div>
                      <div class="upload-hint">支持 JPG、PNG</div>
                    </div>
                  </div>
                </div>
                <div v-if="previewImages.length > 0" class="preview-count">
                  已选择 {{ previewImages.length }} / {{ MAX_IMAGES }} 张图片
                </div>
              </div>
            </div>
            
            <div class="form-section">
              <h3>验证码验证</h3>
              <div class="form-group">
                <label for="verification-code">验证码 *</label>
                <div class="verification-row">
                  <input 
                    id="verification-code"
                    v-model="verificationCode" 
                    type="text" 
                    placeholder="请输入验证码"
                    maxlength="5"
                  />
                  <div class="verification-code">{{ generatedCode }}</div>
                  <button type="button" class="btn-refresh" @click="generateCode">刷新</button>
                </div>
              </div>
            </div>
            
            <div class="form-notice">
              <h4>📌 注意事项</h4>
              <ul>
                <li>请确保填写的信息真实有效</li>
                <li>认领申请提交后需要等待管理员审核</li>
                <li>审核通过后，系统会通过短信或电话通知您</li>
              </ul>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="handleCancel" class="btn-cancel">取消</button>
              <button type="submit" :disabled="isSubmitting" class="btn-submit">
                {{ isSubmitting ? '提交中...' : '提交认领申请' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.claim-modal-overlay {
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
  padding: 20px;
  overflow-y: auto;
}

.claim-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: white;
  border-radius: 12px 12px 0 0;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: white;
  padding: 0;
  line-height: 1;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.close-btn:hover {
  opacity: 1;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  max-height: calc(90vh - 60px);
}

.item-preview {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #33ccff;
  margin-bottom: 20px;
}

.preview-title {
  font-weight: 600;
  color: #333;
  margin-bottom: 5px;
}

.preview-info {
  color: #666;
  font-size: 14px;
}

.item-preview.no-item {
  background: #e7f7ff;
  border-left-color: #0099cc;
}

.claim-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 15px;
}

.form-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #333;
  border-bottom: 2px solid #33ccff;
  padding-bottom: 6px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.form-group input, .form-group textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-group input:focus, .form-group textarea:focus {
  outline: none;
  border-color: #33ccff;
  box-shadow: 0 0 0 3px rgba(51, 204, 255, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.image-preview-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
  margin-top: 8px;
}

.preview-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #ddd;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.delete-btn {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}

.delete-btn:hover {
  background: rgba(231, 76, 60, 0.9);
}

.upload-area-wrapper {
  aspect-ratio: 1;
  position: relative;
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 10;
}

.upload-area {
  width: 100%;
  height: 100%;
  border: 2px dashed #ddd;
  border-radius: 6px;
  padding: 8px;
  text-align: center;
  transition: all 0.3s;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.upload-area:hover {
  border-color: #33ccff;
  background: #f0f9ff;
}

.upload-icon {
  font-size: 20px;
  margin-bottom: 4px;
  color: #999;
}

.upload-text {
  font-size: 11px;
  color: #666;
  margin-bottom: 2px;
}

.upload-hint {
  font-size: 9px;
  color: #999;
}

.preview-count {
  font-size: 13px;
  color: #666;
  background: #e7f7ff;
  padding: 6px 10px;
  border-radius: 4px;
  border-left: 3px solid #33ccff;
  margin-top: 10px;
}

.form-notice {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 15px;
}

.form-notice h4 {
  margin: 0 0 8px 0;
  color: #856404;
  font-size: 14px;
}

.form-notice ul {
  margin: 0;
  padding-left: 18px;
  color: #856404;
  font-size: 13px;
}

.form-notice li {
  margin-bottom: 4px;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.btn-cancel {
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel:hover {
  background: #5a6268;
}

.btn-submit {
  padding: 10px 20px;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(51, 204, 255, 0.3);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.verification-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.verification-code {
  padding: 10px 16px;
  background: #f5f5f5;
  font-size: 16px;
  font-weight: bold;
  letter-spacing: 4px;
  border-radius: 6px;
  color: #333;
  user-select: none;
  min-width: 80px;
  text-align: center;
}

.btn-refresh {
  padding: 10px 14px;
  background: #33ccff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.3s;
}

.btn-refresh:hover {
  background: #0099cc;
}

@media (max-width: 500px) {
  .image-preview-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .verification-row {
    flex-wrap: wrap;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .modal-body {
    padding: 15px;
  }
}
</style>