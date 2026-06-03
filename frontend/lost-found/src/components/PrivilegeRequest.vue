<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const showToast = window.showToast;

const reason = ref('');
const submitting = ref(false);
const requests = ref([]);
const loading = ref(false);
const permissions = ref([]);
const secondaryAdmins = ref([]);
const selectedPermissions = ref([]);
const selectedAdminId = ref(null);

const adminRole = computed(() => localStorage.getItem('admin_role') || 'secondary_admin');
const isAdmin = computed(() => localStorage.getItem('is_admin') === '1');
const adminToken = computed(() => localStorage.getItem('admin_token') || 'admin_token');

const permissionCategories = computed(() => {
  const categories = {};
  permissions.value.forEach(p => {
    if (!categories[p.category]) {
      categories[p.category] = [];
    }
    categories[p.category].push(p);
  });
  return categories;
});

async function fetchPermissions() {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/admin/permissions', {
      headers: {
        'Authorization': `Bearer ${adminToken.value}`
      }
    });
    const data = await res.json();
    if (data.code === 200) {
      permissions.value = data.data;
    }
  } catch (err) {
    console.error('获取权限列表失败:', err);
  }
}

async function fetchSecondaryAdmins() {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/admin/secondary-admins', {
      headers: {
        'Authorization': `Bearer ${adminToken.value}`
      }
    });
    const data = await res.json();
    if (data.code === 200) {
      secondaryAdmins.value = data.data;
    }
  } catch (err) {
    console.error('获取二级管理员列表失败:', err);
  }
}

