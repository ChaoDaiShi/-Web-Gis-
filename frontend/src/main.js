import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import toastManager from './utils/toastManager'
import { confirmManager } from './utils/toastManager'

import './assets/base.css'
import './assets/main.css'
import './assets/home.css'

const app = createApp(App)

app.config.devtools = false

// 全局属性 - 使用新的 toastManager
app.config.globalProperties.$showToast = function(message, type = 'info') {
  toastManager.show(message, type)
}

app.config.globalProperties.$confirm = function(options) {
  if (typeof options === 'string') {
    return confirmManager.show({ message: options })
  }
  return confirmManager.show(options)
}

app.use(router).mount('#app')

// 全局函数
window.showToast = function(message, type = 'info') {
  toastManager.show(message, type)
}

window.showConfirm = function(options) {
  if (typeof options === 'string') {
    return confirmManager.show({ message: options })
  }
  return confirmManager.show(options)
}