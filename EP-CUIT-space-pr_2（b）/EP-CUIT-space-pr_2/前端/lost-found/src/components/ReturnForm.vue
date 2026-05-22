<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  item: {
    type: Object,
    default: null
  },
  username: {
    type: String,
    default: ""
  }
});

const emit = defineEmits(['close', 'success']);

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");

const formData = ref({
  item_id: "",
  username: "",
  applicant_name: "",
  applicant_phone: "",
  return_reason: "",
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

const DRAFT_KEY_PREFIX = 'return_form_draft_';

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

function checkAndRestoreDraft() {
  const draft = loadDraft();
  if (draft) {
    if (confirm("检测到未完成的归还申请，是否恢复？")) {
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
    const storedUsername = localStorage.getItem('username') || '';
    formData.value.username = props.username || storedUsername;
    
    if (props.item) {
      formData.value.item_id = props.item.id || props.item.item_id;
    }
    
    generateCode();
    
    setTimeout(() => {
      originalFormData = JSON.stringify(formData.value);
      checkAndRestoreDraft();
    }, 100);
  }
});

watch(formData, (newVal) => {
  if (originalFormData) {
    isFormModified.value = JSON.stringify(newVal) !== originalFormData;
  }
}, { deep: true });

async function submitReturn() {
  if (!validateForm()) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    const formDataToSubmit = new FormData();
    formDataToSubmit.append('username', formData.value.username);
    formDataToSubmit.append('applicant_name', formData.value.applicant_name);
    formDataToSubmit.append('applicant_phone', formData.value.applicant_phone);
    formDataToSubmit.append('return_reason', formData.value.return_reason);
    formDataToSubmit.append('item_description', formData.value.item_description);
    formDataToSubmit.append('user_id', userId);
    if (formData.value.item_id) {
      formDataToSubmit.append('item_id', formData.value.item_id);
    }
    
    previewImages.value.forEach((image, index) => {
      formDataToSubmit.append(`proof_images[${index}]`, image.file);
    });
    
    const response = await fetch(`${API_BASE}/admin/return-forms`, {
      method: "POST",
      body: formDataToSubmit,
    });
    
    const result = await response.json();
    
    if (result.success) {
      clearDraft();
      isFormModified.value = false;
      alert("归还申请提交成功，请等待审核");
      emit('success');
      handleCancel();
    } else {
      alert("提交失败: " + (result.message || "请重试"));
    }
  } catch (error) {
    console.error("提交归还申请失败:", error);
    alert("提交失败，请检查网络连接后重试");
  } finally {
    isSubmitting.value = false;
  }
}

function validateForm() {
  if (!formData.value.applicant_phone?.trim()) {
    alert("请输入联系方式（电话/QQ/微信/邮箱）");
    return false;
  }
  
  if (!formData.value.return_reason?.trim()) {
    alert("请输入归还理由");
    return false;
  }
  
  if (!formData.value.item_description?.trim()) {
    alert("请输入物品特征描述");
    return false;
  }
  
  if (!verificationCode.value?.trim()) {
    alert("请输入验证码");
    return false;
  }
  
  if (verificationCode.value !== generatedCode.value) {
    alert("验证码输入错误，请重试");
    generateCode();
    verificationCode.value = '';
    return false;
  }
  
  return true;
}

function resetForm() {
  formData.value = {
    item_id: "",
    username: "",
    applicant_name: "",
    applicant_phone: "",
    return_reason: "",
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

function handleCancel() {
  if (isFormModified.value) {
    const choice = confirm("表单内容已修改，是否保存草稿？");
    if (choice) {
      saveDraft();
      alert("草稿已保存，下次打开时可以恢复");
    }
  }
  resetForm();
  emit('close');
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
    <div v-if="show" class="return-modal-overlay">
      <div class="return-modal">
        <div class="modal-header">
          <h2>归还申请表单</h2>
          <button class="close-btn" @click="handleCancel">✕</button>
        </div>
        
        <div class="modal-body">
          <div v-if="item" class="item-preview">
            <div class="preview-title">归还物品: {{ item.title }}</div>
            <div class="preview-info">物品ID: {{ item.id || item.item_id }}</div>
          </div>
          <div v-else class="item-preview no-item">
            <div class="preview-title">📋 自主归还申请</div>
            <div class="preview-info">请填写以下信息提交归还申请</div>
          </div>
          
          <form @submit.prevent="submitReturn" class="return-form">
            <div class="form-section">
              <h3>归还人信息</h3>
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
                <label for="applicant_name">归还人姓名</label>
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
                  type="tel" 
                  placeholder="请输入电话/QQ/微信/邮箱"
                  maxlength="50"
                />
              </div>
            </div>
            
            <div class="form-section">
              <h3>归还信息</h3>
              <div class="form-group">
                <label for="return_reason">归还理由 *</label>
                <textarea 
                  id="return_reason"
                  v-model="formData.return_reason" 
                  placeholder="请详细说明您归还该物品的理由，例如发现物品的时间地点等"
                  rows="3"
                  maxlength="500"
                ></textarea>
                <div class="char-count">{{ formData.return_reason.length }}/500</div>
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
                <li>归还申请提交后需要等待管理员审核</li>
                <li>审核通过后，系统会通过短信或电话通知您</li>
                <li>如有疑问，请联系系统管理员</li>
              </ul>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="handleCancel" class="btn-cancel">取消</button>
              <button type="submit" :disabled="isSubmitting" class="btn-submit">
                {{ isSubmitting ? '提交中...' : '提交归还申请' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.return-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  box-sizing: border-box;
}

.return-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  padding: 20px 24px;
  border-radius: 12px 12px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 20px;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.8);
  color: #333;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.close-btn:hover {
  background: white;
  transform: rotate(90deg);
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  max-height: calc(90vh - 80px);
}

.item-preview {
  background: #e8f5e9;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #28a745;
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

.return-form {
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
  border-bottom: 2px solid #28a745;
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
  border-color: #28a745;
  box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1);
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
  border-color: #28a745;
  background: #e8f5e9;
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
  background: #e8f5e9;
  padding: 6px 10px;
  border-radius: 4px;
  border-left: 3px solid #28a745;
  margin-top: 8px;
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
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
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
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
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
  padding: 10px 12px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.3s;
}

.btn-refresh:hover {
  background: #218838;
}

@media (max-width: 768px) {
  .return-modal {
    max-height: 95vh;
  }
  
  .modal-body {
    padding: 15px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .image-preview-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .verification-row {
    flex-wrap: wrap;
  }
}
</style>