async function fetchMyRequests() {
  loading.value = true;
  try {
    const res = await fetch('http://127.0.0.1:5000/api/admin/privilege-requests', {
      headers: {
        'Authorization': `Bearer ${adminToken.value}`
      }
    });
    const data = await res.json();
    if (data.code === 200) {
      requests.value = data.data;
    } else {
      showToast(data.message || '获取申请列表失败', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('网络错误', 'error');
  } finally {
    loading.value = false;
  }
}

async function submitRequest() {
  if (!reason.value.trim()) {
    showToast('请填写申请理由', 'error');
    return;
  }
  
  if (selectedPermissions.value.length === 0) {
    showToast('请至少选择一个权限', 'error');
    return;
  }
  
  if (!selectedAdminId.value) {
    showToast('请选择目标管理员', 'error');
    return;
  }
  
  submitting.value = true;
  try {
    const res = await fetch('http://127.0.0.1:5000/api/admin/privilege-requests', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken.value}`
      },
      body: JSON.stringify({
        reason: reason.value.trim(),
        requested_permissions: selectedPermissions.value,
        target_admin_id: selectedAdminId.value
      })
    });
    const data = await res.json();
    if (data.code === 200) {
      showToast('提权申请已提交', 'success');
      reason.value = '';
      selectedPermissions.value = [];
      selectedAdminId.value = null;
      fetchMyRequests();
    } else {
      showToast(data.message || '提交失败', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('网络错误', 'error');
  } finally {
    submitting.value = false;
  }
}

function togglePermission(permissionKey) {
  const index = selectedPermissions.value.indexOf(permissionKey);
  if (index > -1) {
    selectedPermissions.value.splice(index, 1);
  } else {
    selectedPermissions.value.push(permissionKey);
  }
}

function getStatusText(status) {
  const statusMap = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝'
  };
  return statusMap[status] || status;
}

function getStatusClass(status) {
  const classMap = {
    'pending': 'status-pending',
    'approved': 'status-approved',
    'rejected': 'status-rejected'
  };
  return classMap[status] || '';
}

function getPermissionName(key) {
  const perm = permissions.value.find(p => p.permission_key === key);
  return perm ? perm.permission_name : key;
}

function goBack() {
  router.push('/admin');
}

onMounted(() => {
  if (!isAdmin.value) {
    router.push('/login');
    return;
  }
  fetchPermissions();
  fetchSecondaryAdmins();
  fetchMyRequests();
});
</script>

<template>
  <div class="privilege-request-page">
    <div class="header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <h1>申请权限</h1>
    </div>
    
    <div class="content">
      <div class="role-info">
        <div class="role-badge" :class="adminRole === 'super_admin' ? 'super' : 'secondary'">
          当前角色：{{ adminRole === 'super_admin' ? '超级管理员' : '二级管理员' }}
        </div>
      </div>
      
      <div v-if="adminRole === 'super_admin'" class="already-super">
        <p>您已经是超级管理员，拥有所有权限。</p>
      </div>
      
      <div v-else class="request-form">
        <h2>提交权限申请</h2>
        
        <div class="form-section">
          <h3>选择目标管理员</h3>
          <p class="section-desc">请选择您要向哪位二级管理员申请权限</p>
          <div class="admin-list">
            <div 
              v-for="admin in secondaryAdmins" 
              :key="admin.admin_id"
              class="admin-card"
              :class="{ selected: selectedAdminId === admin.admin_id }"
              @click="selectedAdminId = admin.admin_id"
            >
              <div class="admin-name">{{ admin.username }}</div>
              <div class="admin-department" v-if="admin.department">{{ admin.department }}</div>
              <div class="admin-permissions" v-if="admin.permissions && admin.permissions.length > 0">
                <span class="perm-tag" v-for="perm in admin.permissions.slice(0, 3)" :key="perm">
                  {{ getPermissionName(perm) }}
                </span>
                <span v-if="admin.permissions.length > 3" class="perm-more">
                  +{{ admin.permissions.length - 3 }}
                </span>
              </div>
              <div class="admin-permissions" v-else>
                <span class="no-perm">暂无权限</span>
              </div>
            </div>
          </div>
          <div v-if="secondaryAdmins.length === 0" class="empty-admins">
            暂无可选的二级管理员，请联系超级管理员创建
          </div>
        </div>
        
        <div class="form-section">
          <h3>选择申请的权限</h3>
          <p class="section-desc">请选择您需要申请的权限（可多选）</p>
          <div class="permission-categories">
            <div v-for="(perms, category) in permissionCategories" :key="category" class="category-group">
              <div class="category-title">{{ category }}</div>
              <div class="permission-list">
                <div 
                  v-for="perm in perms" 
                  :key="perm.permission_key"
                  class="permission-item"
                  :class="{ selected: selectedPermissions.includes(perm.permission_key) }"
                  @click="togglePermission(perm.permission_key)"
                >
                  <div class="perm-checkbox">
                    <span v-if="selectedPermissions.includes(perm.permission_key)">✓</span>
                  </div>
                  <div class="perm-info">
                    <div class="perm-name">{{ perm.permission_name }}</div>
                    <div class="perm-desc">{{ perm.description }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label>申请理由</label>
          <textarea 
            v-model="reason" 
            placeholder="请详细说明您申请这些权限的理由..."
            rows="5"
          ></textarea>
        </div>
        
        <button 
          class="submit-btn" 
          @click="submitRequest" 
          :disabled="submitting"
        >
          {{ submitting ? '提交中...' : '提交申请' }}
        </button>
      </div>
      
      <div class="request-history">
        <h2>我的申请记录</h2>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="requests.length === 0" class="empty">暂无申请记录</div>
        <div v-else class="request-list">
          <div 
            v-for="req in requests" 
            :key="req.request_id" 
            class="request-item"
          >
            <div class="request-header">
              <span class="request-id">申请 #{{ req.request_id }}</span>
              <span class="request-status" :class="getStatusClass(req.status)">
                {{ getStatusText(req.status) }}
              </span>
            </div>
            <div class="request-body">
              <div class="request-target" v-if="req.target_admin_name">
                <strong>申请对象：</strong>
                {{ req.target_admin_name }}
                <span v-if="req.target_admin_department">（{{ req.target_admin_department }}）</span>
              </div>
              <div class="request-permissions" v-if="req.requested_permissions && req.requested_permissions.length > 0">
                <strong>申请权限：</strong>
                <div class="perm-tags">
                  <span class="perm-tag" v-for="perm in req.requested_permissions" :key="perm">
                    {{ getPermissionName(perm) }}
                  </span>
                </div>
              </div>
              <div class="request-reason">
                <strong>申请理由：</strong>
                <p>{{ req.reason }}</p>
              </div>
              <div class="request-time">
                <strong>提交时间：</strong>{{ req.create_time }}
              </div>
              <div v-if="req.status !== 'pending'" class="request-review">
                <div><strong>审核人：</strong>{{ req.reviewer_name || '未知' }}</div>
                <div><strong>审核时间：</strong>{{ req.review_time }}</div>
                <div v-if="req.review_note"><strong>审核备注：</strong>{{ req.review_note }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.privilege-request-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.back-btn {
  padding: 10px 20px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #f0f0f0;
}

.header h1 {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.content {
  max-width: 900px;
  margin: 0 auto;
}

.role-info {
  margin-bottom: 30px;
}

.role-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.role-badge.super {
  background: #fef3c7;
  color: #92400e;
}

.role-badge.secondary {
  background: #dbeafe;
  color: #1e40af;
}

.already-super {
  background: #fff;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  color: #666;
}

.request-form {
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.request-form h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
}

.form-section {
  margin-bottom: 30px;
}

.form-section h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #333;
}

.section-desc {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: #666;
}

.admin-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
}

.admin-card {
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.admin-card:hover {
  border-color: #93c5fd;
}

.admin-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.admin-name {
  font-weight: 600;
  font-size: 16px;
  color: #333;
  margin-bottom: 5px;
}

.admin-department {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.admin-permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.perm-tag {
  display: inline-block;
  padding: 2px 8px;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 4px;
  font-size: 12px;
}

.perm-more {
  display: inline-block;
  padding: 2px 8px;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 4px;
  font-size: 12px;
}

.no-perm {
  font-size: 12px;
  color: #9ca3af;
}

.empty-admins {
  text-align: center;
  padding: 30px;
  color: #999;
  background: #f9fafb;
  border-radius: 8px;
}

.permission-categories {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.category-group {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 15px;
}

.category-title {
  font-weight: 600;
  font-size: 15px;
  color: #333;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.permission-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.permission-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.permission-item:hover {
  background: #f9fafb;
}

.permission-item.selected {
  background: #eff6ff;
}

.perm-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
  color: #3b82f6;
}

.permission-item.selected .perm-checkbox {
  border-color: #3b82f6;
  background: #3b82f6;
  color: #fff;
}

.perm-info {
  flex: 1;
}

.perm-name {
  font-weight: 500;
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.perm-desc {
  font-size: 13px;
  color: #666;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
  transition: border-color 0.3s;
}

.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.3s;
}

.submit-btn:hover:not(:disabled) {
  background: #2563eb;
}

.submit-btn:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.request-history {
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.request-history h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
}

.loading, .empty {
  text-align: center;
  color: #999;
  padding: 40px;
}

.request-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.request-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.request-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.request-id {
  font-weight: 500;
  color: #333;
}

.request-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-approved {
  background: #d1fae5;
  color: #065f46;
}

.status-rejected {
  background: #fee2e2;
  color: #991b1b;
}

.request-body {
  font-size: 14px;
  color: #666;
}

.request-target {
  margin-bottom: 10px;
}

.request-permissions {
  margin-bottom: 10px;
}

.perm-tags {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-left: 5px;
}

.request-reason {
  margin-bottom: 12px;
}

.request-reason p {
  margin: 4px 0 0 0;
  color: #333;
  white-space: pre-wrap;
}

.request-time {
  margin-bottom: 8px;
}

.request-review {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.request-review > div {
  margin-bottom: 4px;
}
</style>
