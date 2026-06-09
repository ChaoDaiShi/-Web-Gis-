<!-- 社区通知页面 -->
<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";

const showToast = window.showToast;
const API_BASE = "http://127.0.0.1:5000/api";
const router = useRouter();
const userId = localStorage.getItem("user_id");
const notifications = ref([]);
const unreadCount = ref(0);

const formatTime = (timeStr) => {
  if (!timeStr) return "未知时间";
  const date = new Date(timeStr);
  return date.toLocaleString("zh-CN");
};

const getNotificationTypeText = (type) => {
  const typeMap = {
    like: "点赞",
    comment: "评论",
    reply: "回复",
    mention: "@提及",
    comment_like: "评论点赞"
  };
  return typeMap[type] || "通知";
};

const getNotificationIcon = (type) => {
  const iconMap = {
    like: "❤️",
    comment: "💬",
    reply: "↩️",
    mention: "@",
    comment_like: "👍"
  };
  return iconMap[type] || "📢";
};

async function loadNotifications() {
  try {
    const res = await fetch(`${API_BASE}/community/notifications?user_id=${userId}`);
    const data = await res.json();
    notifications.value = data.success ? data.data || [] : [];
  } catch (e) {
    console.error("加载通知失败:", e);
    notifications.value = [];
  }
}

async function loadUnreadCount() {
  try {
    const res = await fetch(`${API_BASE}/community/notifications/unread?user_id=${userId}`);
    const data = await res.json();
    unreadCount.value = data.success ? data.count : 0;
  } catch (e) {
    console.error("加载未读数量失败:", e);
    unreadCount.value = 0;
  }
}

async function handleNotificationClick(notification) {
  const wasUnread = notification.is_read === 0 || notification.is_read === false;
  
  if (wasUnread) {
    try {
      const res = await fetch(`${API_BASE}/community/notifications/${notification.id}/read?user_id=${userId}`, {
        method: "POST"
      });
      const data = await res.json();
      
      if (data.success) {
        notification.is_read = 1;
        unreadCount.value = Math.max(0, unreadCount.value - 1);
      } else {
        console.error("标记已读失败:", data.message);
      }
    } catch (e) {
      console.error("标记已读失败:", e);
    }
  }
  
  if (notification.post_id) {
    setTimeout(() => {
      router.push(`/community?post_id=${notification.post_id}`);
    }, 100);
  }
}

async function deleteNotification(notificationId) {
  if (!confirm("确定要删除这条通知吗？")) return;
  
  try {
    const res = await fetch(`${API_BASE}/community/notifications/${notificationId}?user_id=${userId}`, {
      method: "DELETE"
    });
    
    const data = await res.json();
    if (data.success) {
      const notification = notifications.value.find(n => n.id === notificationId);
      if (notification && !notification.is_read) {
        unreadCount.value = Math.max(0, unreadCount.value - 1);
      }
      notifications.value = notifications.value.filter(n => n.id !== notificationId);
      showToast("删除成功", "success");
    } else {
      showToast(data.message || "删除失败", "error");
    }
  } catch (e) {
    console.error("删除通知失败:", e);
    showToast("删除失败", "error");
  }
}

async function markAllAsRead() {
  if (!confirm("确定要标记所有通知为已读吗？")) return;
  
  try {
    await fetch(`${API_BASE}/community/notifications/read-all?user_id=${userId}`, {
      method: "POST"
    });
    notifications.value.forEach(n => {
      n.is_read = 1;
    });
    unreadCount.value = 0;
    showToast("已标记全部为已读", "success");
  } catch (e) {
    console.error("标记全部已读失败:", e);
  }
}

function goBack() {
  router.push("/community");
}

onMounted(() => {
  if (!userId) {
    showToast("请先登录", "warning");
    router.push("/login");
    return;
  }
  
  loadNotifications();
  loadUnreadCount();
});
</script>

<template>
  <div class="community-notifications-page">
    <AppTopBar variant="home">
      <template #actions>
        <button class="back-btn" @click="goBack">← 返回社区</button>
        <span class="unread-badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
      </template>
    </AppTopBar>
    
    <div class="page-content">
      <div class="page-header">
        <h1>社区通知</h1>
        <div class="header-actions">
          <span v-if="unreadCount > 0" class="unread-text">{{ unreadCount }} 条未读</span>
          <button class="mark-all-btn" v-if="notifications.length > 0" @click="markAllAsRead">
            全部已读
          </button>
        </div>
      </div>
      
      <div class="notifications-list">
            <div v-for="notification in notifications" 
                 :key="notification.id" 
                 :class="['notification-item', { 'unread': !notification.is_read, 'has-link': notification.post_id }]"
                 @click="handleNotificationClick(notification)">
              <div class="notification-icon">{{ getNotificationIcon(notification.type) }}</div>
              <div class="notification-content">
                <div class="notification-type">{{ getNotificationTypeText(notification.type) }}</div>
                <div class="notification-text">{{ notification.content }}</div>
                <div class="notification-time">{{ formatTime(notification.create_time) }}</div>
              </div>
              <div v-if="notification.post_id" class="notification-arrow">→</div>
              <button class="delete-btn" @click.stop="deleteNotification(notification.id)">
                🗑️
              </button>
            </div>
        
        <div v-if="notifications.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-text">暂无社区通知</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.community-notifications-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-content {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
  padding-top: 80px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.unread-text {
  font-size: 14px;
  color: #ff6b6b;
  font-weight: 500;
}

.mark-all-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.mark-all-btn:hover {
  background: #5568d3;
}

.notifications-list {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.notification-item {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.notification-item:last-child {
  margin-bottom: 0;
}

.notification-item:hover {
  background: #f8f9fa;
  border-color: #e8e8e8;
}

.notification-item.unread {
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
  border-left: 4px solid #ff6b6b;
}

.notification-item.has-link {
  cursor: pointer;
}

.notification-arrow {
  color: #999;
  font-size: 18px;
  margin-right: 8px;
  opacity: 0.6;
}

.notification-icon {
  font-size: 28px;
  line-height: 1;
}

.notification-content {
  flex: 1;
}

.notification-type {
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 4px;
}

.notification-text {
  font-size: 15px;
  color: #333;
  margin-bottom: 4px;
  line-height: 1.5;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  font-size: 16px;
  opacity: 0.5;
  transition: all 0.2s;
}

.delete-btn:hover {
  opacity: 1;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  color: #999;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.unread-badge {
  background: #ff6b6b;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}
</style>