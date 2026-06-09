<!-- 消息页面 -->
<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";
import MarkerDetailModal from "../components/MarkerDetailModal.vue";

const showToast = window.showToast;
const showConfirm = window.showConfirm;
const API_BASE = "http://127.0.0.1:5000/api";
const router = useRouter();
const userId = localStorage.getItem("user_id");
const activeTab = ref("all");
const messages = ref([]);
const trashMessages = ref([]);
const unreadCount = ref(0);
const username = ref("用户名");
const avatarUrl = ref("");
const bgImage = ref("");
const fromPage = ref("profile");
const showTrash = ref(false);
const showManageMenu = ref(false);
const selectedMessages = ref(new Set());
const showDetailModal = ref(false);
const currentItem = ref(null);
// 系统通知的子分类: all|system|claim|publish|return
const systemSubTab = ref("all");
const showSubTabDropdown = ref(false);

const pageStyle = computed(() => {
  if (bgImage.value) {
    return {
      background: `url(${bgImage.value}) center/cover`,
      minHeight: '100vh'
    };
  }
  return {};
});

const formatTime = (timeStr) => {
  if (!timeStr) return "未知时间";
  const date = new Date(timeStr);
  return date.toLocaleString("zh-CN");
};

const getMessageTypeText = (type) => {
  const typeMap = {
    system: "认证通知",
    claim: "认领通知", 
    publish: "发布通知",
    reminder: "提醒通知",
    return: "归还通知",
    appointment: "预约通知"
  };
  return typeMap[type] || "认证通知";
};

const getMessageTypeClass = (type) => {
  const classMap = {
    system: "type-system",
    claim: "type-claim",
    publish: "type-publish",
    reminder: "type-reminder",
    return: "type-return",
    appointment: "type-appointment"
  };
  return classMap[type] || "type-system";
};

const tabClass = (tab) => (activeTab.value === tab ? "tab-btn active" : "tab-btn");

const filteredMessages = computed(() => {
  if (showTrash.value) return trashMessages.value;
  if (activeTab.value === "all") return messages.value;
  if (activeTab.value === "unread") return messages.value.filter(msg => !msg.is_read);
  if (activeTab.value === "system") {
    // 系统通知包含：system|claim|publish|return|appointment 类型
    if (systemSubTab.value === "all") {
      return messages.value.filter(msg => 
        msg.message_type === 'system' || 
        msg.message_type === 'claim' || 
        msg.message_type === 'publish' || 
        msg.message_type === 'return' ||
        msg.message_type === 'appointment'
      );
    } else {
      // 按子分类过滤
      return messages.value.filter(msg => msg.message_type === systemSubTab.value);
    }
  }
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
      avatarUrl.value = user.avatar ? (user.avatar.startsWith('http') ? user.avatar : `http://127.0.0.1:5000${user.avatar}`) : "";
      bgImage.value = user.bg_image ? (user.bg_image.startsWith('http') ? user.bg_image : `http://127.0.0.1:5000${user.bg_image}`) : "";
      if (bgImage.value) {
        document.body.style.background = `url(${bgImage.value}) center/cover fixed`;
        document.body.style.minHeight = '100vh';
      }
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
  const confirmed = await showConfirm({title: '标记已读', message: '确定要标记所有消息为已读吗？', type: 'info', confirmText: '确认'});
  if (!confirmed) return;
  
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
      showToast("已将所有消息标记为已读", "success");
    }
  } catch (e) {
    console.error("标记全部已读失败:", e);
  }
}

async function deleteMessage(messageId) {
  const confirmed = await showConfirm({title: '移至回收站', message: '确定要将这条消息移至回收站吗？', type: 'warning', confirmText: '确认'});
  if (!confirmed) return;
  
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
  const confirmed = await showConfirm({title: '恢复消息', message: '确定要恢复这条消息吗？', type: 'info', confirmText: '确认'});
  if (!confirmed) return;
  
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
  const confirmed = await showConfirm({title: '永久删除', message: '确定要永久删除这条消息吗？此操作不可恢复！', type: 'danger', confirmText: '永久删除'});
  if (!confirmed) return;
  
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
  if (tab === 'trash') {
    showTrash.value = true;
    loadTrashMessages();
  } else {
    showTrash.value = false;
  }
}

// 下拉菜单相关函数
function toggleSubTabDropdown() {
  showSubTabDropdown.value = !showSubTabDropdown.value;
}

function selectSubTab(tab) {
  systemSubTab.value = tab;
  showSubTabDropdown.value = false;
}

