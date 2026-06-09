<!-- 聊天界面 -->
<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from "vue";
import AppTopBar from "../components/AppTopBar.vue";
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();
const showToast = window.showToast;
const API_BASE = "http://127.0.0.1:5000/api";

const currentUserId = localStorage.getItem("user_id");
const currentUsername = localStorage.getItem("username");

const viewMode = ref("list"); // list | chat
const conversations = ref([]);
const messages = ref([]);
const friendId = ref(null);
const friendName = ref("");
const friendAvatar = ref("");
const newMessage = ref("");
const messagesContainer = ref(null);
const loading = ref(false);

let pollingInterval = null;

async function loadConversations() {
  try {
    const res = await fetch(`${API_BASE}/chat/conversations?user_id=${currentUserId}`);
    const data = await res.json();
    conversations.value = data.success ? data.data || [] : [];
  } catch (e) {
    console.error("加载会话列表失败:", e);
  }
}

async function loadMessages() {
  if (!friendId.value) return;
  
  try {
    const res = await fetch(`${API_BASE}/chat/messages/${friendId.value}?user_id=${currentUserId}`);
    const data = await res.json();
    messages.value = data.success ? data.data || [] : [];
    
    await nextTick();
    scrollToBottom();
  } catch (e) {
    console.error("加载消息失败:", e);
  }
}

function openConversation(conv) {
  friendId.value = conv.friend_id;
  friendName.value = conv.username;
  friendAvatar.value = conv.avatar;
  viewMode.value = "chat";
  loadMessages();
  
  // 开始轮询新消息
  startPolling();
}

function startPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
  pollingInterval = setInterval(() => {
    loadMessages();
  }, 3000);
}

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

async function sendMessage() {
  if (!newMessage.value.trim() || !friendId.value) return;
  
  const content = newMessage.value.trim();
  newMessage.value = "";
  
  try {
    const res = await fetch(`${API_BASE}/chat/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: currentUserId,
        receiver_id: friendId.value,
        content: content,
        message_type: "text"
      })
    });
    
    const data = await res.json();
    if (data.success) {
      loadMessages();
    } else {
      showToast(data.message || "发送失败", "error");
    }
  } catch (e) {
    console.error("发送消息失败:", e);
    showToast("发送失败", "error");
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function goBack() {
  if (viewMode.value === "chat") {
    viewMode.value = "list";
    friendId.value = null;
    friendName.value = "";
    friendAvatar.value = "";
    stopPolling();
  } else {
    router.back();
  }
}

function formatTime(time) {
  if (!time) return "";
  const date = new Date(time);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return "刚刚";
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  
  return time.substring(5, 16);
}

function handleKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

onMounted(() => {
  if (!currentUserId) {
    showToast("请先登录", "warning");
    router.push("/login");
    return;
  }
  
  // 检查是否直接打开与某人的聊天
  const targetId = route.params.id;
  if (targetId) {
    friendId.value = parseInt(targetId);
    // 获取对方信息
    fetch(`${API_BASE}/user/${targetId}/profile`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          friendName.value = data.data.username;
          friendAvatar.value = data.data.avatar;
          viewMode.value = "chat";
          loadMessages();
          startPolling();
        }
      });
  } else {
    loadConversations();
  }
});

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <div class="chat-page">
    <AppTopBar variant="inner" />
    
    <!-- 会话列表 -->
    <div v-if="viewMode === 'list'" class="conversations-container">
      <div class="header">
        <button @click="goBack" class="back-btn">← 返回</button>
        <h2>消息</h2>
      </div>
      
      <div class="conversation-list">
        <div 
          v-for="conv in conversations" 
          :key="conv.conversation_id" 
          class="conversation-item"
          @click="openConversation(conv)"
        >
          <div class="avatar-wrapper">
            <img v-if="conv.avatar" :src="conv.avatar" class="avatar" />
            <div v-else class="avatar-placeholder">👤</div>
            <span v-if="conv.unread_count > 0" class="unread-badge">{{ conv.unread_count }}</span>
          </div>
          
          <div class="conversation-info">
            <div class="top-row">
              <span class="name">{{ conv.username }}</span>
              <span class="time">{{ formatTime(conv.last_message_time) }}</span>
            </div>
            <div class="last-message">
              {{ conv.last_message_type === 'text' ? conv.last_message : '[图片]' }}
            </div>
          </div>
        </div>
        
        <div v-if="conversations.length === 0" class="empty">
          <p>暂无会话</p>
          <p class="hint">与他人互动后可在此聊天</p>
        </div>
      </div>
    </div>
    
    <!-- 聊天界面 -->
    <div v-if="viewMode === 'chat'" class="chat-container">
      <div class="chat-header">
        <button @click="goBack" class="back-btn">← 返回</button>
        <div class="friend-info">
          <img v-if="friendAvatar" :src="friendAvatar" class="avatar-small" />
          <span class="friend-name">{{ friendName }}</span>
        </div>
        <button @click="router.push(`/user/${friendId}`)" class="profile-btn">👤</button>
      </div>
      
      <div class="messages-container" ref="messagesContainer">
        <div 
          v-for="msg in messages" 
          :key="msg.message_id" 
          :class="['message', msg.is_mine ? 'mine' : 'other']"
        >
          <div class="message-content">
            {{ msg.content }}
          </div>
          <div class="message-time">{{ formatTime(msg.created_at) }}</div>
        </div>
        
        <div v-if="messages.length === 0" class="empty-messages">
          <p>暂无消息</p>
          <p class="hint">发送消息开始聊天</p>
        </div>
      </div>
      
      <div class="input-area">
        <textarea 
          v-model="newMessage" 
          placeholder="输入消息..." 
          @keydown="handleKeydown"
          rows="1"
        ></textarea>
        <button @click="sendMessage" class="send-btn">发送</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  min-height: 100vh;
  background: #f5f5f5;
}

/* 会话列表样式 */
.conversations-container {
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

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conversation-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: #f0f0f0;
}

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
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

.unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ff4d4f;
  color: white;
  font-size: 12px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.conversation-info {
  flex: 1;
  overflow: hidden;
}

.top-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.name {
  font-weight: 500;
  color: #333;
}

.time {
  font-size: 12px;
  color: #999;
}

.last-message {
  font-size: 14px;
  color: #888;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

/* 聊天界面样式 */
.chat-container {
  max-width: 600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
}

.chat-header {
  background: white;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid #eee;
}

.friend-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-small {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.friend-name {
  font-weight: 500;
}

.profile-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f5;
}

.message {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}

.message.mine {
  align-items: flex-end;
}

.message.other {
  align-items: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  word-break: break-word;
}

.message.mine .message-content {
  background: #1890ff;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.other .message-content {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}

.empty-messages {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.input-area {
  background: white;
  padding: 12px 20px;
  display: flex;
  gap: 12px;
  border-top: 1px solid #eee;
}

.input-area textarea {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  resize: none;
  max-height: 100px;
  line-height: 1.4;
}

.input-area textarea:focus {
  outline: none;
  border-color: #1890ff;
}

.send-btn {
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0 20px;
  cursor: pointer;
  font-size: 14px;
}

.send-btn:hover {
  background: #40a9ff;
}
</style>
