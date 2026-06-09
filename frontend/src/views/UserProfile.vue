<!-- 用户主页 - 查看他人主页 -->
<script setup>
import { computed, onMounted, ref } from "vue";
import AppTopBar from "../components/AppTopBar.vue";
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();
const showToast = window.showToast;
const API_BASE = "http://127.0.0.1:5000/api";

const currentUserId = localStorage.getItem("user_id");
const targetUserId = ref(route.params.id);

const loading = ref(true);
const username = ref("");
const avatarUrl = ref("");
const bgImage = ref("");
const signature = ref("");
const bio = ref("");
const createTime = ref("");
const identity = ref("");
const postCount = ref(0);
const publishCount = ref(0);
const friendCount = ref(0);
const isFriend = ref(false);
const friendStatus = ref(null);
const isFollowing = ref(false);
const isOwn = ref(false);

const activeTab = ref("posts");
const posts = ref([]);
const items = ref([]);

const pageStyle = computed(() => {
  if (bgImage.value) {
    return {
      background: `url(${bgImage.value}) center/cover`,
      minHeight: '100vh'
    };
  }
  return {};
});

async function loadUserProfile() {
  try {
    loading.value = true;
    const res = await fetch(`${API_BASE}/user/${targetUserId.value}/profile?current_user_id=${currentUserId}`);
    const data = await res.json();
    
    if (data.success && data.data) {
      const user = data.data;
      username.value = user.username || "用户名";
      avatarUrl.value = user.avatar ? (user.avatar.startsWith('http') ? user.avatar : `http://127.0.0.1:5000${user.avatar}`) : "";
      bgImage.value = user.bg_image ? (user.bg_image.startsWith('http') ? user.bg_image : `http://127.0.0.1:5000${user.bg_image}`) : "";
      signature.value = user.signature || "暂无个性签名";
      bio.value = user.bio || "暂无个人简介";
      createTime.value = user.create_time || "";
      identity.value = user.identity || "";
      postCount.value = user.post_count || 0;
      publishCount.value = user.publish_count || 0;
      friendCount.value = user.friend_count || 0;
      isFriend.value = user.is_friend || false;
      friendStatus.value = user.friend_status;
      isFollowing.value = user.is_following || false;
      isOwn.value = user.is_own || false;
    } else {
      showToast("用户不存在", "error");
      router.push("/home");
    }
  } catch (e) {
    console.error("加载用户主页失败:", e);
    showToast("加载失败", "error");
  } finally {
    loading.value = false;
  }
}

async function loadUserPosts() {
  try {
    const res = await fetch(`${API_BASE}/user/${targetUserId.value}/posts?current_user_id=${currentUserId}`);
    const data = await res.json();
    posts.value = data.success ? data.data || [] : [];
  } catch (e) {
    console.error("加载帖子失败:", e);
    posts.value = [];
  }
}

async function loadUserItems() {
  try {
    const res = await fetch(`${API_BASE}/user/${targetUserId.value}/items`);
    const data = await res.json();
    items.value = data.success ? data.data || [] : [];
  } catch (e) {
    console.error("加载失物失败:", e);
    items.value = [];
  }
}

function switchTab(tab) {
  activeTab.value = tab;
  if (tab === "posts") loadUserPosts();
  if (tab === "items") loadUserItems();
}

async function addFriend() {
  if (!currentUserId) {
    showToast("请先登录", "warning");
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/friends/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUserId,
        friend_id: targetUserId.value
      })
    });
    
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success");
      loadUserProfile();
    } else {
      showToast(data.message, "error");
    }
  } catch (e) {
    console.error("添加好友失败:", e);
    showToast("操作失败", "error");
  }
}

