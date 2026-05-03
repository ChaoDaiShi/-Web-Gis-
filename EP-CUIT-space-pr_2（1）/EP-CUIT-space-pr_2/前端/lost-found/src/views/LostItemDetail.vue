<script setup>
import { onMounted, ref } from "vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");

const item = ref(null);
const isLoading = ref(true);

const formatStatus = (status) => ({ 0: "待认领", 1: "已认领", 2: "已关闭" }[status] || "未知");

async function loadItemDetail() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const itemId = urlParams.get('id');
    
    if (!itemId) {
      alert("物品ID不存在");
      goBack();
      return;
    }
    
    const res = await fetch(`${API_BASE}/lost-items/${itemId}`);
    const data = await res.json();
    
    if (data.success) {
      item.value = data.data;
    } else {
      alert("获取物品详情失败");
      goBack();
    }
  } catch (error) {
    console.error("加载物品详情失败:", error);
    alert("加载失败，请重试");
    goBack();
  } finally {
    isLoading.value = false;
  }
}

function goToClaimForm() {
  if (!item.value) return;
  
  if (item.value.status !== 0) {
    alert("该物品无法认领");
    return;
  }
  
  window.location.href = `/claim-form?id=${item.value.item_id}`;
}

function goBack() {
  window.location.href = "/lost-items";
}

function goToProfile() {
  window.location.href = "/profile";
}

onMounted(() => {
  if (!userId) {
    alert("请先登录");
    window.location.href = "/login";
    return;
  }
  loadItemDetail();
});
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">失物详情</div>
      <div class="topbar-user">管</div>
    </div>
    
    <div class="container">
      <div v-if="isLoading" class="loading">
        <div class="loading-spinner"></div>
        <div>加载中...</div>
      </div>
      
      <div v-else-if="!item" class="error">
        <div class="error-icon">❌</div>
        <div>物品不存在</div>
        <button @click="goBack" class="btn-back">返回列表</button>
      </div>
      
      <div v-else class="detail-content">
        <div class="detail-header">
          <h1 class="item-title">{{ item.title }}</h1>
          <div class="item-status" :class="`status-${item.status}`">
            {{ formatStatus(item.status) }}
          </div>
        </div>
        
        <div class="detail-grid">
          <div class="image-section">
            <div class="item-image">
              <img v-if="item.image_url" :src="item.image_url" :alt="item.title" />
              <div v-else class="no-image">📷 暂无图片</div>
            </div>
          </div>
          
          <div class="info-section">
            <div class="info-card">
              <h3>物品信息</h3>
              <div class="info-item">
                <span class="info-label">物品名称:</span>
                <span class="info-value">{{ item.title }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">物品分类:</span>
                <span class="info-value">{{ item.category_name || item.category }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">拾取时间:</span>
                <span class="info-value">{{ item.pickup_time }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">拾取地点:</span>
                <span class="info-value">{{ item.location }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">当前状态:</span>
                <span class="info-value" :class="`status-${item.status}`">
                  {{ formatStatus(item.status) }}
                </span>
              </div>
            </div>
            
            <div class="description-card">
              <h3>物品描述</h3>
              <div class="description-content">
                {{ item.description || "暂无详细描述" }}
              </div>
            </div>
            
            <div class="contact-card">
              <h3>发布者信息</h3>
              <div class="info-item">
                <span class="info-label">发布者:</span>
                <span class="info-value">{{ item.publisher_name || "匿名" }}</span>
              </div>
              <div v-if="item.contact_phone" class="info-item">
                <span class="info-label">联系电话:</span>
                <span class="info-value">{{ item.contact_phone }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="action-buttons">
          <button v-if="item.status === 0" @click="goToClaimForm" class="btn-claim">
            🎯 申请认领
          </button>
          <button @click="goBack" class="btn-back">返回列表</button>
          <button @click="goToProfile" class="btn-profile">个人中心</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 1000px;
  margin: 80px auto 20px;
  padding: 0 20px;
}

.loading, .error {
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

.error-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.detail-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.item-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.item-status {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-0 { background: #fff3cd; color: #856404; }
.status-1 { background: #d4edda; color: #155724; }
.status-2 { background: #f8d7da; color: #721c24; }

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 30px;
  margin-bottom: 30px;
}

.image-section {
  display: flex;
  flex-direction: column;
}

.item-image {
  height: 300px;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image {
  font-size: 48px;
  color: #ccc;
  text-align: center;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card, .description-card, .contact-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.info-card h3, .description-card h3, .contact-card h3 {
  margin: 0 0 15px 0;
  font-size: 18px;
  color: #333;
  border-bottom: 2px solid #33ccff;
  padding-bottom: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.info-item:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.info-label {
  font-weight: 600;
  color: #666;
  min-width: 100px;
}

.info-value {
  color: #333;
  text-align: right;
  flex: 1;
}

.description-content {
  line-height: 1.6;
  color: #666;
  white-space: pre-wrap;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn-claim {
  padding: 12px 24px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-claim:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.btn-back, .btn-profile {
  padding: 12px 24px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-back:hover, .btn-profile:hover {
  background: #5a6268;
}

@media (max-width: 768px) {
  .detail-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .item-title {
    font-size: 20px;
  }
}
</style>