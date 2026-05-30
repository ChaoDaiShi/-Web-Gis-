import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import toastManager from './utils/toastManager'

import './assets/base.css'
import './assets/main.css'
import './assets/主页.css'

const app = createApp(App)

app.config.devtools = false

// 全局属性 - 使用新的 toastManager
app.config.globalProperties.$showToast = function(message, type = 'info') {
  toastManager.show(message, type)
}

app.use(router).mount('#app')

// 全局函数
window.showToast = function(message, type = 'info') {
  toastManager.show(message, type)
}