async function toggleFollow() {
  if (!currentUserId) {
    showToast("请先登录", "warning");
    return;
  }
  
  try {
    const action = isFollowing.value ? "unfollow" : "follow";
    const res = await fetch(`${API_BASE}/community/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUserId,
        target_user_id: targetUserId.value
      })
    });
    
    const data = await res.json();
    if (data.success) {
      isFollowing.value = !isFollowing.value;
      showToast(isFollowing.value ? "关注成功" : "取消关注成功", "success");
    } else {
      showToast(data.message, "error");
    }
  } catch (e) {
    console.error("关注操作失败:", e);
    showToast("操作失败", "error");
  }
}

function openChat() {
  router.push(`/chat/${targetUserId.value}`);
}

function goBack() {
  router.back();
}

function formatTime(time) {
  if (!time) return "";
  return time.substring(0, 10);
}

function formatType(type) {
  return type === 0 ? "丢失" : "拾到";
}

function formatStatus(status, type) {
  if (status === 2) return "已关闭";
  if (type === 0) {
    return status === 0 ? "未找到" : "已找到";
  } else {
    return status === 0 ? "未被认领" : "已被认领";
  }
}

onMounted(() => {
  if (!targetUserId.value) {
    showToast("用户不存在", "error");
    router.push("/home");
    return;
  }
  loadUserProfile();
});
</script>

<template>
  <div :style="pageStyle" class="user-profile-page">
    <AppTopBar variant="inner" />
    
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else class="container">
      <!-- 头部信息 -->
      <div class="profile-header">
        <div class="avatar-wrapper">
          <img v-if="avatarUrl" :src="avatarUrl" class="avatar" />
          <div v-else class="avatar-placeholder">👤</div>
        </div>
        
        <div class="user-info">
          <h2 class="username">
            {{ username }}
            <span v-if="isOwn" class="own-badge">我的主页</span>
          </h2>
          <p class="signature">{{ signature }}</p>
          <div class="stats">
            <span>帖子 {{ postCount }}</span>
            <span>发布 {{ publishCount }}</span>
            <span>好友 {{ friendCount }}</span>
          </div>
        </div>
        
        <div class="actions">
          <!-- 自己的主页 -->
          <template v-if="isOwn">
            <button @click="goBack" class="btn-back">返回</button>
          </template>
          
          <!-- 他人的主页 -->
          <template v-else>
            <button @click="openChat" class="btn-chat">
              💬 发消息
            </button>
            
            <button v-if="!isFriend && friendStatus !== 'pending'" @click="addFriend" class="btn-add-friend">
              ➕ 加好友
            </button>
            <button v-else-if="friendStatus === 'pending'" class="btn-pending" disabled>
              ⏳ 待验证
            </button>
            <button v-else-if="isFriend" class="btn-friend" disabled>
              ✓ 好友
            </button>
            
            <button @click="toggleFollow" :class="isFollowing ? 'btn-unfollow' : 'btn-follow'">
              {{ isFollowing ? '已关注' : '➕ 关注' }}
            </button>
            
            <button @click="goBack" class="btn-back">返回</button>
          </template>
        </div>
      </div>
      
      <!-- 个人简介 -->
      <div class="bio-section" v-if="bio">
        <h3>个人简介</h3>
        <p>{{ bio }}</p>
      </div>
      
      <!-- 基本信息 -->
      <div class="info-section">
        <div class="info-item">
          <span class="label">身份：</span>
          <span class="value">{{ identity || '未设置' }}</span>
        </div>
        <div class="info-item">
          <span class="label">注册时间：</span>
          <span class="value">{{ createTime }}</span>
        </div>
      </div>
      
      <!-- 内容标签页 -->
      <div class="tabs">
        <button :class="activeTab === 'posts' ? 'tab active' : 'tab'" @click="switchTab('posts')">
          帖子
        </button>
        <button :class="activeTab === 'items' ? 'tab active' : 'tab'" @click="switchTab('items')">
          发布的物品
        </button>
      </div>
      
      <!-- 帖子列表 -->
      <div v-if="activeTab === 'posts'" class="content-list">
        <div v-for="post in posts" :key="post.post_id" class="post-card">
          <h4>{{ post.title }}</h4>
          <p class="post-content">{{ post.content?.substring(0, 100) }}{{ post.content?.length > 100 ? '...' : '' }}</p>
          <div class="post-meta">
            <span>{{ formatTime(post.created_at) }}</span>
            <span>❤️ {{ post.likes_count || 0 }}</span>
            <span>💬 {{ post.comments_count || 0 }}</span>
          </div>
        </div>
        <div v-if="posts.length === 0" class="empty">暂无帖子</div>
      </div>
      
      <!-- 物品列表 -->
      <div v-if="activeTab === 'items'" class="content-list">
        <div v-for="item in items" :key="item.item_id" class="item-card">
          <h4>{{ item.title }}</h4>
          <p class="item-desc">{{ item.description?.substring(0, 50) }}{{ item.description?.length > 50 ? '...' : '' }}</p>
          <div class="item-meta">
            <span :class="item.type === 0 ? 'type-lost' : 'type-found'">{{ formatType(item.type) }}</span>
            <span>{{ formatStatus(item.status, item.type) }}</span>
            <span>{{ formatTime(item.create_time) }}</span>
          </div>
        </div>
        <div v-if="items.length === 0" class="empty">暂无发布的物品</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-profile-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e0e0e0;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-header {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.avatar-wrapper {
  flex-shrink: 0;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.avatar-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
}

.user-info {
  flex: 1;
}

.username {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.own-badge {
  font-size: 12px;
  background: #1890ff;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: normal;
}

.signature {
  color: #666;
  margin: 0 0 12px 0;
}

.stats {
  display: flex;
  gap: 20px;
  color: #888;
  font-size: 14px;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.actions button {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-chat {
  background: #1890ff;
  color: white;
}

.btn-chat:hover {
  background: #40a9ff;
}

.btn-add-friend {
  background: #52c41a;
  color: white;
}

.btn-add-friend:hover {
  background: #73d13d;
}

.btn-pending, .btn-friend {
  background: #f0f0f0;
  color: #888;
  cursor: default;
}

.btn-follow {
  background: #1890ff;
  color: white;
}

.btn-unfollow {
  background: #f0f0f0;
  color: #666;
}

.btn-back {
  background: #f0f0f0;
  color: #666;
}

.bio-section, .info-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.bio-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.bio-section p {
  margin: 0;
  color: #666;
  line-height: 1.6;
}

.info-section {
  display: flex;
  gap: 30px;
}

.info-item {
  display: flex;
  gap: 8px;
}

.info-item .label {
  color: #888;
}

.info-item .value {
  color: #333;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tab {
  padding: 10px 24px;
  border: none;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}

.tab.active {
  background: #1890ff;
  color: white;
}

.content-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-card, .item-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}

.post-card h4, .item-card h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.post-content, .item-desc {
  color: #666;
  margin: 0 0 12px 0;
  font-size: 14px;
}

.post-meta, .item-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.type-lost {
  color: #ff4d4f;
}

.type-found {
  color: #52c41a;
}

.empty {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>
