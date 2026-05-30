<!-- 用户认证表单 -->
<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";

const showToast = window.showToast;

const props = defineProps({
  show: Boolean,
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
  identity: "",
  real_name: "",
  student_id: "",
  school: "",
  phone: "",
  email: "",
  id_card_front: null,
  id_card_back: null
});

const isFormModified = ref(false);
let originalFormData = "";

const verificationCode = ref('');
const generatedCode = ref('');

const isSubmitting = ref(false);
const previewImages = ref({
  front: null,
  back: null
});

const uploadFrontRef = ref(null);
const uploadBackRef = ref(null);

const identityFieldConfig = computed(() => {
  const configs = {
    student: {
      idLabel: '学号',
      idPlaceholder: '请输入学号',
      orgLabel: '学院/专业',
      orgPlaceholder: '请输入学院和专业名称',
      requiredId: true
    },
    teacher: {
      idLabel: '教师工号',
      idPlaceholder: '请输入教师工号',
      orgLabel: '学院/部门',
      orgPlaceholder: '请输入学院或部门名称',
      requiredId: true
    },
    maintenance: {
      idLabel: '维修员工号',
      idPlaceholder: '请输入维修员工号',
      orgLabel: '所属部门',
      orgPlaceholder: '请输入所属部门名称',
      requiredId: true
    },
    staff: {
      idLabel: '教职工号',
      idPlaceholder: '请输入教职工号',
      orgLabel: '部门/科室',
      orgPlaceholder: '请输入部门或科室名称',
      requiredId: true
    }
  };
  return configs[formData.value.identity] || null;
});

const DRAFT_KEY_PREFIX = 'verification_form_draft_';

function generateCode() {
  generatedCode.value = Math.random().toString().substring(2, 7);
}

function getDraftKey() {
  return `${DRAFT_KEY_PREFIX}${userId}`;
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
    if (confirm("检测到未完成的认证申请，是否恢复？")) {
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

async function submitVerification() {
  if (!validateForm()) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    const formDataToSubmit = new FormData();
    formDataToSubmit.append('user_id', userId);
    formDataToSubmit.append('identity', formData.value.identity);
    formDataToSubmit.append('real_name', formData.value.real_name);
    formDataToSubmit.append('student_id', formData.value.student_id);
    formDataToSubmit.append('school', formData.value.school);
    formDataToSubmit.append('phone', formData.value.phone);
    formDataToSubmit.append('email', formData.value.email);
    
    if (previewImages.value.front) {
      formDataToSubmit.append('id_card_front', previewImages.value.front.file);
    }
    if (previewImages.value.back) {
      formDataToSubmit.append('id_card_back', previewImages.value.back.file);
    }
    
    console.log('DEBUG: 准备提交认证表单');
    
    const response = await fetch(`${API_BASE}/my/verify`, {
      method: "POST",
      body: formDataToSubmit,
    });
    
    const data = await response.json();
    
    if (data.success) {
      clearDraft();
      isFormModified.value = false;
      showToast("认证申请提交成功，等待审核", "success");
      emit('success');
    } else {
      showToast("提交失败: " + (data.message || "请重试"), "error");
    }
  } catch (error) {
    console.error("提交认证申请失败:", error);
    showToast("提交失败，请检查网络连接后重试", "error");
  } finally {
    isSubmitting.value = false;
  }
}

function validateForm() {
  if (!formData.value.identity?.trim()) {
    showToast("请选择身份", "warning");
    return false;
  }
  
  if (!formData.value.real_name?.trim()) {
    showToast("请输入真实姓名", "warning");
    return false;
  }
  
  const config = identityFieldConfig.value;
  if (config && config.requiredId && !formData.value.student_id?.trim()) {
    showToast(`请输入${config.idLabel}`, "warning");
    return false;
  }
  
  if (!formData.value.phone?.trim() && !formData.value.email?.trim()) {
    showToast("请输入手机号或邮箱", "warning");
    return false;
  }
  
  if (!previewImages.value.front) {
    showToast("请上传证件正面照片", "warning");
    return false;
  }
  
  if (!previewImages.value.back) {
    showToast("请上传证件反面照片", "warning");
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
    real_name: "",
    student_id: "",
    school: "",
    phone: "",
    email: "",
    id_card_front: null,
    id_card_back: null
  };
  previewImages.value = {
    front: null,
    back: null
  };
  verificationCode.value = '';
  isFormModified.value = false;
  originalFormData = "";
}

function handleImageUpload(event, type) {
  const files = event.target.files;
  if (files.length > 0) {
    const file = files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImages.value[type] = {
        file: file,
        preview: e.target.result
      };
    };
    reader.readAsDataURL(file);
    
    event.target.value = '';
  }
}

