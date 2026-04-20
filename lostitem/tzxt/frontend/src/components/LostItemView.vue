<template>
  <div class="lost-item-view">
    <div class="header-actions">
      <h2>失物列表</h2>
      <button @click="showCreateForm = true" class="btn-create">发布失物</button>
    </div>

    <div v-if="showCreateForm" class="modal">
      <div class="modal-content">
        <h3>发布失物</h3>
        <form @submit.prevent="createLostItem">
          <div class="form-group">
            <label>标题</label>
            <input v-model="newItem.title" required />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="newItem.description"></textarea>
          </div>
          <div class="form-group">
            <label>地点</label>
            <input v-model="newItem.location" required />
          </div>
          <div class="form-group">
            <label>类别</label>
            <input v-model="newItem.category" />
          </div>
          <div class="form-actions">
            <button type="submit" class="btn-submit">发布</button>
            <button type="button" @click="showCreateForm = false" class="btn-cancel">取消</button>
          </div>
        </form>
      </div>
    </div>

    <div class="lost-items-grid">
      <div v-for="item in lostItems" :key="item.id" class="lost-item-card">
        <h3>{{ item.title }}</h3>
        <p>{{ item.description }}</p>
        <div class="item-info">
          <span>📍 {{ item.location }}</span>
          <span>🏷️ {{ item.category }}</span>
        </div>
        <div class="item-status" :class="item.status">
          {{ getStatusText(item.status) }}
        </div>
      </div>
    </div>

    <div v-if="lostItems.length === 0" class="empty-state">
      <p>暂无失物信息</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { lostItemAPI } from '../api'

const props = defineProps({
  userId: {
    type: Number,
    required: true
  }
})

const lostItems = ref([])
const showCreateForm = ref(false)
const newItem = ref({
  title: '',
  description: '',
  location: '',
  category: ''
})

const fetchLostItems = async () => {
  try {
    const response = await lostItemAPI.getAll()
    lostItems.value = response.data.lost_items
  } catch (error) {
    console.error('获取失物列表失败:', error)
  }
}

const createLostItem = async () => {
  try {
    const data = {
      ...newItem.value,
      owner_id: props.userId
    }
    await lostItemAPI.create(data)
    showCreateForm.value = false
    newItem.value = { title: '', description: '', location: '', category: '' }
    fetchLostItems()
  } catch (error) {
    console.error('创建失物失败:', error)
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'lost': '寻找中',
    'claimed': '已认领'
  }
  return statusMap[status] || status
}

onMounted(() => {
  fetchLostItems()
})
</script>

<style scoped>
.lost-item-view {
  max-width: 1000px;
  margin: 0 auto;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn-create {
  padding: 10px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  width: 400px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-submit {
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel {
  padding: 8px 16px;
  background: #999;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.lost-items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.lost-item-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.lost-item-card h3 {
  margin-bottom: 10px;
  color: #333;
}

.lost-item-card p {
  color: #666;
  margin-bottom: 10px;
}

.item-info {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
}

.item-status {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.item-status.lost {
  background: #fff3cd;
  color: #856404;
}

.item-status.claimed {
  background: #d4edda;
  color: #155724;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>