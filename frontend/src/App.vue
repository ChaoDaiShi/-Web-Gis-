<script setup>
import { RouterView } from 'vue-router'
import { ref, onMounted, onUnmounted } from 'vue'
import Toast from './components/Toast.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import toastManager from './utils/toastManager'
import { confirmManager } from './utils/toastManager'

const currentToast = ref(null)
const showToast = ref(false)
const confirmDialog = ref(null)
let removeConfirmListener = null

function handleToastClose() {
  showToast.value = false
  setTimeout(() => {
    currentToast.value = null
    toastManager.close()
  }, 300)
}

function handleConfirmConfirm() {
  if (confirmDialog.value?.onConfirm) {
    confirmDialog.value.onConfirm()
  }
}

function handleConfirmCancel() {
  if (confirmDialog.value?.onCancel) {
    confirmDialog.value.onCancel()
  }
}

onMounted(() => {
  toastManager.setOnToastUpdate((toast) => {
    if (toast) {
      currentToast.value = toast
      setTimeout(() => {
        showToast.value = true
      }, 50)
    } else {
      showToast.value = false
    }
  })
  
  removeConfirmListener = confirmManager.addListener((confirm) => {
    confirmDialog.value = confirm
  })
})

onUnmounted(() => {
  if (removeConfirmListener) {
    removeConfirmListener()
  }
})
</script>

<template>
  <RouterView />
  <Toast 
    v-if="currentToast" 
    :visible="showToast" 
    :message="currentToast.message" 
    :type="currentToast.type || 'info'"
    @close="handleToastClose"
  />
  <ConfirmDialog
    v-if="confirmDialog"
    :visible="confirmDialog.visible"
    :title="confirmDialog.title"
    :message="confirmDialog.message"
    :confirm-text="confirmDialog.confirmText"
    :cancel-text="confirmDialog.cancelText"
    :type="confirmDialog.type"
    @confirm="handleConfirmConfirm"
    @cancel="handleConfirmCancel"
  />
</template>

<style scoped>
</style>