<!-- 认领审核 -->
<script setup>
import { computed, onMounted, ref } from "vue";

const showToast = window.showToast;
const showConfirm = window.showConfirm;
const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");

const claims = ref([]);
const filterStatus = ref("all");
const searchKeyword = ref("");
const isLoading = ref(true);
const detailClaim = ref(null);
const showDetailModal = ref(false);

const statusOptions = [
  { value: "all", label: "全部状态" },
  { value: "0", label: "待审核" },
  { value: "1", label: "审核通过" },
  { value: "2", label: "审核驳回" },
  { value: "3", label: "已取消" }
];

const formatClaimStatus = (status) => ({ 0: "待审核", 1: "审核通过", 2: "审核驳回", 3: "已取消" }[status] || "未知");

const filteredClaims = computed(() => {
  return claims.value.filter(claim => {
    const matchesSearch = !searchKeyword.value || 
      claim.item_title?.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      claim.applicant_name?.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      claim.applicant_phone?.includes(searchKeyword.value);
    
    const matchesStatus = filterStatus.value === "all" || String(claim.status) === filterStatus.value;
    
    return matchesSearch && matchesStatus;
  });
});

async function loadClaims() {
  try {
    const res = await fetch(`${API_BASE}/admin/claims`);
    const data = await res.json();
    claims.value = data.success ? data.data || [] : [];
  } catch (error) {
    console.error("加载认领申请失败:", error);
    claims.value = [];
  } finally {
    isLoading.value = false;
  }
}

async function approveClaim(claimId) {
  const confirmed = await showConfirm({
    title: '确认通过',
    message: '确定要通过这个认领申请吗？',
    type: 'success',
    confirmText: '确认通过',
    cancelText: '取消'
  });
  if (!confirmed) return;
  
  const remark = prompt("请输入审核备注（选填）:");
  if (remark === null) return;
  
  try {
    const res = await fetch(`${API_BASE}/admin/claims/${claimId}/approve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reviewer_id: userId,
        review_remark: remark || ""
      }),
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast("审核通过成功", "success");
      loadClaims();
    } else {
      showToast("审核失败: " + (data.message || "请重试"), "error");
    }
  } catch (error) {
    console.error("审核认领申请失败:", error);
    showToast("审核失败，请检查网络连接后重试", "error");
  }
}

async function rejectClaim(claimId) {
  const confirmed = await showConfirm({
    title: '确认驳回',
    message: '确定要驳回这个认领申请吗？',
    type: 'danger',
    confirmText: '确认驳回',
    cancelText: '取消'
  });
  if (!confirmed) return;
  
  const remark = prompt("请输入驳回原因（必填）:");
  if (remark === null) return;
  
  if (!remark.trim()) {
    showToast("请填写驳回原因", "warning");
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/admin/claims/${claimId}/reject`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reviewer_id: userId,
        review_remark: remark
      }),
    });
    
    const data = await res.json();
    
    if (data.success) {
      showToast("驳回成功", "success");
      loadClaims();
    } else {
      showToast("驳回失败: " + (data.message || "请重试"), "error");
    }
  } catch (error) {
    console.error("驳回认领申请失败:", error);
    showToast("驳回失败，请检查网络连接后重试", "error");
  }
}

function viewClaimDetail(claim) {
  detailClaim.value = claim;
  showDetailModal.value = true;
}

function closeDetailModal() {
  showDetailModal.value = false;
  detailClaim.value = null;
}

function goToProfile() {
  window.location.href = "/profile";
}

function goToAdmin() {
  window.location.href = "/admin";
}

