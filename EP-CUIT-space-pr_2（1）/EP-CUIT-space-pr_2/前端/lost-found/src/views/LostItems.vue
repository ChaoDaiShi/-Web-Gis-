<script setup>
import { computed, onMounted, ref } from "vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");

const lostItems = ref([]);
const searchKeyword = ref("");
const filterCategory = ref("all");
const filterStatus = ref("all");

const categories = [
  { value: "all", label: "全部分类" },
  { value: "electronics", label: "电子产品" },
  { value: "documents", label: "证件文件" },
  { value: "bags", label: "包类" },
  { value: "clothing", label: "衣物" },
  { value: "books", label: "书籍文具" },
  { value: "others", label: "其他" }
];

const statusOptions = [
  { value: "all", label: "全部状态" },
  { value: "0", label: "待认领" },
  { value: "1", label: "已认领" },
  { value: "2", label: "已关闭" }
];

const formatStatus = (status) => ({ 0: "待认领", 1: "已认领", 2: "已关闭" }[status] || "未知");

const filteredItems = computed(() => {
  return lostItems.value.filter(item => {
    const matchesSearch = !searchKeyword.value || 
      item.title.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      item.description.toLowerCase().includes(searchKeyword.value.toLowerCase());
    
    const matchesCategory = filterCategory.value === "all" || item.category === filterCategory.value;
    const matchesStatus = filterStatus.value === "all" || String(item.status) === filterStatus.value;
    
    return matchesSearch && matchesCategory && matchesStatus;
  });
});

async function loadLostItems() {
  try {
    const res = await fetch(`${API_BASE}/lost-items`);
    const data = await res.json();
    lostItems.value = data.success ? data.data || [] : [];
  } catch {
    lostItems.value = [];
  }
}

function goToDetail(itemId) {
  window.location.href = `/lost-item-detail?id=${itemId}`;
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
  loadLostItems();
});
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">失物列表</div>
      <div class="topbar-user">管</div>
    </div>
    
    <div class="container">
      <div class="search-filters">
        <div class="search-box">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="搜索物品名称或描述..." 
            class="search-input"
          />
        </div>
        
        <div class="filter-group">
          <select v-model="filterCategory" class="filter-select">
            <option v-for="cat in categories" :key="cat.value" :value="cat.value">
              {{ cat.label }}
            </option>
          </select>
          
          <select v-model="filterStatus" class="filter-select">
            <option v-for="status in statusOptions" :key="status.value" :value="status.value">
              {{ status.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="items-list">
        <div v-if="filteredItems.length === 0" class="empty-state">
          <div class="empty-icon">📦</div>
          <div class="empty-text">暂无失物信息</div>
        </div>
        
        <div v-else class="items-grid">
          <div 
            v-for="item in filteredItems" 
            :key="item.item_id" 
            class="item-card"
            @click="goToDetail(item.item_id)"
          >
            <div class="item-image">
              <img v-if="item.image_url" :src="item.image_url" :alt="item.title" />
              <div v-else class="no-image">📷</div>
            </div>
            
            <div class="item-content">
              <div class="item-title">{{ item.title }}</div>
              <div class="item-meta">
                <span class="item-category">{{ categories.find(c => c.value === item.category)?.label || '其他' }}</span>
                <span class="item-status" :class="`status-${item.status}`">
                  {{ formatStatus(item.status) }}
                </span>
              </div>
              <div class="item-description">{{ item.description }}</div>
              <div class="item-time">拾取时间: {{ item.pickup_time }}</div>
              <div class="item-location">拾取地点: {{ item.location }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="back-button">
        <button @click="goToProfile" class="btn-back">返回个人中心</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 1200px;
  margin: 80px auto 20px;
  padding: 0 20px;
}

.search-filters {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  align-items: center;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 300px;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.filter-group {
  display: flex;
  gap: 10px;
}

.filter-select {
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background: white;
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.item-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.item-image {
  height: 200px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image {
  font-size: 48px;
  color: #999;
}

.item-content {
  padding: 20px;
}

.item-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #333;
}

.item-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.item-category {
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.item-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-0 { background: #fff3cd; color: #856404; }
.status-1 { background: #d4edda; color: #155724; }
.status-2 { background: #f8d7da; color: #721c24; }

.item-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
  line-height: 1.4;
}

.item-time, .item-location {
  color: #999;
  font-size: 12px;
  margin-bottom: 5px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-text {
  font-size: 16px;
}

.back-button {
  text-align: center;
  margin-top: 30px;
}

.btn-back {
  padding: 12px 24px;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.btn-back:hover {
  opacity: 0.9;
}

@media (max-width: 768px) {
  .search-filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    min-width: auto;
  }
  
  .items-grid {
    grid-template-columns: 1fr;
  }
}
</style>