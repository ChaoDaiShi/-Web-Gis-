<script setup>
import { computed, onMounted, ref } from "vue";
import MarkerDetailModal from "../components/MarkerDetailModal.vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");
const activeTab = ref("all");
const messages = ref([]);
const unreadCount = ref(0);
const username = ref("用户名");
const avatarUrl = ref("");
const fromPage = ref("profile");

const showDetailModal = ref(false);
const selectedItem = ref(null);

const selectedMessages = ref(new Set());
const showMenu = ref(false);
const isTrash = ref(false);
const trashMessages = ref([]);

const formatTime = (timeStr) => {
  if (!timeStr) return "未知时间";
  const date = new Date(timeStr.replace(/-/g, '/'));
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

const tabClass = (tab) => {
  if (tab === 'trash') {
    return isTrash.value ? "tab-btn active" : "tab-btn";
  }
  return !isTrash.value && activeTab.value === tab ? "tab-btn active" : "tab-btn";
};

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

async function markAllAsRead() {
  if (!confirm("确定要将所有消息标记为已读吗？")) return;
  
  try {
    const res = await fetch(`${API_BASE}/my/messages/read-all`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      messages.value.forEach(msg => msg.is_read = true);
      unreadCount.value = 0;
    }
  } catch (e) {
    console.error("标记全部已读失败:", e);
  }
}

function toggleSelect(messageId) {
  if (selectedMessages.value.has(messageId)) {
    selectedMessages.value.delete(messageId);
  } else {
    selectedMessages.value.add(messageId);
  }
  selectedMessages.value = new Set(selectedMessages.value);
}

function toggleSelectAll() {
  if (selectedMessages.value.size === filteredMessages.value.length) {
    selectedMessages.value.clear();
  } else {
    filteredMessages.value.forEach(msg => {
      selectedMessages.value.add(msg.message_id);
    });
  }
  selectedMessages.value = new Set(selectedMessages.value);
}

async function markSelectedAsRead() {
  if (selectedMessages.value.size === 0) {
    alert("请先选择消息");
    return;
  }
  
  try {
    for (const messageId of selectedMessages.value) {
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
    }
    selectedMessages.value.clear();
    showMenu.value = false;
  } catch (e) {
    console.error("标记已读失败:", e);
  }
}

async function markSelectedAsUnread() {
  if (selectedMessages.value.size === 0) {
    alert("请先选择消息");
    return;
  }
  
  try {
    for (const messageId of selectedMessages.value) {
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
    }
    selectedMessages.value.clear();
    showMenu.value = false;
  } catch (e) {
    console.error("标记未读失败:", e);
  }
}

async function deleteSelected() {
  if (selectedMessages.value.size === 0) {
    alert("请先选择消息");
    return;
  }
  
  if (!confirm(`确定要删除选中的 ${selectedMessages.value.size} 条消息吗？`)) return;
  
  try {
    for (const messageId of selectedMessages.value) {
      const res = await fetch(`${API_BASE}/my/messages/delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: messageId, user_id: userId })
      });
      const data = await res.json();
      if (data.success) {
        messages.value = messages.value.filter(msg => msg.message_id !== messageId);
      }
    }
    selectedMessages.value.clear();
    showMenu.value = false;
    loadUnreadCount();
  } catch (e) {
    console.error("删除消息失败:", e);
  }
}

function closeMenu() {
  showMenu.value = false;
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

async function toggleTrash() {
  isTrash.value = !isTrash.value;
  selectedMessages.value.clear();
  if (isTrash.value) {
    await loadTrashMessages();
  } else {
    await loadMessages();
  }
}

async function restoreMessage(messageId) {
  try {
    const res = await fetch(`${API_BASE}/my/messages/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: messageId, user_id: userId })
    });
    const data = await res.json();
    if (data.success) {
      trashMessages.value = trashMessages.value.filter(msg => msg.message_id !== messageId);
      loadUnreadCount();
    }
  } catch (e) {
    console.error("恢复消息失败:", e);
  }
}

async function deletePermanently(messageId) {
  if (!confirm("确定要永久删除这条消息吗？此操作不可恢复。")) return;
  
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
    console.error("永久删除失败:", e);
  }
}

function highlightItemName(content) {
  content = content.replace(/您的「物品ID：\d+，物品名：(.+?)」认领申请已/g, '您的<span style="color: #3b82f6; font-weight: bold; font-size: 1.1em;">$1</span>认领申请已');
  content = content.replace(/您的「物品ID：\d+，物品名：(.+?)」归还申请已/g, '您的<span style="color: #28a745; font-weight: bold; font-size: 1.1em;">$1</span>归还申请已');
  return content;
}

function extractItemId(content) {
  const match = content.match(/物品ID：(\d+)/);
  return match ? match[1] : null;
}

