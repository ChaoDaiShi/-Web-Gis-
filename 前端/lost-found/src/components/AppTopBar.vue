<!-- 顶部栏 -->
<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

defineProps({
  variant: {
    type: String,
    default: "inner",
    validator: (v) => ["inner", "home", "admin", "login"].includes(v),
  },
});

const router = useRouter();
const avatarUrl = ref("");
const username = ref("");

async function loadUserInfo() {
  const userId = localStorage.getItem("user_id");
  if (!userId) return;
  
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/profile?user_id=${userId}`);
    const data = await res.json();
    if (data.success && data.data) {
      if (data.data.avatar) {
        avatarUrl.value = `http://127.0.0.1:5000${data.data.avatar}`;
      }
      username.value = data.data.username || "";
    }
  } catch (e) {
    console.error("加载用户信息失败:", e);
  }
}

function goProfile() {
  router.push("/profile");
}

function getInitial() {
  return username.value ? username.value.charAt(0).toUpperCase() : "用";
}

onMounted(() => {
  loadUserInfo();
});
</script>

<template>
  <header :class="['app-topbar', `app-topbar--${variant}`]">
    <div class="app-topbar__logo">
      <img src="/1.jpg" alt="校徽" class="app-topbar__logo-img" />
    </div>
    <component :is="variant === 'home' ? 'h1' : 'div'" class="app-topbar__title">
      校园失物招领与位置追踪系统
    </component>
    <div class="app-topbar__center">
      <slot name="center" />
    </div>
    <div class="app-topbar__right">
      <slot name="actions" />
      <button
        v-if="variant === 'inner'"
        type="button"
        class="app-topbar__avatar app-topbar__avatar--click"
        aria-label="前往个人中心"
        @click="goProfile"
      >
        <img v-if="avatarUrl" :src="avatarUrl" class="app-topbar__avatar-img" />
        <span v-else>{{ getInitial() }}</span>
      </button>
      <span v-else-if="variant === 'admin'" class="app-topbar__avatar" aria-hidden="true">
        <img v-if="avatarUrl" :src="avatarUrl" class="app-topbar__avatar-img" />
        <span v-else>{{ getInitial() }}</span>
      </span>
    </div>
  </header>
</template>

<style scoped>
.app-topbar {
  box-sizing: border-box;
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  gap: 12px;
}

.app-topbar__logo {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-topbar__logo-img {
  width: 48px;
  height: 48px;
  border-radius: 8px;
}

.app-topbar__title {
  margin: 0;
  font-size: clamp(14px, 2vw, 20px);
  color: #333;
  font-weight: 500;
  line-height: 1.2;
  flex-shrink: 0;
}

.app-topbar__center {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 0 20px;
}

.app-topbar__right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.app-topbar__avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #111827;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  border: none;
  box-sizing: border-box;
  overflow: hidden;
}

.app-topbar__avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.app-topbar__avatar--click {
  cursor: pointer;
  transition: transform 0.2s;
}

.app-topbar__avatar--click:hover {
  transform: scale(1.08);
}

/* 内页：与个人中心/修改资料等一致 */
.app-topbar--inner {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

/* 地图主页 */
.app-topbar--home {
  padding: 0 16px;
  background: #33ccff;
}

.app-topbar--home .app-topbar__title {
  font-size: clamp(14px, 1.8vw, 18px);
  color: #1f2937;
}

.app-topbar--home .app-topbar__logo-img {
  width: 44px;
  height: 44px;
}

/* 后台 */
.app-topbar--admin {
  padding: 0 16px;
  background: #33ccff;
}

.app-topbar--admin .app-topbar__title {
  font-size: clamp(14px, 1.8vw, 18px);
  color: #1f2937;
}

.app-topbar--admin .app-topbar__logo-img {
  width: 44px;
  height: 44px;
}

/* 登录页顶栏 */
.app-topbar--login {
  background: #39a9db;
  padding-left: 20px;
}

.app-topbar--login .app-topbar__title {
  color: #fff;
  font-size: 20px;
}

.app-topbar--login .app-topbar__right:empty {
  display: none;
}
</style>
