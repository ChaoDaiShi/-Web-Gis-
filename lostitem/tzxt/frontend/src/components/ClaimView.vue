<template>
  <div class="claim-view">
    <div class="header-actions">
      <h2>认领管理</h2>
    </div>

    <div class="create-claim-form">
      <h3>创建认领申请</h3>
      <div class="form-row">
        <input v-model="newClaim.lostItemId" type="number" placeholder="失物ID" />
        <button @click="createClaim" class="btn-create">提交认领</button>
      </div>
    </div>

    <div class="claims-section">
      <h3>我的认领申请</h3>
      <div class="claims-list">
        <div v-for="claim in myClaims" :key="claim.id" class="claim-item">
          <div class="claim-info">
            <span>失物ID: {{ claim.lost_item_id }}</span>
            <span class="claim-status" :class="claim.status">
              {{ getStatusText(claim.status) }}
            </span>
          </div>
          <p>申请时间: {{ formatTime(claim.created_at) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { claimAPI } from '../api'

const props = defineProps({
  userId: {
    type: Number,
    required: true
  }
})

const myClaims = ref([])
const newClaim = ref({
  lostItemId: ''
})

const fetchMyClaims = async () => {
  try {
    const response = await claimAPI.getByUser(props.userId)
    myClaims.value = response.data.claims
  } catch (error) {
    console.error('获取认领申请失败:', error)
  }
}

const createClaim = async () => {
  if (!newClaim.value.lostItemId) return

  try {
    await claimAPI.create({
      lost_item_id: parseInt(newClaim.value.lostItemId),
      claimer_id: props.userId
    })
    newClaim.value.lostItemId = ''
    fetchMyClaims()
  } catch (error) {
    console.error('创建认领申请失败:', error)
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': '待处理',
    'approved': '已通过',
    'rejected': '已拒绝'
  }
  return statusMap[status] || status
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchMyClaims()
})
</script>

<style scoped>
.claim-view {
  max-width: 800px;
  margin: 0 auto;
}

.header-actions {
  margin-bottom: 20px;
}

.create-claim-form {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.form-row {
  display: flex;
  gap: 10px;
}

.form-row input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn-create {
  padding: 10px 20px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.claims-section {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.claims-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.claim-item {
  padding: 15px;
  border: 1px solid #eee;
  border-radius: 4px;
}

.claim-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.claim-status {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
}

.claim-status.pending {
  background: #fff3cd;
  color: #856404;
}

.claim-status.approved {
  background: #d4edda;
  color: #155724;
}

.claim-status.rejected {
  background: #f8d7da;
  color: #721c24;
}
</style>