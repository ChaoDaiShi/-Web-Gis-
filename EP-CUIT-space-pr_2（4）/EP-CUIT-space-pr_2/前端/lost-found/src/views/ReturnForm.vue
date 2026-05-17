<script setup>
import { onMounted, onUnmounted, ref, watch } from "vue";
import { onBeforeRouteLeave } from "vue-router";
import MarkerDetailModal from "../components/MarkerDetailModal.vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");

const username = ref("用户名");
const avatarUrl = ref("");
const item = ref(null);
const isLoading = ref(true);
const showDetailModal = ref(false);

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

function generateCode() {
  generatedCode.value = Math.random().toString().substring(2, 7);
}

function saveDraft() {
  localStorage.setItem('returnFormDraft', JSON.stringify(formData.value));
  localStorage.setItem('returnFormItemId', formData.value.item_id);
}

function clearDraft() {
  localStorage.removeItem('returnFormDraft');
  localStorage.removeItem('returnFormItemId');
}

function checkAndRestoreDraft() {
  const draft = localStorage.getItem('returnFormDraft');
  const draftItemId = localStorage.getItem('returnFormItemId');
  const currentItemId = new URLSearchParams(window.location.search).get('id');
  
  if (draft && draftItemId === currentItemId) {
    if (confirm("检测到未完成的归还申请，是否恢复？")) {
      const draftData = JSON.parse(draft);
      Object.assign(formData.value, draftData);
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

onBeforeRouteLeave((to, from, next) => {
  if (isFormModified.value) {
    const choice = confirm("表单内容已修改，是否保存后再离开？\n\n确定 - 保存并离开\n取消 - 不保存直接离开");
    if (choice) {
      saveDraft();
      next();
    } else {
      next();
    }
  } else {
    next();
  }
});

const isSubmitting = ref(false);
const MAX_IMAGES = 5;
const previewImages = ref([]);

async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile?user_id=${userId}`);
    const data = await res.json();
    if (data.success && data.data) {
      const user = data.data;
      username.value = user.username || "用户名";
      avatarUrl.value = user.avatar ? `http://127.0.0.1:5000${user.avatar}` : "";
      formData.value.username = user.username || "";
    }
  } catch (e) {
    console.error(e);
  }
}

async function loadItemInfo() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const itemId = urlParams.get('id');
    
    if (itemId) {
      formData.value.item_id = itemId;
      
      const res = await fetch(`${API_BASE}/lost-items/${itemId}`);
      const data = await res.json();
      
      if (data.success) {
        item.value = data.data;
        
        if (item.value.type !== 0) {
          alert("只能归还丢失的物品");
          goBack();
          return;
        }
        
        if (userId && String(item.value.publisher_id) === String(userId)) {
          alert("不能归还自己发布的物品");
          goBack();
          return;
        }
      } else {
        alert("获取物品信息失败");
      }
    }
  } catch (error) {
    console.error("加载物品信息失败:", error);
  } finally {
    isLoading.value = false;
  }
}

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
    
    const data = await response.json();
    
    if (data.success) {
      alert("归还申请提交成功，请等待审核");
      clearDraft();
      isFormModified.value = false;
      goToProfile();
    } else {
      alert("提交失败: " + (data.message || "请重试"));
    }
  } catch (error) {
    console.error("提交归还申请失败:", error);
    alert("提交失败，请检查网络连接后重试");
  } finally {
    isSubmitting.value = false;
  }
}

function validateForm() {
  if (!formData.value.applicant_phone.trim()) {
    alert("请输入联系方式（电话/QQ/微信/邮箱）");
    return false;
  }
  
  if (!formData.value.return_reason.trim()) {
    alert("请输入归还理由");
    return false;
  }
  
  if (!formData.value.item_description.trim()) {
    alert("请输入物品特征描述");
    return false;
  }
  
  if (!verificationCode.value.trim()) {
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

function goBack() {
  window.location.href = "/home";
}

function goToProfile() {
  window.location.href = "/profile";
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

function openItemDetail() {
  showDetailModal.value = true;
}

function closeDetailModal() {
  showDetailModal.value = false;
}

onMounted(() => {
  if (!userId) {
    alert("请先登录");
    window.location.href = "/login";
    return;
  }
  loadProfile();
  loadItemInfo();
  generateCode();
  
  setTimeout(() => {
    originalFormData = JSON.stringify(formData.value);
    checkAndRestoreDraft();
  }, 500);
  
  window.addEventListener('beforeunload', handleBeforeUnload);
});

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload);
});

