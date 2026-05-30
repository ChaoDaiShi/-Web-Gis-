<script setup>
import { RouterView } from 'vue-router'
import { ref, onMounted } from 'vue'
import Toast from './components/Toast.vue'
import toastManager from './utils/toastManager'

const currentToast = ref(null)
const showToast = ref(false)

function handleToastClose() {
  showToast.value = false
  setTimeout(() => {
    currentToast.value = null
    toastManager.close()
  }, 300)
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
</template>

<style scoped>
</style>
