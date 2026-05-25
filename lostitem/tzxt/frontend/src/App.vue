<template>
  <div class="app-container">
    <header class="app-header">
      <h1>失物招领系统</h1>
      <nav class="nav-tabs">
        <button @click="currentView = 'notifications'" :class="{ active: currentView === 'notifications' }">
          通知中心
        </button>
        <button @click="currentView = 'lost-items'" :class="{ active: currentView === 'lost-items' }">
          失物列表
        </button>
        <button @click="currentView = 'claims'" :class="{ active: currentView === 'claims' }">
          认领管理
        </button>
      </nav>
    </header>

    <main class="app-main">
      <NotificationView v-if="currentView === 'notifications'" :userId="currentUserId" />
      <LostItemView v-else-if="currentView === 'lost-items'" :userId="currentUserId" />
      <ClaimView v-else-if="currentView === 'claims'" :userId="currentUserId" />
    </main>

    <div class="user-selector">
      <label>当前用户ID: </label>
      <input type="number" v-model="currentUserId" @change="switchUser" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import NotificationView from './components/NotificationView.vue'
import LostItemView from './components/LostItemView.vue'
import ClaimView from './components/ClaimView.vue'

const currentView = ref('notifications')
const currentUserId = ref(1)

const switchUser = () => {
  console.log('Switching to user:', currentUserId.value)
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: white;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header h1 {
  color: #333;
  margin-bottom: 15px;
}

.nav-tabs {
  display: flex;
  gap: 10px;
}

.nav-tabs button {
  padding: 10px 20px;
  border: none;
  background: #e0e0e0;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-tabs button.active {
  background: #4CAF50;
  color: white;
}

.app-main {
  flex: 1;
  padding: 20px;
}

.user-selector {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-selector input {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style>