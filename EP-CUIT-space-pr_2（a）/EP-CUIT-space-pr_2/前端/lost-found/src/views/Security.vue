<script setup>
import { onMounted, ref } from "vue"
import AppTopBar from "../components/AppTopBar.vue"

const tab = ref("bind")
const phone = ref("")
const sms = ref("")
const oldPwd = ref("")
const newPwd = ref("")
const confirmPwd = ref("")
const pwdSms = ref("")
const pwdGeneratedCode = ref("")
const sendText = ref("获取验证码")
const sendDisabled = ref(false)
const bindSuccess = ref(false)
const pwdSuccess = ref(false)
const hasChanges = ref(false)
let countdown = 0
let timer = null

const originalPhone = ref("")

function switchTab(target) {
  tab.value = target
  window.location.hash = target
}
function checkChanges() {
  if (tab.value === 'bind') {
    hasChanges.value = phone.value !== originalPhone.value || sms.value !== ""
  } else {
    hasChanges.value = oldPwd.value !== "" || newPwd.value !== "" || confirmPwd.value !== ""
  }
}
function cancel() {
  window.location.href = "/profile"
}
function sendSms() {
  if (!phone.value || phone.value.length !== 11) return window.showToast("请输入正确的手机号", 'warning')
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
  window.showToast("验证码已发送，请查收短信", 'success')
}
function generatePwdCode() {
  pwdGeneratedCode.value = Math.random().toString().substring(2, 6)
}
function submitBind() {
  if (!phone.value || phone.value.length !== 11) return window.showToast("请输入正确的手机号", 'warning')
  if (!sms.value || sms.value.length !== 6) return window.showToast("请输入6位验证码", 'warning')
  window.showToast("绑定成功", 'success')
  setTimeout(() => window.location.href = "/profile", 1000)
}
async function submitPwd() {
  if (!oldPwd.value) return window.showToast("请输入当前密码", 'warning')
  if (!newPwd.value || newPwd.value.length < 8) return window.showToast("新密码至少8位", 'warning')
  if (newPwd.value !== confirmPwd.value) return window.showToast("两次输入的密码不一致", 'error')
  
  const user_id = localStorage.getItem("user_id")
  if (!user_id) return window.showToast("请先登录", 'warning')
  
  try {
    const response = await fetch('http://127.0.0.1:5000/api/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: user_id,
        old_password: oldPwd.value,
        new_password: newPwd.value
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      window.showToast("密码修改成功", 'success')
      setTimeout(() => {
        oldPwd.value = ""
        newPwd.value = ""
        confirmPwd.value = ""
        pwdSms.value = ""
        pwdGeneratedCode.value = ""
      }, 1000)
    } else {
      window.showToast(data.message || '修改失败', 'error')
    }
  } catch (error) {
    window.showToast('网络错误', 'error')
    console.error(error)
  }
}

onMounted(() => {
  const initial = (window.location.hash || "").replace("#", "")
  tab.value = initial === "password" ? "password" : "bind"
})
</script>

<template>
  <div class="page">
    <AppTopBar variant="inner" />
    <div class="container">
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
          <div class="form-group"><label>手机号</label><input v-model="phone" type="tel" placeholder="请输入手机号" maxlength="11" @input="checkChanges" /></div>
          <div class="form-group">
            <label>短信验证码</label>
            <div class="input-group">
              <input v-model="sms" type="text" placeholder="请输入验证码" maxlength="6" @input="checkChanges" />
              <button class="btn" :disabled="sendDisabled" @click="sendSms">{{ sendText }}</button>
            </div>
          </div>
          <div class="button-group">
            <button class="btn" @click="cancel">{{ hasChanges ? '取消' : '返回' }}</button>
            <button class="btn btn-primary submit-btn" @click="submitBind">确认绑定</button>
          </div>
        </div>
        <div v-show="tab === 'password'" class="panel active">
          <div v-show="pwdSuccess" class="success-msg">密码修改成功！</div>
          <div class="form-group"><label>当前密码</label><input v-model="oldPwd" type="password" placeholder="请输入当前密码" @input="checkChanges" /></div>
          <div class="form-group"><label>新密码</label><input v-model="newPwd" type="password" placeholder="请输入新密码（8位及以上）" @input="checkChanges" /></div>
          <div class="form-group"><label>确认新密码</label><input v-model="confirmPwd" type="password" placeholder="请再次输入新密码" @input="checkChanges" /></div>
          <div class="form-group">
            <label>验证码</label>
            <div class="input-group">
              <input v-model="pwdSms" type="text" placeholder="请输入验证码" maxlength="4" @input="checkChanges" />
              <button class="btn" @click="generatePwdCode">{{ pwdGeneratedCode || '获取验证码' }}</button>
            </div>
          </div>
          <div class="button-group">
            <button class="btn" @click="cancel">{{ hasChanges ? '取消' : '返回' }}</button>
            <button class="btn btn-primary submit-btn" @click="submitPwd">确认修改</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/账号安全.css"></style>