function triggerUpload(type) {
  if (type === 'front' && uploadFrontRef.value) {
    uploadFrontRef.value.click();
  } else if (type === 'back' && uploadBackRef.value) {
    uploadBackRef.value.click();
  }
}

function removeImage(type) {
  previewImages.value[type] = null;
}

function handleCancel() {
  if (isFormModified.value) {
    const choice = confirm("表单内容已修改，是否保存草稿？");
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
    <div v-if="show" class="verification-modal-overlay">
      <div class="verification-modal">
        <div class="modal-header">
          <h2>用户认证</h2>
          <button class="close-btn" @click="handleCancel">&times;</button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="submitVerification" class="verification-form">
            <div class="form-section">
              <div class="section-header">
                <h3>👤 基本信息</h3>
                <div class="identity-select-wrapper">
                  <label class="identity-label">身份选择:</label>
                  <select v-model="formData.identity" class="identity-select">
                    <option value="">请选择身份</option>
                    <option value="student">学生</option>
                    <option value="teacher">教师</option>
                    <option value="maintenance">维修工</option>
                    <option value="staff">教职工</option>
                  </select>
                </div>
              </div>
              <div class="form-group">
                <label for="real_name">真实姓名 *</label>
                <input 
                  id="real_name"
                  v-model="formData.real_name" 
                  type="text" 
                  placeholder="请输入您的真实姓名"
                  maxlength="20"
                />
              </div>
              
              <div v-if="identityFieldConfig" class="form-group">
                <label for="student_id">{{ identityFieldConfig.idLabel }}<span v-if="identityFieldConfig.requiredId"> *</span></label>
                <input 
                  id="student_id"
                  v-model="formData.student_id" 
                  type="text" 
                  :placeholder="identityFieldConfig.idPlaceholder"
                  maxlength="20"
                />
              </div>
              
              <div v-if="identityFieldConfig" class="form-group">
                <label for="school">{{ identityFieldConfig.orgLabel }}</label>
                <input 
                  id="school"
                  v-model="formData.school" 
                  type="text" 
                  :placeholder="identityFieldConfig.orgPlaceholder"
                  maxlength="100"
                />
              </div>
            </div>
            
            <div class="form-section">
              <h3>📞 联系方式</h3>
              <div class="form-group">
                <label for="phone">手机号码</label>
                <input 
                  id="phone"
                  v-model="formData.phone" 
                  type="tel" 
                  placeholder="请输入手机号码"
                  maxlength="11"
                />
              </div>
              
              <div class="form-group">
                <label for="email">电子邮箱</label>
                <input 
                  id="email"
                  v-model="formData.email" 
                  type="email" 
                  placeholder="请输入电子邮箱"
                  maxlength="100"
                />
                <div class="hint">手机号和邮箱至少填写一项</div>
              </div>
            </div>
            
            <div class="form-section">
              <h3>🖼️ 证件照片</h3>
              <div class="form-group">
                <label>证件正面 *</label>
                <div class="image-upload-wrapper">
                  <div v-if="previewImages.front" class="image-preview-box">
                    <img :src="previewImages.front.preview" alt="证件正面" class="preview-img" />
                    <button class="remove-img-btn" @click="removeImage('front')">✕</button>
                  </div>
                  <div v-else class="upload-box" @click="triggerUpload('front')">
                    <input 
                      ref="uploadFrontRef"
                      type="file" 
                      accept="image/*"
                      @change="handleImageUpload($event, 'front')"
                      class="hidden-input"
                    />
                    <div class="upload-icon">📷</div>
                    <div class="upload-text">点击上传证件正面</div>
                  </div>
                </div>
              </div>
              
              <div class="form-group">
                <label>证件反面 *</label>
                <div class="image-upload-wrapper">
                  <div v-if="previewImages.back" class="image-preview-box">
                    <img :src="previewImages.back.preview" alt="证件反面" class="preview-img" />
                    <button class="remove-img-btn" @click="removeImage('back')">✕</button>
                  </div>
                  <div v-else class="upload-box" @click="triggerUpload('back')">
                    <input 
                      ref="uploadBackRef"
                      type="file" 
                      accept="image/*"
                      @change="handleImageUpload($event, 'back')"
                      class="hidden-input"
                    />
                    <div class="upload-icon">📷</div>
                    <div class="upload-text">点击上传证件反面</div>
                  </div>
                </div>
              </div>
              
              <div class="upload-hint">
                💡 请确保证件照片清晰可见，无遮挡
              </div>
            </div>
            
            <div class="form-section">
              <h3>🔐 验证码验证</h3>
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
              <h4>📌 认证须知</h4>
              <ul>
                <li>请确保提交的信息真实有效，我们将严格保密您的个人信息</li>
                <li>认证申请提交后需要等待管理员审核，通常在1-3个工作日内完成</li>
                <li>审核通过后，您将获得更多功能权限</li>
                <li>如信息有误，请重新提交认证申请</li>
              </ul>
            </div>
            
            <div class="form-actions">
              <button type="button" @click="handleCancel" class="btn-cancel">取消</button>
              <button type="submit" :disabled="isSubmitting" class="btn-submit">
                {{ isSubmitting ? '提交中...' : '提交认证申请' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.verification-modal-overlay {
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

.verification-modal {
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

.form-section {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.identity-select-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.identity-label {
  font-size: 14px;
  font-weight: 500;
  color: #666;
}

.identity-select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  color: #333;
  background: white;
  cursor: pointer;
  transition: border-color 0.3s;
}

.identity-select:focus {
  outline: none;
  border-color: #33ccff;
  box-shadow: 0 0 0 3px rgba(51, 204, 255, 0.1);
}

.identity-select option {
  padding: 8px;
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

.form-group input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #33ccff;
  box-shadow: 0 0 0 3px rgba(51, 204, 255, 0.1);
}

.form-group .hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.image-upload-wrapper {
  margin-top: 8px;
}

.image-preview-box {
  position: relative;
  width: 100%;
  max-width: 200px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid #33ccff;
}

.preview-img {
  width: 100%;
  height: auto;
  display: block;
}

.remove-img-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: rgba(231, 76, 60, 0.9);
  color: white;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}

.remove-img-btn:hover {
  background: rgba(231, 76, 60, 1);
}

.upload-box {
  width: 100%;
  max-width: 200px;
  padding: 25px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
}

.upload-box:hover {
  border-color: #33ccff;
  background: #f0f9ff;
}

.upload-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.upload-text {
  font-size: 14px;
  color: #666;
}

.hidden-input {
  display: none;
}

.upload-hint {
  font-size: 12px;
  color: #666;
  background: #e7f7ff;
  padding: 8px 12px;
  border-radius: 4px;
  margin-top: 10px;
  border-left: 3px solid #33ccff;
}

.form-notice {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
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
  padding: 10px 24px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel:hover {
  background: #5a6268;
}

.btn-submit {
  padding: 10px 24px;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: white;
  border: none;
  border-radius: 8px;
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
  .verification-container {
    padding: 15px;
  }
  
  .verification-form {
    padding: 15px;
  }
  
  .verification-row {
    flex-wrap: wrap;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .btn-cancel, .btn-submit {
    width: 100%;
  }
}
</style>
