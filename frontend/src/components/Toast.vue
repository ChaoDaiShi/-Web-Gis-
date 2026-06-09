<!-- 提示组件 -->
<script setup>
import { defineProps, defineEmits, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  message: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
  },
  visible: {
    type: Boolean,
    default: false
  },
  autoClose: {
    type: Boolean,
    default: true
  },
  duration: {
    type: Number,
    default: 3000
  }
})

const emit = defineEmits(['close'])

let timer = null

function close() {
  emit('close')
}

function startTimer() {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
  
  if (props.visible && props.autoClose) {
    timer = setTimeout(() => {
      close()
    }, props.duration)
  }
}

function clearTimer() {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    startTimer()
  } else {
    clearTimer()
  }
})

onMounted(() => {
  if (props.visible && props.autoClose) {
    startTimer()
  }
})

onUnmounted(() => {
  clearTimer()
})
</script>

<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" class="toast-overlay" @click="close">
        <div class="toast-container" @click.stop>
          <div class="toast-content">
            <div class="toast-icon" :class="type">
              <span v-if="type === 'success'">✓</span>
              <span v-else-if="type === 'error'">✗</span>
              <span v-else-if="type === 'warning'">⚠</span>
              <span v-else>ℹ</span>
            </div>
            <div class="toast-message">{{ message }}</div>
          </div>
          <button v-if="!autoClose" class="toast-button" @click="close">确定</button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.toast-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  pointer-events: none;
}

.toast-overlay > .toast-container {
  pointer-events: auto;
}

.toast-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 20px;
  padding: 24px 28px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15),
              0 8px 25px rgba(0, 0, 0, 0.1),
              0 0 0 1px rgba(0, 0, 0, 0.05);
  color: #1f2937;
  font-size: 16px;
  min-width: 280px;
  max-width: 420px;
  animation: toastPopIn 0.3s ease;
}

@keyframes toastPopIn {
  0% {
    opacity: 0;
    transform: scale(0.9) translateY(-10px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.toast-content {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.toast-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 20px;
  flex-shrink: 0;
}

.toast-icon.success {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: #fff;
}

.toast-icon.error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: #fff;
}

.toast-icon.warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fff;
}

.toast-icon.info {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
}

.toast-message {
  flex: 1;
  font-size: 15px;
  line-height: 1.6;
  color: #374151;
  padding-top: 6px;
}

.toast-button {
  align-self: flex-end;
  padding: 10px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.toast-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.35);
}

.toast-button:active {
  transform: translateY(0);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(-10px);
}

.toast-enter-to,
.toast-leave-from {
  opacity: 1;
  transform: scale(1) translateY(0);
}
</style>
