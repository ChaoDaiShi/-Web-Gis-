<script setup>
import { ref } from "vue";

const mode = ref("login");
const username = ref("");
const email = ref("");
const password = ref("");
const tipText = ref("请输入账号密码进行登录");

function switchToLogin() {
  mode.value = "login";
  tipText.value = "请输入账号密码进行登录";
}

function switchToRegister() {
  mode.value = "register";
  tipText.value = "创建新账号";
}

async function submit() {
  const emailVal = email.value.trim();
  const passwordVal = password.value.trim();
  const usernameVal = username.value.trim();

  if (!emailVal || !passwordVal) {
    alert("请输入完整信息");
    return;
  }

  try {
    if (mode.value === "login") {
      const res = await fetch("http://127.0.0.1:5000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailVal, password: passwordVal }),
      });

      const data = await res.json();
      if (res.status === 200) {
        localStorage.setItem("user_id", data.user.user_id);
        localStorage.setItem("username", data.user.username);
        localStorage.setItem("email", data.user.email);
        alert("登录成功");
        window.location.href = "/home";
      } else {
        alert(data.message || "登录失败");
      }
      return;
    }

    if (!usernameVal) {
      alert("请输入用户名");
      return;
    }

    const res = await fetch("http://127.0.0.1:5000/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: usernameVal,
        email: emailVal,
        password: passwordVal,
      }),
    });
    const data = await res.json();
    if (res.status === 201) {
      alert("注册成功，请登录");
      switchToLogin();
    } else {
      alert(data.message || "注册失败");
    }
  } catch (err) {
    console.error(err);
    alert("服务器连接失败");
  }
}
</script>

<template>
  <div>
    <div class="header">校园失物招领与位置追踪系统</div>

    <div class="container">
      <div class="card">
        <div class="tabs">
          <button :class="{ active: mode === 'login' }" @click="switchToLogin">登录</button>
          <button :class="{ active: mode === 'register' }" @click="switchToRegister">注册</button>
        </div>

        <div class="card-inner">
          <input
            v-show="mode === 'register'"
            v-model="username"
            type="text"
            placeholder="用户名（注册用）"
          />
          <input v-model="email" type="text" placeholder="邮箱" />
          <input v-model="password" type="password" placeholder="密码" />
          <button @click="submit">{{ mode === "login" ? "登录" : "注册" }}</button>
          <div class="tip">{{ tipText }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/登录界面.css"></style>
