<script setup>
import { onMounted, ref } from "vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");

const item = ref(null);
const formData = ref({
  item_id: "",
  applicant_name: "",
  applicant_phone: "",
  applicant_email: "",
  claim_reason: "",
  item_description: "",
  proof_images: []
});

const isLoading = ref(true);
const isSubmitting = ref(false);

async function loadItemInfo() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const itemId = urlParams.get('id');
    
    if (!itemId) {
      alert("物品ID不存在");
      goBack();
      return;
    }
    
    formData.value.item_id = itemId;
    
    const res = await fetch(`${API_BASE}/lost-items/${itemId}`);
    const data = await res.json();
    
    if (data.success) {
      item.value = data.data;
      
      if (item.value.status !== 0) {
        alert("该物品无法认领");
        goBack();
        return;
      }
    } else {
      alert("获取物品信息失败");
      goBack();
    }
  } catch (error) {
    console.error("加载物品信息失败:", error);
    alert("加载失败，请重试");
    goBack();
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
    const response = await fetch(`${API_BASE}/claims`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...formData.value,
        user_id: userId
      }),
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
  if (item.value) {
    window.location.href = `/lost-item-detail?id=${item.value.item_id}`;
  } else {
    window.location.href = "/lost-items";
  }
}

function goToProfile() {
  window.location.href = "/profile";
}

function handleImageUpload(event) {
  const files = event.target.files;
  if (files.length > 0) {
    formData.value.proof_images = Array.from(files);
  }
}

onMounted(() => {
  if (!userId) {
    alert("请先登录");
    window.location.href = "/login";
    return;
  }
  loadItemInfo();
});
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">认领申请</div>
      <div class="topbar-user">管</div>
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
            <div class="preview-info">拾取地点: {{ item.location }}</div>
            <div class="preview-info">拾取时间: {{ item.pickup_time }}</div>
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
              <div class="file-upload">
                <input 
                  type="file" 
                  multiple 
                  accept="image/*"
                  @change="handleImageUpload"
                  class="file-input"
                />
                <div class="upload-area">
                  <div class="upload-icon">📁</div>
                  <div class="upload-text">点击选择图片或拖拽文件到此处</div>
                  <div class="upload-hint">支持 JPG、PNG 格式，最多 5 张</div>
                </div>
              </div>
              <div v-if="formData.proof_images.length > 0" class="image-preview">
                <div class="preview-count">已选择 {{ formData.proof_images.length }} 张图片</div>
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
.container {
  max-width: 800px;
  margin: 80px auto 20px;
  padding: 0 20px;
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

.file-upload {
  position: relative;
}

.file-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  transition: all 0.3s;
  background: #fafafa;
}

.upload-area:hover {
  border-color: #33ccff;
  background: #f0f9ff;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 10px;
  color: #999;
}

.upload-text {
  font-size: 16px;
  color: #666;
  margin-bottom: 5px;
}

.upload-hint {
  font-size: 12px;
  color: #999;
}

.image-preview {
  margin-top: 10px;
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