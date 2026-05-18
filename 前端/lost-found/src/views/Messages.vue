<script setup>
import { computed, onMounted, ref } from "vue";
import AppTopBar from "../components/AppTopBar.vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");
const activeTab = ref("all");
const messages = ref([]);
const trashMessages = ref([]);
const unreadCount = ref(0);
const username = ref("用户名");
const avatarUrl = ref("");
const fromPage = ref("profile");
const showTrash = ref(false);

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
    reminder: "提醒通知",
    return: "归还通知"
  };
  return typeMap[type] || "系统通知";
};

const getMessageTypeClass = (type) => {
  const classMap = {
    system: "type-system",
    claim: "type-claim",
    publish: "type-publish",
    reminder: "type-reminder",
    return: "type-return"
  };
  return classMap[type] || "type-system";
};

const tabClass = (tab) => (activeTab.value === tab ? "tab-btn active" : "tab-btn");

const filteredMessages = computed(() => {
  if (showTrash.value) return trashMessages.value;
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

async function loadTrashMessages() {
  try {
    const res = await fetch(`${API_BASE}/my/messages/trash?user_id=${userId}`);
    const data = await res.json();
    trashMessages.value = data.success ? data.data || [] : [];
  } catch {
    trashMessages.value = [];
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

async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile?user_id=${userId}`);
    const data = await res.json();
    if (data.success && data.data) {
      const user = data.data;
      username.value = user.username || "用户名";
      avatarUrl.value = user.avatar ? `http://127.0.0.1:5000${user.avatar}` : "";
    }
  } catch (e) {
    console.error(e);
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

async function markAsUnread(messageId) {
  try {
    const res = await fetch(`${API_BASE}/my/messages/unread`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      const message = messages.value.find(msg => msg.message_id === messageId);
      if (message) {
        message.is_read = false;
        unreadCount.value++;
      }
    }
  } catch (e) {
    console.error("标记未读失败:", e);
  }
}

async function markAllAsRead() {
  if (!confirm("确定要标记所有消息为已读吗？")) return;
  
  try {
    const res = await fetch(`${API_BASE}/my/messages/read-all`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      messages.value.forEach(msg => {
        msg.is_read = true;
      });
      unreadCount.value = 0;
      alert("已将所有消息标记为已读");
    }
  } catch (e) {
    console.error("标记全部已读失败:", e);
  }
}

async function deleteMessage(messageId) {
  if (!confirm("确定要将这条消息移至回收站吗？")) return;
  
  try {
    const res = await fetch(`${API_BASE}/my/messages/delete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      const message = messages.value.find(msg => msg.message_id === messageId);
      if (message) {
        messages.value = messages.value.filter(msg => msg.message_id !== messageId);
        if (!message.is_read) {
          unreadCount.value = Math.max(0, unreadCount.value - 1);
        }
      }
    }
  } catch (e) {
    console.error("删除消息失败:", e);
  }
}

async function restoreMessage(messageId) {
  if (!confirm("确定要恢复这条消息吗？")) return;
  
  try {
    const res = await fetch(`${API_BASE}/my/messages/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      trashMessages.value = trashMessages.value.filter(msg => msg.message_id !== messageId);
      await loadMessages();
      await loadUnreadCount();
    }
  } catch (e) {
    console.error("恢复消息失败:", e);
  }
}

async function deletePermanently(messageId) {
  if (!confirm("确定要永久删除这条消息吗？此操作不可恢复！")) return;
  
  try {
    const res = await fetch(`${API_BASE}/my/messages/delete-permanently`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      trashMessages.value = trashMessages.value.filter(msg => msg.message_id !== messageId);
    }
  } catch (e) {
    console.error("永久删除消息失败:", e);
  }
}

function switchTab(tab) {
  activeTab.value = tab;
  showTrash.value = false;
}

function toggleTrash() {
  showTrash.value = !showTrash.value;
  if (showTrash.value) {
    loadTrashMessages();
  }
}

function goBack() {
  if (fromPage.value === "home") {
    window.location.href = "/home";
  } else {
    window.location.href = "/profile";
  }
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
  
  const urlParams = new URLSearchParams(window.location.search);
  const from = urlParams.get('from');
  if (from === 'home') {
    fromPage.value = 'home';
  }
  
  loadProfile();
  loadMessages();
  loadUnreadCount();
});
</script>

<template>
  <div>
    <AppTopBar variant="inner" />
    <div class="container">
      <div class="sidebar">
        <div class="avatar-container">
          <div class="avatar">
            <img v-if="avatarUrl" :src="avatarUrl" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;" />
            <span v-else>{{ username.charAt(0) || '👤' }}</span>
          </div>
          <div>
            <div class="username">{{ username }}</div>
            <div class="user-id">消息中心</div>
            <div class="signature">未读消息: {{ unreadCount }}</div>
          </div>
        </div>

        <div class="nav-buttons">
          <button :class="tabClass('all')" @click="switchTab('all')">全部消息</button>
          <button :class="tabClass('unread')" @click="switchTab('unread')">未读消息</button>
          <button :class="tabClass('system')" @click="switchTab('system')">系统通知</button>
          <button :class="tabClass('claim')" @click="switchTab('claim')">认领通知</button>
          <button :class="tabClass('publish')" @click="switchTab('publish')">发布通知</button>
          <button :class="['tab-btn', { active: showTrash }]" @click="toggleTrash">回收站</button>
          <button class="tab-btn" @click="goBack()">返回{{ fromPage === 'home' ? '主页' : '个人中心' }}</button>
        </div>
        <div class="sidebar-footer">
          <a @click="logout">退出登录</a>
          <a @click="goTo('about')">关于我们</a>
        </div>
      </div>

      <div class="main-content">
        <div class="content-panel">
          <div class="panel-header">
            <div class="panel-tab active">
              {{ showTrash ? '回收站' : (activeTab === 'all' ? '全部消息' : activeTab === 'unread' ? '未读消息' : getMessageTypeText(activeTab)) }}
            </div>
            <div class="panel-actions">
              <div class="message-count">共 {{ filteredMessages.length }} 条消息</div>
              <button v-if="!showTrash && messages.length > 0" class="btn-mark-all" @click="markAllAsRead">
                全部标为已读
              </button>
            </div>
          </div>
          
          <div class="messages-list">
            <div v-for="message in filteredMessages" :key="message.message_id" 
                 :class="['message-item', { 'unread': !message.is_read, 'in-trash': showTrash }]">
              <div class="message-header">
                <span :class="['message-type', getMessageTypeClass(message.message_type)]">
                  {{ getMessageTypeText(message.message_type) }}
                </span>
                <span class="message-time">{{ formatTime(showTrash ? message.delete_time : message.create_time) }}</span>
              </div>
              <div class="message-title">{{ message.title }}</div>
              <div class="message-content">{{ message.content }}</div>
              <div class="message-actions">
                <template v-if="showTrash">
                  <button class="btn-restore" @click="restoreMessage(message.message_id)">
                    恢复
                  </button>
                  <button class="btn-delete-permanent" @click="deletePermanently(message.message_id)">
                    永久删除
                  </button>
                </template>
                <template v-else>
                  <button v-if="!message.is_read" class="btn-read" @click="markAsRead(message.message_id)">
                    标记已读
                  </button>
                  <button v-else class="btn-unread" @click="markAsUnread(message.message_id)">
                    标记未读
                  </button>
                  <button class="btn-delete" @click="deleteMessage(message.message_id)">
                    删除
                  </button>
                </template>
              </div>
            </div>
            
            <div v-if="filteredMessages.length === 0" class="no-messages">
              <div class="no-messages-icon">{{ showTrash ? '🗑️' : '📭' }}</div>
              <div class="no-messages-text">{{ showTrash ? '回收站为空' : '暂无消息' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/消息中心.css"></style>