function getSubTabDisplayName() {
  const names = {
    'all': '全部',
    'claim': '认领通知',
    'publish': '发布通知',
    'return': '归还通知'
  };
  return names[systemSubTab.value] || '选择分类';
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

async function logout() {
  const confirmed = await showConfirm({title: '退出登录', message: '确定要退出登录吗？', type: 'warning', confirmText: '退出'});
  if (!confirmed) return;
  localStorage.removeItem("user_id");
  localStorage.removeItem("username");
  localStorage.removeItem("email");
  window.location.href = "/login";
}

function toggleSelectAll() {
  selectedMessages.value.clear();
  if (filteredMessages.value.length > 0) {
    filteredMessages.value.forEach(msg => {
      selectedMessages.value.add(msg.message_id);
    });
  }
}

function cancelSelectAll() {
  selectedMessages.value.clear();
}

function isSelected(messageId) {
  return selectedMessages.value.has(messageId);
}

function toggleSelect(messageId) {
  if (selectedMessages.value.has(messageId)) {
    selectedMessages.value.delete(messageId);
  } else {
    selectedMessages.value.add(messageId);
  }
}

async function deleteSelected() {
  if (selectedMessages.value.size === 0) {
    showToast("请先选择要删除的消息", "warning");
    return;
  }
  
  const confirmed = await showConfirm({title: '批量删除', message: `确定要删除选中的 ${selectedMessages.value.size} 条消息吗？`, type: 'danger', confirmText: '批量删除'});
  if (!confirmed) return;
  
  const ids = Array.from(selectedMessages.value);
  try {
    for (const id of ids) {
      const res = await fetch(`${API_BASE}/my/messages/delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: id, user_id: userId })
      });
      
      const data = await res.json();
      if (data.success) {
        const message = messages.value.find(msg => msg.message_id === id);
        if (message && !message.is_read) {
          unreadCount.value = Math.max(0, unreadCount.value - 1);
        }
        messages.value = messages.value.filter(msg => msg.message_id !== id);
      }
    }
    selectedMessages.value.clear();
    showToast("删除成功", "success");
  } catch (e) {
    console.error("批量删除失败:", e);
    showToast("删除失败", "error");
  }
}

async function markSelectedAsRead() {
  if (selectedMessages.value.size === 0) {
    showToast("请先选择要标记已读的消息", "warning");
    return;
  }
  
  const ids = Array.from(selectedMessages.value);
  try {
    for (const id of ids) {
      const res = await fetch(`${API_BASE}/my/messages/read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: id, user_id: userId })
      });
      
      const data = await res.json();
      if (data.success) {
        const message = messages.value.find(msg => msg.message_id === id);
        if (message && !message.is_read) {
          message.is_read = true;
          unreadCount.value = Math.max(0, unreadCount.value - 1);
        }
      }
    }
    selectedMessages.value.clear();
    showToast("已标记为已读", "success");
  } catch (e) {
    console.error("批量标记已读失败:", e);
    showToast("标记失败", "error");
  }
}

