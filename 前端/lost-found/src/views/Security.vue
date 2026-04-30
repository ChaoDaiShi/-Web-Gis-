<script setup>
import { onMounted, ref } from "vue"

const tab = ref("bind")
const phone = ref("")
const sms = ref("")
const oldPwd = ref("")
const newPwd = ref("")
const confirmPwd = ref("")
const sendText = ref("获取验证码")
const sendDisabled = ref(false)
const bindSuccess = ref(false)
const pwdSuccess = ref(false)
let countdown = 0
let timer = null

function switchTab(target) {
  tab.value = target
  window.location.hash = target
}
function goProfile() {
  window.location.href = "/profile"
}
function goHome() {
  window.location.href = "/home"
}
function sendSms() {
  if (!phone.value || phone.value.length !== 11) return alert("请输入正确的手机号")
  if (countdown > 0) return
  countdown = 60
  sendDisabled.value = true
  sendText.value = `${countdown}秒后重试`
  timer = setInterval(() => {
    countdown -= 1
    if (countdown > 0) sendText.value = `${countdown}秒后重试`
    else {
      clearInterval(timer)
      sendDisabled.value = false
      sendText.value = "获取验证码"
    }
  }, 1000)
  alert("验证码已发送，请查收短信")
}
function submitBind() {
  if (!phone.value || phone.value.length !== 11) return alert("请输入正确的手机号")
  if (!sms.value || sms.value.length !== 6) return alert("请输入6位验证码")
  bindSuccess.value = true
  setTimeout(() => (bindSuccess.value = false), 3000)
}
function submitPwd() {
  if (!oldPwd.value) return alert("请输入当前密码")
  if (!newPwd.value || newPwd.value.length < 8) return alert("新密码至少8位")
  if (newPwd.value !== confirmPwd.value) return alert("两次输入的密码不一致")
  pwdSuccess.value = true
  setTimeout(() => {
    pwdSuccess.value = false
    oldPwd.value = ""
    newPwd.value = ""
    confirmPwd.value = ""
  }, 3000)
}

onMounted(() => {
  const initial = (window.location.hash || "").replace("#", "")
  tab.value = initial === "password" ? "password" : "bind"
})
</script>

<template>
  <div class="page">
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
        <div class="card-header">
          <h1 class="card-title">账号安全中心</h1>
          <p class="card-desc">绑定手机与修改密码已合并到同一页，统一入口，操作更直观。</p>
        </div>
        <div class="tabs">
          <button class="tab" :class="{ active: tab === 'bind' }" @click="switchTab('bind')">绑定手机</button>
          <button class="tab" :class="{ active: tab === 'password' }" @click="switchTab('password')">修改密码</button>
        </div>
        <div v-show="tab === 'bind'" class="panel active">
          <div v-show="bindSuccess" class="success-msg">手机号绑定成功！</div>
          <div class="form-group"><label>手机号</label><input v-model="phone" type="tel" placeholder="请输入手机号" maxlength="11" /></div>
          <div class="form-group">
            <label>短信验证码</label>
            <div class="input-group">
              <input v-model="sms" type="text" placeholder="请输入验证码" maxlength="6" />
              <button class="btn" :disabled="sendDisabled" @click="sendSms">{{ sendText }}</button>
            </div>
          </div>
          <button class="btn btn-primary submit-btn" @click="submitBind">确认绑定</button>
        </div>
        <div v-show="tab === 'password'" class="panel active">
          <div v-show="pwdSuccess" class="success-msg">密码修改成功！</div>
          <div class="form-group"><label>当前密码</label><input v-model="oldPwd" type="password" placeholder="请输入当前密码" /></div>
          <div class="form-group"><label>新密码</label><input v-model="newPwd" type="password" placeholder="请输入新密码（8位及以上）" /></div>
          <div class="form-group"><label>确认新密码</label><input v-model="confirmPwd" type="password" placeholder="请再次输入新密码" /></div>
          <button class="btn btn-primary submit-btn" @click="submitPwd">确认修改</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/账号安全.css"></style>
