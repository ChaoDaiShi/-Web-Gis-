<script setup>import { onMounted, ref } from "vue";
import AppTopBar from "../components/AppTopBar.vue";
const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");
const username = ref("");
const signature = ref("");
const bio = ref("");
const avatar = ref("");
const avatarFile = ref(null);
const successMsg = ref(false);
const errorMsg = ref("");
function goProfile() {
  window.location.href = "/profile";
}
function goHome() {
 window.location.href = "/home";
}
async function loadUser() {
 try {
 const res = await fetch(`http://127.0.0.1:5000/api/profile?user_id=${userId}`);
 const data = await res.json();
 if (data.success && data.data) {
 username.value = data.data.username || "";
 signature.value = data.data.signature || "";
 bio.value = data.data.bio || "";
 avatar.value = data.data.avatar ? `http://127.0.0.1:5000${data.data.avatar}` : "";
 }
 }
 catch (error) {
 console.error("加载用户信息失败:", error);
 }
}
function changeAvatar() {
 const input = document.createElement("input");
 input.type = "file";
 input.accept = "image/*";
 input.onchange = () => {
 const file = input.files?.[0];
 if (!file)
 return;
 avatar.value = URL.createObjectURL(file);
 avatarFile.value = file;
 };
 input.click();
}
async function submitEdit() {
 if (!username.value.trim()) {
 showToast("请输入用户名", 'warning');
 return;
 }
 errorMsg.value = "";
 try {
 if (avatarFile.value) {
 const formData = new FormData();
 formData.append("user_id", userId);
 formData.append("avatar", avatarFile.value);
 const res = await fetch(`http://127.0.0.1:5000/api/profile/avatar`, {
 method: "POST",
 body: formData,
 });
 const data = await res.json();
 if (!data.success) {
 showToast(data.message || "头像上传失败", 'error');
 return;
 }
 }
 const res = await fetch(`http://127.0.0.1:5000/api/profile`, {
 method: "PUT",
 headers: { "Content-Type": "application/json" },
 body: JSON.stringify({
 user_id: userId,
 username: username.value.trim(),
 signature: signature.value.trim(),
 bio: bio.value.trim(),
 }),
 });
 const data = await res.json();
 if (data.success) {
 localStorage.setItem("username", username.value.trim());
 successMsg.value = true;
 setTimeout(() => {
 window.location.href = "/profile";
 }, 1200);
 }
 else {
 errorMsg.value = data.message || "保存失败";
 }
 }
 catch (error) {
 console.error("保存失败:", error);
 errorMsg.value = "保存失败，请重试";
 }
}
onMounted(() => {
 if (!userId) {
 showToast("请先登录", 'warning');
 setTimeout(() => window.location.href = "/login", 1000);
 return;
 }
 loadUser();
});
</script>

<template>
  <div class="edit-profile-page" style="overflow-y: auto !important; overflow-x: hidden;">
    <AppTopBar variant="inner" />
    <div class="container">
      <div class="content-card">
        <h1 class="card-title">修改个人资料</h1>
        <div v-show="successMsg" class="success-msg">个人资料修改成功！</div>
        <div v-show="errorMsg" class="error-msg">{{ errorMsg }}</div>
        
        <div class="section">
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
        </div>
        
        <div class="button-group">
          <button class="btn" @click="goProfile">取消</button>
          <button class="btn btn-primary" @click="submitEdit">确认修改</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/修改个人资料.css"></style>