watch(formData, (newVal) => {
  if (originalFormData) {
    isFormModified.value = JSON.stringify(newVal) !== originalFormData;
  }
}, { deep: true });
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">归还申请</div>
      <div class="topbar-user">
        <img v-if="avatarUrl" :src="avatarUrl" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;" />
        <span v-else>{{ username.charAt(0) || '管' }}</span>
      </div>
    </div>
    
    <div class="container">
      <div v-if="isLoading" class="loading">
        <div class="loading-spinner"></div>
        <div>加载中...</div>
      </div>
      
      <div v-else class="form-content">
        <div class="form-header">
          <h1>归还申请表单</h1>
          <div v-if="item" class="item-preview clickable" @click="openItemDetail">
            <div class="preview-title">归还物品: {{ item.title }}</div>
            <div class="preview-info">物品ID: {{ item.item_id }}</div>
            <div class="preview-hint">点击查看详情</div>
          </div>
          <div v-else class="item-preview no-item">
            <div class="preview-title">📋 自主归还申请</div>
            <div class="preview-info">请填写以下信息提交归还申请</div>
          </div>
        </div>
        
        <form @submit.prevent="submitReturn" class="claim-form">
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
                maxlength="11"
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
                rows="4"
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
                rows="4"
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
            <button type="button" @click="goBack" class="btn-cancel">取消</button>
            <button type="submit" :disabled="isSubmitting" class="btn-submit">
              {{ isSubmitting ? '提交中...' : '提交归还申请' }}
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <MarkerDetailModal
      :show="showDetailModal"
      :marker="item"
      :disableActions="true"
      @close="closeDetailModal"
    />
  </div>
</template>

<style scoped>
.topbar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 1000;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.topbar-title {
  font-size: clamp(18px, 2.5vw, 28px);
  color: #333;
  font-weight: 500;
}

.topbar-user {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #111827;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  overflow: hidden;
}

.container {
  max-width: 800px;
  margin: 80px auto 20px;
  padding: 0 20px 40px;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
  box-sizing: border-box;
}

html {
  overflow-y: auto;
  scroll-behavior: smooth;
}

body {
  overflow-y: auto;
}

.loading {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #28a745;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.form-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  min-height: calc(100vh - 160px);
}

.form-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.form-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0 0 15px 0;
  text-align: center;
}

.item-preview {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #28a745;
}

.item-preview.clickable {
  cursor: pointer;
  transition: all 0.3s ease;
}

.item-preview.clickable:hover {
  background: #e8f5e9;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
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

.preview-hint {
  color: #28a745;
  font-size: 12px;
  margin-top: 8px;
  text-align: right;
}

.item-preview.no-item {
  background: #e8f5e9;
  border-left-color: #20c997;
}

.claim-form {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.form-section {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 20px;
}

.form-section h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
  border-bottom: 2px solid #28a745;
  padding-bottom: 8px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.form-group input, .form-group textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus, .form-group textarea:focus {
  outline: none;
  border-color: #28a745;
  box-shadow: 0 0 0 3px rgba(40, 167, 69, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.image-preview-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  margin-top: 10px;
}

.preview-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
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
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 14px;
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
  border-radius: 8px;
  padding: 10px;
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
  font-size: 24px;
  margin-bottom: 5px;
  color: #999;
}

.upload-text {
  font-size: 12px;
  color: #666;
  margin-bottom: 2px;
}

.upload-hint {
  font-size: 10px;
  color: #999;
}

.preview-count {
  font-size: 14px;
  color: #666;
  background: #e8f5e9;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid #28a745;
}

.form-notice {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 20px;
}

.form-notice h4 {
  margin: 0 0 10px 0;
  color: #856404;
}

.form-notice ul {
  margin: 0;
  padding-left: 20px;
  color: #856404;
}

.form-notice li {
  margin-bottom: 5px;
}

.form-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn-cancel {
  padding: 12px 24px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel:hover {
  background: #5a6268;
}

.btn-submit {
  padding: 12px 24px;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
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
  gap: 12px;
}

.verification-code {
  padding: 12px 20px;
  background: #f5f5f5;
  font-size: 18px;
  font-weight: bold;
  letter-spacing: 6px;
  border-radius: 8px;
  color: #333;
  user-select: none;
  min-width: 100px;
  text-align: center;
}

.btn-refresh {
  padding: 12px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.btn-refresh:hover {
  background: #218838;
}

@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }
  
  .form-section {
    padding: 15px;
  }
}
</style>