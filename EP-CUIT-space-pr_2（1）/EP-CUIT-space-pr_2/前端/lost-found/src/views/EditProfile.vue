<script setup>
import { onMounted, ref } from "vue";

const userId = localStorage.getItem("user_id");
const username = ref("");
const signature = ref("");
const bio = ref("");
const email = ref("");
const avatar = ref("");
const verifyCode = ref("");
const successMsg = ref(false);
const sendText = ref("获取验证码");
const sendDisabled = ref(false);
let countdown = 0;
let timer = null;

function goProfile() {
  window.location.href = "/profile";
}

function goHome() {
  window.location.href = "/home";
}

function loadUser() {
  const u = {
    username: localStorage.getItem("username") || "",
    email: localStorage.getItem("email") || "",
  };
  username.value = u.username;
  email.value = u.email;
}

function changeAvatar() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*";
  input.onchange = () => {
    const file = input.files?.[0];
    if (!file) return;
    avatar.value = URL.createObjectURL(file);
  };
  input.click();
}

function sendCode() {
  if (countdown > 0) return;
  countdown = 60;
  sendDisabled.value = true;
  sendText.value = `${countdown}秒后重试`;
  timer = setInterval(() => {
    countdown -= 1;
    if (countdown > 0) sendText.value = `${countdown}秒后重试`;
    else {
      clearInterval(timer);
      sendDisabled.value = false;
      sendText.value = "获取验证码";
    }
  }, 1000);
  alert("验证码已发送，请查收短信");
}

function cancelEdit() {
  if (confirm("确定要取消修改吗？未保存的内容将丢失。")) goProfile();
}

function submitEdit() {
  if (!username.value.trim()) {
    alert("请输入用户名");
    return;
  }
  localStorage.setItem("username", username.value.trim());
  localStorage.setItem("email", email.value.trim());
  successMsg.value = true;
  setTimeout(() => goProfile(), 1200);
}

onMounted(() => {
  if (!userId) {
    alert("请先登录");
    window.location.href = "/login";
    return;
  }
  loadUser();
});
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">校园失物招领与位置追踪系统</div>
      <div class="topbar-user" @click="goProfile">管</div>
    </div>
    <div class="container">
      <div class="action-bar">
        <button class="btn" @click="goProfile">返回个人中心</button>
        <button class="btn btn-primary" @click="goHome">返回主页</button>
      </div>
      <div class="content-card">
        <h1 class="card-title">修改个人资料</h1>
        <div v-show="successMsg" class="success-msg">个人资料修改成功！</div>
        <h2 class="section-title">基础设置</h2>
        <div class="avatar-section">
          <div class="avatar">
            <img v-if="avatar" :src="avatar" style="width: 100%; border-radius: 50%" />
            <span v-else>👤</span>
          </div>
          <div class="avatar-info">
            <h3>个人头像</h3>
            <p>支持 JPG、PNG 格式，文件大小不超过 2MB</p>
            <button class="btn" @click="changeAvatar">点击修改头像</button>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="username" type="text" placeholder="请输入用户名" />
          </div>
          <div class="form-group">
            <label>用户签名</label>
            <input v-model="signature" type="text" placeholder="请输入个性签名" />
          </div>
        </div>
        <div class="form-group">
          <label>个人介绍</label>
          <textarea v-model="bio" placeholder="介绍一下自己吧..."></textarea>
        </div>
        <div class="more-settings">
          <h2 class="section-title">更多设置</h2>
          <div class="form-group">
            <label>电子邮箱</label>
            <input v-model="email" type="email" placeholder="请输入电子邮箱" />
          </div>
          <div class="form-group">
            <label>验证码</label>
            <div class="input-group">
              <input v-model="verifyCode" type="text" placeholder="请输入验证码" maxlength="6" />
              <button class="btn" :disabled="sendDisabled" @click="sendCode">{{ sendText }}</button>
            </div>
            <p class="hint">验证码将发送到您的绑定手机</p>
          </div>
        </div>
        <div class="button-group">
          <button class="btn" @click="cancelEdit">取消</button>
          <button class="btn btn-primary" @click="submitEdit">确认修改</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/修改个人资料.css"></style>
