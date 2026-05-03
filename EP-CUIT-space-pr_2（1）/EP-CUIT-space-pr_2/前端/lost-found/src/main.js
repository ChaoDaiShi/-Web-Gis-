import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// ⭐ 全局引入你的原始CSS（关键！）
import './assets/主页.css'

const app = createApp(App)
app.config.devtools = false
app.use(router).mount('#app')