async function viewItem(message) {
  const content = message.content;
  const itemIdMatch = content.match(/物品ID：(\d+)/);
  if (!itemIdMatch) {
    alert("无法获取物品信息");
    return;
  }
  
  const itemId = itemIdMatch[1];
  
  try {
    const res = await fetch(`${API_BASE}/map/markers`);
    const data = await res.json();
    
    if (data.success && data.data) {
      const item = data.data.find(item => String(item.item_id) === String(itemId));
      
      if (item) {
        selectedItem.value = {
          id: item.item_id,
          title: item.title,
          detail: item.description,
          status: item.status,
          time: item.create_time,
          images: item.image_urls ? (Array.isArray(item.image_urls) ? item.image_urls : []) : [],
          type: item.type,
          publisher_id: item.publisher_id,
          lng: item.lng,
          lat: item.lat
        };
        showDetailModal.value = true;
      } else {
        alert("未找到该物品");
      }
    }
  } catch (e) {
    console.error("加载物品详情失败:", e);
    alert("加载物品详情失败");
  }
}

function closeDetailModal() {
  showDetailModal.value = false;
  selectedItem.value = null;
}

async function switchTab(tab) {
  if (tab === 'trash') {
    isTrash.value = true;
    await loadTrashMessages();
  } else {
    isTrash.value = false;
    activeTab.value = tab;
    await loadMessages();
  }
  selectedMessages.value.clear();
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
    <div class="topbar">
      <div class="topbar-title">校园失物招领与位置追踪系统</div>
      <div class="topbar-user">
        <img v-if="avatarUrl" :src="avatarUrl" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;" />
        <span v-else>{{ username.charAt(0) || '管' }}</span>
      </div>
    </div>
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
          <button :class="tabClass('return')" @click="switchTab('return')">归还通知</button>
          <button :class="tabClass('publish')" @click="switchTab('publish')">发布通知</button>
          <button :class="tabClass('trash')" @click="switchTab('trash')">🗑️ 回收站</button>
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
            <div class="menu-container">
              <button class="menu-btn" @click.stop="showMenu = !showMenu">
                管理
                <span class="menu-arrow">▼</span>
              </button>
              <div v-if="showMenu" class="dropdown-menu" @click.stop>
                <div class="menu-item" @click="toggleSelectAll">
                  <span>{{ selectedMessages.size === filteredMessages.length && filteredMessages.length > 0 ? '取消全选' : '全选消息' }}</span>
                </div>
                <div class="menu-divider"></div>
                <div class="menu-item" @click="markSelectedAsRead">标记已读</div>
                <div class="menu-item" @click="markSelectedAsUnread">标记未读</div>
                <div class="menu-item danger" @click="deleteSelected">删除</div>
              </div>
            </div>
            <div class="message-count">共 {{ filteredMessages.length }} 条消息</div>
            <span v-if="selectedMessages.size > 0" class="selected-count">已选择 {{ selectedMessages.size }} 条</span>
          </div>
          
          <div class="messages-list">
            <template v-if="!isTrash">
              <div v-for="message in filteredMessages" :key="message.message_id" 
                   :class="['message-item', { 'unread': !message.is_read, 'selected': selectedMessages.has(message.message_id) }]"
                   @click="viewItem(message)">
                <input type="checkbox" 
                       :checked="selectedMessages.has(message.message_id)" 
                       @click.stop="toggleSelect(message.message_id)"
                       class="message-checkbox" />
                <div class="message-content-wrapper">
                  <div class="message-header">
                    <span :class="['message-type', getMessageTypeClass(message.message_type)]">
                      {{ getMessageTypeText(message.message_type) }}
                    </span>
                    <span class="message-time">{{ formatTime(message.create_time) }}</span>
                  </div>
                  <div class="message-title">{{ message.title }}</div>
                  <div class="message-content" v-html="highlightItemName(message.content)"></div>
                  <div class="message-footer">
                    <div class="message-item-id" v-if="extractItemId(message.content)">
                      物品ID: {{ extractItemId(message.content) }}
                    </div>
                    <div class="message-actions">
                      <button v-if="!message.is_read" class="btn-read" @click.stop="markAsRead(message.message_id)">
                        标记已读
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="filteredMessages.length === 0" class="no-messages">
                <div class="no-messages-icon">📭</div>
                <div class="no-messages-text">暂无消息</div>
              </div>
            </template>
            
            <template v-else>
              <div v-for="message in trashMessages" :key="message.message_id" 
                   :class="['message-item', 'trash-item']">
                <div class="message-content-wrapper">
                  <div class="message-header">
                    <span :class="['message-type', getMessageTypeClass(message.message_type)]">
                      {{ getMessageTypeText(message.message_type) }}
                    </span>
                    <span class="message-time">删除于 {{ formatTime(message.delete_time) }}</span>
                  </div>
                  <div class="message-title">{{ message.title }}</div>
                  <div class="message-content" v-html="highlightItemName(message.content)"></div>
                  <div class="message-footer">
                    <div class="message-item-id" v-if="extractItemId(message.content)">
                      物品ID: {{ extractItemId(message.content) }}
                    </div>
                    <div class="message-actions">
                      <button class="btn-restore" @click.stop="restoreMessage(message.message_id)">
                        恢复
                      </button>
                      <button class="btn-delete" @click.stop="deletePermanently(message.message_id)">
                        永久删除
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="trashMessages.length === 0" class="no-messages">
                <div class="no-messages-icon">🗑️</div>
                <div class="no-messages-text">回收站为空</div>
                <div class="no-messages-hint">删除的消息会在此保留15天</div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>

  <MarkerDetailModal
    :show="showDetailModal"
    :marker="selectedItem"
    :disableActions="true"
    @close="closeDetailModal"
  />
</template>

<style scoped src="../assets/消息中心.css"></style>