<script setup>
import { onMounted, ref } from "vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");

const username = ref("用户名");
const avatarUrl = ref("");
const item = ref(null);
const isLoading = ref(true);

const formData = ref({
  item_id: "",
  applicant_name: "",
  applicant_phone: "",
  applicant_email: "",
  claim_reason: "",
  item_description: "",
  proof_images: []
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
        
        if (item.value.type !== 1) {
          alert("只能认领拾到的物品");
          goBack();
          return;
        }
        
        if (userId && String(item.value.publisher_id) === String(userId)) {
          alert("不能认领自己发布的物品");
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

async function submitClaim() {
  if (!validateForm()) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    const formDataToSubmit = new FormData();
    formDataToSubmit.append('applicant_name', formData.value.applicant_name);
    formDataToSubmit.append('applicant_phone', formData.value.applicant_phone);
    formDataToSubmit.append('applicant_email', formData.value.applicant_email);
    formDataToSubmit.append('claim_reason', formData.value.claim_reason);
    formDataToSubmit.append('item_description', formData.value.item_description);
    formDataToSubmit.append('user_id', userId);
    if (formData.value.item_id) {
      formDataToSubmit.append('item_id', formData.value.item_id);
    }
    
    previewImages.value.forEach((image, index) => {
      formDataToSubmit.append(`proof_images[${index}]`, image.file);
    });
    
    const response = await fetch(`${API_BASE}/admin/claim-forms`, {
      method: "POST",
      body: formDataToSubmit,
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert("认领申请提交成功，请等待审核");
      goToProfile();
    } else {
      alert("提交失败: " + (data.message || "请重试"));
    }
  } catch (error) {
    console.error("提交认领申请失败:", error);
    alert("提交失败，请检查网络连接后重试");
  } finally {
    isSubmitting.value = false;
  }
}

function validateForm() {
  if (!formData.value.applicant_name.trim()) {
    alert("请输入认领人姓名");
    return false;
  }
  
  if (!formData.value.applicant_phone.trim()) {
    alert("请输入联系电话");
    return false;
  }
  
  const phoneRegex = /^1[3-9]\d{9}$/;
  if (!phoneRegex.test(formData.value.applicant_phone)) {
    alert("请输入正确的手机号码");
    return false;
  }
  
  if (!formData.value.claim_reason.trim()) {
    alert("请输入认领理由");
    return false;
  }
  
  if (!formData.value.item_description.trim()) {
    alert("请输入物品特征描述");
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

onMounted(() => {
  if (!userId) {
    alert("请先登录");
    window.location.href = "/login";
    return;
  }
  loadProfile();
  loadItemInfo();
});
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">认领申请</div>
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
          <h1>认领申请表单</h1>
          <div v-if="item" class="item-preview">
            <div class="preview-title">认领物品: {{ item.title }}</div>
            <div class="preview-info">物品ID: {{ item.item_id }}</div>
          </div>
          <div v-else class="item-preview no-item">
            <div class="preview-title">📋 自主认领申请</div>
            <div class="preview-info">请填写以下信息提交认领申请</div>
          </div>
        </div>
        
        <form @submit.prevent="submitClaim" class="claim-form">
          <div class="form-section">
            <h3>认领人信息</h3>
            <div class="form-group">
              <label for="applicant_name">认领人姓名 *</label>
              <input 
                id="applicant_name"
                v-model="formData.applicant_name" 
                type="text" 
                placeholder="请输入您的真实姓名"
                maxlength="20"
              />
            </div>
            
            <div class="form-group">
              <label for="applicant_phone">联系电话 *</label>
              <input 
                id="applicant_phone"
                v-model="formData.applicant_phone" 
                type="tel" 
                placeholder="请输入手机号码"
                maxlength="11"
              />
            </div>
            
            <div class="form-group">
              <label for="applicant_email">电子邮箱</label>
              <input 
                id="applicant_email"
                v-model="formData.applicant_email" 
                type="email" 
                placeholder="请输入邮箱地址（选填）"
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
                rows="4"
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
          
          <div class="form-notice">
            <h4>📌 注意事项</h4>
            <ul>
              <li>请确保填写的信息真实有效</li>
              <li>认领申请提交后需要等待管理员审核</li>
              <li>审核通过后，系统会通过短信或电话通知您</li>
              <li>如有疑问，请联系系统管理员</li>
            </ul>
          </div>
          
          <div class="form-actions">
            <button type="button" @click="goBack" class="btn-cancel">取消</button>
            <button type="submit" :disabled="isSubmitting" class="btn-submit">
              {{ isSubmitting ? '提交中...' : '提交认领申请' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
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
  border-top: 4px solid #33ccff;
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
}

.item-preview {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #33ccff;
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
  border-bottom: 2px solid #33ccff;
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
  border-color: #33ccff;
  box-shadow: 0 0 0 3px rgba(51, 204, 255, 0.1);
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
  border-color: #33ccff;
  background: #f0f9ff;
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
  background: #e7f7ff;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid #33ccff;
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
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
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
  box-shadow: 0 4px 12px rgba(51, 204, 255, 0.3);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
