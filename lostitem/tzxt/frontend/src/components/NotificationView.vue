<template>
  <div class="notification-view">
    <div class="header-actions">
      <h2>通知中心</h2>
      <button @click="markAllRead" class="btn-mark-all">标记全部已读</button>
    </div>

    <div class="filter-bar">
      <label>
        <input type="checkbox" v-model="unreadOnly" @change="fetchNotifications" />
        只显示未读
      </label>
    </div>

    <div class="notification-list" v-if="notifications.length > 0">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="notification-item"
        :class="{ unread: !notification.is_read }"
        @click="markAsRead(notification)"
      >
        <div class="notification-icon">{{ getNotificationIcon(notification.type) }}</div>
        <div class="notification-content">
          <h4>{{ notification.title }}</h4>
          <p>{{ notification.content }}</p>
          <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>暂无通知</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { notificationAPI } from '../api'

const props = defineProps({
  userId: {
    type: Number,
    required: true
  }
})

const notifications = ref([])
const unreadOnly = ref(false)

const fetchNotifications = async () => {
  try {
    const response = await notificationAPI.getNotifications(props.userId, unreadOnly.value)
    notifications.value = response.data.notifications
  } catch (error) {
    console.error('获取通知失败:', error)
  }
}

const markAsRead = async (notification) => {
  if (notification.is_read) return
  try {
    await notificationAPI.markAsRead(notification.id)
    notification.is_read = true
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

const markAllRead = async () => {
  try {
    await notificationAPI.markAllAsRead(props.userId)
    notifications.value.forEach(n => n.is_read = true)
  } catch (error) {
    console.error('标记全部已读失败:', error)
  }
}

const getNotificationIcon = (type) => {
  const icons = {
    'lost_item_published': '📢',
    'claim_approved': '✅',
    'item_claimed': '🎉'
  }
  return icons[type] || '📧'
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchNotifications()
})
</script>

<style scoped>
.notification-view {
  max-width: 800px;
  margin: 0 auto;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions h2 {
  color: #333;
}

.btn-mark-all {
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.filter-bar {
  margin-bottom: 20px;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification-item {
  background: white;
  padding: 15px;
  border-radius: 8px;
  display: flex;
  gap: 15px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.notification-item:hover {
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.notification-item.unread {
  border-left: 4px solid #4CAF50;
}

.notification-icon {
  font-size: 24px;
}

.notification-content h4 {
  margin-bottom: 5px;
  color: #333;
}

.notification-content p {
  color: #666;
  margin-bottom: 5px;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>