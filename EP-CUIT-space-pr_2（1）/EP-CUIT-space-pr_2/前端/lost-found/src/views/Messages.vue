<script setup>
import { computed, onMounted, ref } from "vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");
const activeTab = ref("all");
const messages = ref([]);
const unreadCount = ref(0);

const formatTime = (timeStr) => {
  if (!timeStr) return "未知时间";
  const date = new Date(timeStr);
  return date.toLocaleString("zh-CN");
};

const getMessageTypeText = (type) => {
  const typeMap = {
    system: "系统通知",
    claim: "认领通知", 
    publish: "发布通知",
    reminder: "提醒通知"
  };
  return typeMap[type] || "系统通知";
};

const getMessageTypeClass = (type) => {
  const classMap = {
    system: "type-system",
    claim: "type-claim",
    publish: "type-publish",
    reminder: "type-reminder"
  };
  return classMap[type] || "type-system";
};

const tabClass = (tab) => (activeTab.value === tab ? "tab-btn active" : "tab-btn");

const filteredMessages = computed(() => {
  if (activeTab.value === "all") return messages.value;
  if (activeTab.value === "unread") return messages.value.filter(msg => !msg.is_read);
  return messages.value.filter(msg => msg.message_type === activeTab.value);
});

async function loadMessages() {
  try {
    const res = await fetch(`${API_BASE}/my/messages?user_id=${userId}`);
    const data = await res.json();
    messages.value = data.success ? data.data || [] : [];
  } catch {
    messages.value = [];
  }
}

async function loadUnreadCount() {
  try {
    const res = await fetch(`${API_BASE}/my/messages/unread-count?user_id=${userId}`);
    const data = await res.json();
    unreadCount.value = data.success ? data.unread_count : 0;
  } catch {
    unreadCount.value = 0;
  }
}

async function markAsRead(messageId) {
  try {
    const res = await fetch(`${API_BASE}/my/messages/read`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      const message = messages.value.find(msg => msg.message_id === messageId);
      if (message) {
        message.is_read = true;
        unreadCount.value = Math.max(0, unreadCount.value - 1);
      }
    }
  } catch (e) {
    console.error("标记已读失败:", e);
  }
}

async function deleteMessage(messageId) {
  if (!confirm("确定要删除这条消息吗？")) return;
  
  try {
    const res = await fetch(`${API_BASE}/my/messages/delete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      messages.value = messages.value.filter(msg => msg.message_id !== messageId);
      if (!messages.value.find(msg => msg.message_id === messageId)?.is_read) {
        unreadCount.value = Math.max(0, unreadCount.value - 1);
      }
    }
  } catch (e) {
    console.error("删除消息失败:", e);
  }
}

function switchTab(tab) {
  activeTab.value = tab;
}

function goTo(action) {
  if (action === "home") window.location.href = "/home";
  if (action === "profile") window.location.href = "/profile";
  if (action === "about") window.location.href = "/about";
}

function logout() {
  if (!confirm("确定要退出登录吗？")) return;
  localStorage.removeItem("user_id");
  localStorage.removeItem("username");
  localStorage.removeItem("email");
  window.location.href = "/login";
}

onMounted(() => {
  if (!userId) {
    alert("请先登录");
    window.location.href = "/login";
    return;
  }
  loadMessages();
  loadUnreadCount();
});
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">校园失物招领与位置追踪系统</div>
      <div class="topbar-user">管</div>
    </div>
    <div class="container">
      <div class="sidebar">
        <div class="avatar-container">
          <div class="avatar">👤</div>
          <div>
            <div class="username">消息中心</div>
            <div class="user-id">未读消息: {{ unreadCount }}</div>
          </div>
        </div>

        <div class="nav-buttons">
          <button :class="tabClass('all')" @click="switchTab('all')">全部消息</button>
          <button :class="tabClass('unread')" @click="switchTab('unread')">未读消息</button>
          <button :class="tabClass('system')" @click="switchTab('system')">系统通知</button>
          <button :class="tabClass('claim')" @click="switchTab('claim')">认领通知</button>
          <button :class="tabClass('publish')" @click="switchTab('publish')">发布通知</button>
          <button class="nav-btn" @click="goTo('profile')">返回个人中心</button>
          <button class="nav-btn" @click="goTo('home')">返回主页</button>
        </div>
        <div class="sidebar-footer">
          <a @click="logout">退出登录</a>
          <a @click="goTo('about')">关于我们</a>
        </div>
      </div>

      <div class="main-content">
        <div class="content-panel">
          <div class="panel-header">
            <div class="panel-tab active">{{ activeTab === 'all' ? '全部消息' : activeTab === 'unread' ? '未读消息' : getMessageTypeText(activeTab) }}</div>
            <div class="message-count">共 {{ filteredMessages.length }} 条消息</div>
          </div>
          
          <div class="messages-list">
            <div v-for="message in filteredMessages" :key="message.message_id" 
                 :class="['message-item', { 'unread': !message.is_read }]">
              <div class="message-header">
                <span :class="['message-type', getMessageTypeClass(message.message_type)]">
                  {{ getMessageTypeText(message.message_type) }}
                </span>
                <span class="message-time">{{ formatTime(message.create_time) }}</span>
              </div>
              <div class="message-title">{{ message.title }}</div>
              <div class="message-content">{{ message.content }}</div>
              <div class="message-actions">
                <button v-if="!message.is_read" class="btn-read" @click="markAsRead(message.message_id)">
                  标记已读
                </button>
                <button class="btn-delete" @click="deleteMessage(message.message_id)">
                  删除
                </button>
              </div>
            </div>
            
            <div v-if="filteredMessages.length === 0" class="no-messages">
              <div class="no-messages-icon">📭</div>
              <div class="no-messages-text">暂无消息</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/消息中心.css"></style>