onMounted(() => {
  if (!userId) {
    showToast("请先登录", "warning");
    window.location.href = "/login";
    return;
  }
  loadClaims();
});
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">认领申请审核</div>
      <div class="topbar-user">管</div>
    </div>
    
    <div class="container">
      <div class="toolbar">
        <div class="search-section">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="搜索物品名称、认领人姓名或电话..." 
            class="search-input"
          />
        </div>
        
        <div class="filter-section">
          <select v-model="filterStatus" class="filter-select">
            <option v-for="status in statusOptions" :key="status.value" :value="status.value">
              {{ status.label }}
            </option>
          </select>
          
          <button @click="loadClaims" class="btn-refresh">🔄 刷新</button>
        </div>
      </div>

      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-label">待审核:</span>
          <span class="stat-value">{{ claims.filter(c => c.status === 0).length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">已通过:</span>
          <span class="stat-value">{{ claims.filter(c => c.status === 1).length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">已驳回:</span>
          <span class="stat-value">{{ claims.filter(c => c.status === 2).length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">总计:</span>
          <span class="stat-value">{{ claims.length }}</span>
        </div>
      </div>

      <div class="table-container">
        <div v-if="isLoading" class="loading">
          <div class="loading-spinner"></div>
          <div>加载中...</div>
        </div>
        
        <div v-else-if="filteredClaims.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-text">暂无认领申请记录</div>
        </div>
        
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>物品名称</th>
              <th>认领人</th>
              <th>联系方式</th>
              <th>申请时间</th>
              <th>审核状态</th>
              <th>审核时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="claim in filteredClaims" :key="claim.claim_id">
              <td class="item-title" @click="viewClaimDetail(claim)" title="点击查看详情">
                {{ claim.item_title }}
              </td>
              <td>{{ claim.applicant_name }}</td>
              <td>{{ claim.applicant_phone }}</td>
              <td>{{ claim.create_time }}</td>
              <td>
                <span :class="`status-badge status-${claim.status}`">
                  {{ formatClaimStatus(claim.status) }}
                </span>
              </td>
              <td>{{ claim.review_time || "-" }}</td>
              <td class="actions">
                <button 
                  v-if="claim.status === 0" 
                  @click="approveClaim(claim.claim_id)" 
                  class="btn-approve"
                >
                  通过
                </button>
                <button 
                  v-if="claim.status === 0" 
                  @click="rejectClaim(claim.claim_id)" 
                  class="btn-reject"
                >
                  驳回
                </button>
                <button 
                  @click="viewClaimDetail(claim)" 
                  class="btn-detail"
                >
                  详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="navigation-buttons">
        <button @click="goToProfile" class="btn-nav">返回个人中心</button>
        <button @click="goToAdmin" class="btn-nav">后台管理主页</button>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showDetailModal" class="detail-modal-overlay" @click="closeDetailModal">
        <div class="detail-modal" @click.stop>
          <div class="modal-header">
            <h3>认领申请详情</h3>
            <button class="close-btn" @click="closeDetailModal">×</button>
          </div>
          <div class="modal-body" v-if="detailClaim">
            <div class="detail-section">
              <h4>物品信息</h4>
              <div class="detail-row"><span class="label">物品名称：</span>{{ detailClaim.item_title }}</div>
              <div class="detail-row"><span class="label">物品分类：</span>{{ detailClaim.item_category }}</div>
              <div class="detail-row"><span class="label">拾取地点：</span>{{ detailClaim.item_location }}</div>
              <div class="detail-row"><span class="label">拾取时间：</span>{{ detailClaim.item_pickup_time }}</div>
            </div>
            <div class="detail-section">
              <h4>认领人信息</h4>
              <div class="detail-row"><span class="label">姓名：</span>{{ detailClaim.applicant_name }}</div>
              <div class="detail-row"><span class="label">电话：</span>{{ detailClaim.applicant_phone }}</div>
              <div class="detail-row"><span class="label">邮箱：</span>{{ detailClaim.applicant_email || "未填写" }}</div>
            </div>
            <div class="detail-section">
              <h4>认领信息</h4>
              <div class="detail-row"><span class="label">认领理由：</span>{{ detailClaim.claim_reason }}</div>
              <div class="detail-row"><span class="label">物品特征：</span>{{ detailClaim.item_description }}</div>
              <div class="detail-row"><span class="label">申请时间：</span>{{ detailClaim.create_time }}</div>
              <div class="detail-row"><span class="label">当前状态：</span>{{ formatClaimStatus(detailClaim.status) }}</div>
              <div class="detail-row" v-if="detailClaim.review_time"><span class="label">审核时间：</span>{{ detailClaim.review_time }}</div>
              <div class="detail-row" v-if="detailClaim.review_remark"><span class="label">审核备注：</span>{{ detailClaim.review_remark }}</div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.container {
  max-width: 1200px;
  margin: 80px auto 20px;
  padding: 0 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.search-section {
  flex: 1;
  min-width: 300px;
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.filter-section {
  display: flex;
  gap: 10px;
  align-items: center;
}

.filter-select {
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
}

.btn-refresh {
  padding: 10px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-refresh:hover {
  background: #5a6268;
}

.stats-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-item {
  background: white;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 100px;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading, .empty-state {
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

.empty-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
  position: sticky;
  top: 0;
}

.item-title {
  color: #33ccff;
  cursor: pointer;
  font-weight: 500;
}

.item-title:hover {
  text-decoration: underline;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-0 { background: #fff3cd; color: #856404; }
.status-1 { background: #d4edda; color: #155724; }
.status-2 { background: #f8d7da; color: #721c24; }
.status-3 { background: #e2e3e5; color: #383d41; }

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-approve {
  padding: 6px 12px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-approve:hover {
  background: #218838;
}

.btn-reject {
  padding: 6px 12px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-reject:hover {
  background: #c82333;
}

.btn-detail {
  padding: 6px 12px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-detail:hover {
  background: #5a6268;
}

.navigation-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.btn-nav {
  padding: 12px 24px;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.btn-nav:hover {
  opacity: 0.9;
}

.detail-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  padding: 20px;
}

.detail-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
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

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: white;
  opacity: 0.8;
}

.close-btn:hover {
  opacity: 1;
}

.modal-body {
  padding: 20px;
}

.detail-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #333;
  border-bottom: 2px solid #33ccff;
  padding-bottom: 8px;
}

.detail-row {
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.detail-row .label {
  font-weight: 600;
  color: #555;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-section {
    min-width: auto;
  }
  
  .stats-bar {
    justify-content: center;
  }
  
  .stat-item {
    min-width: 80px;
    padding: 10px 15px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .data-table {
    font-size: 12px;
  }
  
  .data-table th,
  .data-table td {
    padding: 8px 12px;
  }
  
  .navigation-buttons {
    flex-direction: column;
  }
}
</style>