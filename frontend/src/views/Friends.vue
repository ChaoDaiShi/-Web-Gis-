<!-- 好友列表 -->
<script setup>
import { ref, onMounted } from "vue";
import AppTopBar from "../components/AppTopBar.vue";
import { useRouter } from 'vue-router';

const router = useRouter();
const showToast = window.showToast;
const API_BASE = "http://127.0.0.1:5000/api";

const currentUserId = localStorage.getItem("user_id");

const activeTab = ref("friends");
const friends = ref([]);
const requests = ref([]);
const loading = ref(false);

async function loadFriends() {
  try {
    loading.value = true;
    const res = await fetch(`${API_BASE}/friends?user_id=${currentUserId}`);
    const data = await res.json();
    friends.value = data.success ? data.data || [] : [];
  } catch (e) {
    console.error("加载好友列表失败:", e);
  } finally {
    loading.value = false;
  }
}

async function loadRequests() {
  try {
    loading.value = true;
    const res = await fetch(`${API_BASE}/friends/requests?user_id=${currentUserId}`);
    const data = await res.json();
    requests.value = data.success ? data.data || [] : [];
  } catch (e) {
    console.error("加载好友请求失败:", e);
  } finally {
    loading.value = false;
  }
}

async function acceptRequest(friendshipId) {
  try {
    const res = await fetch(`${API_BASE}/friends/accept/${friendshipId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: currentUserId })
    });
    
    const data = await res.json();
    if (data.success) {
      showToast("已接受好友请求", "success");
      loadRequests();
      loadFriends();
    } else {
      showToast(data.message, "error");
    }
  } catch (e) {
    console.error("接受好友请求失败:", e);
    showToast("操作失败", "error");
  }
}

async function rejectRequest(friendshipId) {
  try {
    const res = await fetch(`${API_BASE}/friends/reject/${friendshipId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: currentUserId })
    });
    
    const data = await res.json();
    if (data.success) {
      showToast("已拒绝好友请求", "success");
      loadRequests();
    } else {
      showToast(data.message, "error");
    }
  } catch (e) {
    console.error("拒绝好友请求失败:", e);
    showToast("操作失败", "error");
  }
}

async function deleteFriend(friendId) {
  const confirmed = await window.showConfirm({
    title: "确认删除",
    message: "确定要删除该好友吗？",
    type: "warning"
  });
  
  if (!confirmed) return;
  
  try {
    const res = await fetch(`${API_BASE}/friends/${friendId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: currentUserId })
    });
    
    const data = await res.json();
    if (data.success) {
      showToast("已删除好友", "success");
      loadFriends();
    } else {
      showToast(data.message, "error");
    }
  } catch (e) {
    console.error("删除好友失败:", e);
    showToast("操作失败", "error");
  }
}

function openChat(friend) {
  router.push(`/chat/${friend.friend_id}`);
}

function viewProfile(friendId) {
  router.push(`/user/${friendId}`);
}

function switchTab(tab) {
  activeTab.value = tab;
  if (tab === "friends") loadFriends();
  if (tab === "requests") loadRequests();
}

function goBack() {
  router.back();
}

onMounted(() => {
  if (!currentUserId) {
    showToast("请先登录", "warning");
    router.push("/login");
    return;
  }
  loadFriends();
});
</script>

<template>
  <div class="friends-page">
    <AppTopBar variant="inner" />
    
    <div class="container">
      <div class="header">
        <button @click="goBack" class="back-btn">← 返回</button>
        <h2>好友</h2>
      </div>
      
      <div class="tabs">
        <button :class="activeTab === 'friends' ? 'tab active' : 'tab'" @click="switchTab('friends')">
          好友列表
        </button>
        <button :class="activeTab === 'requests' ? 'tab active' : 'tab'" @click="switchTab('requests')">
          好友请求
          <span v-if="requests.length > 0" class="badge">{{ requests.length }}</span>
        </button>
      </div>
      
      <!-- 好友列表 -->
      <div v-if="activeTab === 'friends'" class="list">
        <div v-for="friend in friends" :key="friend.friendship_id" class="friend-item">
          <div class="avatar-wrapper" @click="viewProfile(friend.friend_id)">
            <img v-if="friend.avatar" :src="friend.avatar" class="avatar" />
            <div v-else class="avatar-placeholder">👤</div>
          </div>
          
          <div class="friend-info" @click="viewProfile(friend.friend_id)">
            <div class="name">{{ friend.username }}</div>
            <div class="time">好友 since {{ friend.friend_since?.substring(0, 10) }}</div>
          </div>
          
          <div class="actions">
            <button @click="openChat(friend)" class="btn-chat">💬</button>
            <button @click="deleteFriend(friend.friend_id)" class="btn-delete">🗑️</button>
          </div>
        </div>
        
        <div v-if="friends.length === 0 && !loading" class="empty">
          <p>暂无好友</p>
          <p class="hint">在社区互动或认领物品时可添加好友</p>
        </div>
      </div>
      
      <!-- 好友请求 -->
      <div v-if="activeTab === 'requests'" class="list">
        <div v-for="req in requests" :key="req.friendship_id" class="request-item">
          <div class="avatar-wrapper" @click="viewProfile(req.requester_id)">
            <img v-if="req.avatar" :src="req.avatar" class="avatar" />
            <div v-else class="avatar-placeholder">👤</div>
          </div>
          
          <div class="request-info">
            <div class="name">{{ req.username }}</div>
            <div class="time">{{ req.created_at?.substring(0, 10) }}</div>
          </div>
          
          <div class="actions">
            <button @click="acceptRequest(req.friendship_id)" class="btn-accept">接受</button>
            <button @click="rejectRequest(req.friendship_id)" class="btn-reject">拒绝</button>
          </div>
        </div>
        
        <div v-if="requests.length === 0 && !loading" class="empty">
          <p>暂无好友请求</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.friends-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
}

.back-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #666;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tab {
  padding: 10px 20px;
  border: none;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab.active {
  background: #1890ff;
  color: white;
}

.badge {
  background: #ff4d4f;
  color: white;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 10px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.friend-item, .request-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-wrapper {
  cursor: pointer;
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.friend-info, .request-info {
  flex: 1;
  cursor: pointer;
}

.name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.time {
  font-size: 12px;
  color: #999;
}

.actions {
  display: flex;
  gap: 8px;
}

.actions button {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-chat {
  background: #1890ff;
  color: white;
}

.btn-delete {
  background: #f0f0f0;
}

.btn-accept {
  background: #52c41a;
  color: white;
}

.btn-reject {
  background: #f0f0f0;
  color: #666;
}

.empty {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty .hint {
  font-size: 14px;
  margin-top: 8px;
}
</style>