async function restoreSelected() {
  if (selectedMessages.value.size === 0) {
    showToast("请先选择要恢复的消息", "warning");
    return;
  }
  
  const ids = Array.from(selectedMessages.value);
  try {
    for (const id of ids) {
      const res = await fetch(`${API_BASE}/my/messages/restore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_id: id, user_id: userId })
      });
      
      const data = await res.json();
      if (data.success) {
        trashMessages.value = trashMessages.value.filter(msg => msg.message_id !== id);
      }
    }
    selectedMessages.value.clear();
    await loadMessages();
    showToast("已恢复选中的消息", "success");
  } catch (e) {
    console.error("批量恢复失败:", e);
    showToast("恢复失败", "error");
  }
}

async function deleteSelectedPermanently() {
  if (selectedMessages.value.size === 0) {
    showToast("请先选择要永久删除的消息", "warning");
    return;
  }
  
  const confirmed = await showConfirm({title: '批量永久删除', message: '确定要永久删除选中的消息吗？此操作不可恢复！', type: 'danger', confirmText: '批量永久删除'});
  if (!confirmed) return;
  
  const ids = Array.from(selectedMessages.value);
  try {
    const res = await fetch(`${API_BASE}/my/messages/delete-permanently`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_ids: ids, user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      selectedMessages.value.clear();
      await loadMessages();
      showToast("已永久删除选中的消息", "success");
    } else {
      showToast("删除失败: " + (data.message || "未知错误"), "error");
    }
  } catch (e) {
    console.error("批量永久删除失败:", e);
    showToast("删除失败", "error");
  }
}

function toggleManageMenu() {
  showManageMenu.value = !showManageMenu.value;
}

function closeAllDropdowns() {
  showManageMenu.value = false;
  showSubTabDropdown.value = false;
}

function closeManageMenu() {
  closeAllDropdowns();
}

function extractItemId(content) {
  const match = content.match(/物品ID\s*[：:]\s*(\d+)/);
  return match ? match[1] : null;
}

async function handleMessageClick(message) {
  // 如果是预约消息，跳转到预约页面
  if (message.message_type === 'appointment' && message.related_id) {
    markAsRead(message.message_id);
    router.push('/appointments');
    return;
  }
  
  const itemId = extractItemId(message.content);
  if (!itemId) {
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/lost-items/${itemId}`);
    const data = await res.json();
    if (data.success && data.data) {
      currentItem.value = data.data;
      showDetailModal.value = true;
    }
  } catch (e) {
    console.error('获取物品详情失败:', e);
  }
}

function closeDetailModal() {
  showDetailModal.value = false;
  currentItem.value = null;
}

onMounted(() => {
  if (!userId) {
    showToast("请先登录", "warning");
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
  <div :style="pageStyle">
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
          <button :class="tabClass('trash')" @click="switchTab('trash')">回收站</button>
          <button class="tab-btn" @click="goBack()">返回</button>
        </div>
        <div class="sidebar-footer">
          <a @click="logout">退出登录</a>
          <a @click="goTo('about')">关于我们</a>
        </div>
      </div>

      <div class="main-content">
        <div class="content-panel">
          <div class="panel-header">
            <!-- 系统通知的子分类按钮 -->
            <div v-if="activeTab === 'system'" class="sub-tabs">
              <div class="sub-tab-dropdown">
                <button 
                  :class="['sub-tab-btn', 'active']" 
                  @click.stop="toggleSubTabDropdown"
                >
                  {{ getSubTabDisplayName() }}
                  <span class="dropdown-arrow">▼</span>
                </button>
                <div v-show="showSubTabDropdown" class="sub-tab-dropdown-menu" @click.stop>
                  <button class="dropdown-item" @click="selectSubTab('all')">全部</button>
                  <button class="dropdown-item" @click="selectSubTab('claim')">认领通知</button>
                  <button class="dropdown-item" @click="selectSubTab('publish')">发布通知</button>
                  <button class="dropdown-item" @click="selectSubTab('return')">归还通知</button>
                </div>
              </div>
            </div>
            <div class="panel-actions">
              <div class="message-count">共 {{ filteredMessages.length }} 条消息</div>
              <div v-if="filteredMessages.length > 0 && !showTrash" class="manage-dropdown">
                <button class="manage-btn" @click.stop="toggleManageMenu">
                  管理
                  <span class="dropdown-arrow">▼</span>
                </button>
                <div v-show="showManageMenu" class="dropdown-menu" @click.stop>
                  <button class="dropdown-item" @click="toggleSelectAll">全选消息</button>
                  <button class="dropdown-item" @click="cancelSelectAll">取消全选</button>
                  <div class="dropdown-divider"></div>
                  <button class="dropdown-item" @click="markSelectedAsRead">全部已读</button>
                  <button class="dropdown-item delete" @click="deleteSelected">删除</button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="messages-list" @click="closeAllDropdowns">
            <div v-for="message in filteredMessages" :key="message.message_id" 
                 :class="['message-item', { 'unread': !message.is_read, 'in-trash': showTrash, 'selected': !showTrash && isSelected(message.message_id) }]"
                 @click="handleMessageClick(message)">
              <input v-if="!showTrash" type="checkbox" :checked="isSelected(message.message_id)" @click.stop="toggleSelect(message.message_id)" class="message-checkbox" />
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
                  <button class="btn-restore" @click.stop="restoreMessage(message.message_id)">
                    恢复
                  </button>
                  <button class="btn-delete-permanent" @click.stop="deletePermanently(message.message_id)">
                    永久删除
                  </button>
                </template>
                <template v-else>
                  <button v-if="!message.is_read" class="btn-read" @click.stop="markAsRead(message.message_id)">
                    标记已读
                  </button>
                  <button v-else class="btn-unread" @click.stop="markAsUnread(message.message_id)">
                    标记未读
                  </button>
                  <button class="btn-delete" @click.stop="deleteMessage(message.message_id)">
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
    
    <MarkerDetailModal 
      :show="showDetailModal" 
      :marker="currentItem" 
      :show-action-buttons="false"
      :show-locate-button="false"
      @close="closeDetailModal" 
    />
  </div>
</template>

<style scoped src="../assets/messages-center.css"></style>
