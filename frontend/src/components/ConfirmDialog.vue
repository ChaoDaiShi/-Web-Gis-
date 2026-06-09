<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  title: {
    type: String,
    default: '确认操作'
  },
  message: {
    type: String,
    default: '确定要执行此操作吗？'
  },
  confirmText: {
    type: String,
    default: '确定'
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  type: {
    type: String,
    default: 'warning'
  }
})

const emit = defineEmits(['confirm', 'cancel', 'update:visible'])

const localVisible = ref(props.visible)

watch(() => props.visible, (newVal) => {
  localVisible.value = newVal
})

watch(localVisible, (newVal) => {
  emit('update:visible', newVal)
})

function handleConfirm() {
  emit('confirm')
  localVisible.value = false
}

function handleCancel() {
  emit('cancel')
  localVisible.value = false
}
</script>

<template>
  <Teleport to="body">
    <div v-if="localVisible" class="confirm-dialog-overlay">
      <div class="confirm-dialog">
        <div class="dialog-header" :class="type">
          <span class="dialog-icon">
            <template v-if="type === 'warning'">⚠️</template>
            <template v-else-if="type === 'danger'">🔴</template>
            <template v-else-if="type === 'success'">✅</template>
            <template v-else>ℹ️</template>
          </span>
          <h3 class="dialog-title">{{ title }}</h3>
        </div>
        <div class="dialog-body">
          <p class="dialog-message">{{ message }}</p>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-cancel" @click="handleCancel">{{ cancelText }}</button>
          <button class="btn btn-confirm" :class="type" @click="handleConfirm">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.confirm-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.confirm-dialog {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.dialog-header.warning {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
}

.dialog-header.danger {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
}

.dialog-header.success {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
}

.dialog-icon {
  font-size: 24px;
}

.dialog-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.dialog-body {
  padding: 20px;
}

.dialog-message {
  margin: 0;
  font-size: 15px;
  color: #555;
  line-height: 1.6;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: #f8f9fa;
  border-top: 1px solid #eee;
}

.btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #e9ecef;
  color: #495057;
}

.btn-cancel:hover {
  background: #dee2e6;
}

.btn-confirm {
  color: white;
}

.btn-confirm.warning {
  background: #ffc107;
}

.btn-confirm.warning:hover {
  background: #e0a800;
}

.btn-confirm.danger {
  background: #dc3545;
}

.btn-confirm.danger:hover {
  background: #c82333;
}

.btn-confirm.success {
  background: #28a745;
}

.btn-confirm.success:hover {
  background: #218838;
}

.btn-confirm.info {
  background: #17a2b8;
}

.btn-confirm.info:hover {
  background: #138496;
}
</style>