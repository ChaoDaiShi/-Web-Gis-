import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import './assets/base.css'
import './assets/main.css'
import './assets/主页.css'

const app = createApp(App)

app.config.devtools = false

app.config.globalProperties.$showToast = function(message, type = 'info') {
  const toast = document.createElement('div')
  toast.className = 'global-toast'
  
  const iconMap = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  }
  
  const colorMap = {
    success: '#22c55e',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6'
  }
  
  toast.innerHTML = `
    <style>
      .global-toast {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 24px;
        background: rgba(0, 0, 0, 0.85);
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        color: #fff;
        font-size: 16px;
        z-index: 9999;
        animation: toastFadeIn 0.3s ease;
        min-width: 200px;
        max-width: 400px;
      }
      .global-toast.fade-out {
        animation: toastFadeOut 0.3s ease forwards;
      }
      .global-toast-icon {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 16px;
        background: ${colorMap[type]};
      }
      @keyframes toastFadeIn {
        from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
        to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
      }
      @keyframes toastFadeOut {
        from { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        to { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
      }
    </style>
    <div class="global-toast-icon">${iconMap[type]}</div>
    <div>${message}</div>
  `
  
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.classList.add('fade-out')
    setTimeout(() => toast.remove(), 300)
  }, 1500)
}

app.use(router).mount('#app')

window.showToast = function(message, type = 'info') {
  const toast = document.createElement('div')
  toast.className = 'global-toast'
  
  const iconMap = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  }
  
  const colorMap = {
    success: '#22c55e',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6'
  }
  
  toast.innerHTML = `
    <style>
      .global-toast {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 24px;
        background: rgba(0, 0, 0, 0.85);
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        color: #fff;
        font-size: 16px;
        z-index: 9999;
        animation: toastFadeIn 0.3s ease;
        min-width: 200px;
        max-width: 400px;
      }
      .global-toast.fade-out {
        animation: toastFadeOut 0.3s ease forwards;
      }
      .global-toast-icon {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 16px;
        background: ${colorMap[type]};
      }
      @keyframes toastFadeIn {
        from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
        to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
      }
      @keyframes toastFadeOut {
        from { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        to { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
      }
    </style>
    <div class="global-toast-icon">${iconMap[type]}</div>
    <div>${message}</div>
  `
  
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.classList.add('fade-out')
    setTimeout(() => toast.remove(), 300)
  }, 1500)
}