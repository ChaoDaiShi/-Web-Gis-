<!-- 账号安全 -->
<script setup>
import { onMounted, ref } from "vue"
import AppTopBar from "../components/AppTopBar.vue"

const showToast = window.showToast;
const tab = ref("bind")
const phone = ref("")
const sms = ref("")
const oldPwd = ref("")
const newPwd = ref("")
const confirmPwd = ref("")
const pwdSms = ref("")
const pwdGeneratedCode = ref("")
const emailPwd = ref("")
const newEmail = ref("")
const confirmEmail = ref("")
const emailGeneratedCode = ref("")
const emailSms = ref("")
const sendText = ref("获取验证码")
const sendDisabled = ref(false)
const bindSuccess = ref(false)
const pwdSuccess = ref(false)
const emailSuccess = ref(false)
const hasChanges = ref(false)
let countdown = 0
let timer = null

const originalPhone = ref("")
const fromLogin = ref(false)

function switchTab(target) {
  tab.value = target
  window.location.hash = target
}
function checkChanges() {
  if (tab.value === 'bind') {
    hasChanges.value = phone.value !== originalPhone.value || sms.value !== ""
  } else if (tab.value === 'password') {
    hasChanges.value = oldPwd.value !== "" || newPwd.value !== "" || confirmPwd.value !== ""
  } else {
    hasChanges.value = emailPwd.value !== "" || newEmail.value !== "" || confirmEmail.value !== ""
  }
}
function cancel() {
  if (fromLogin.value) {
    window.location.href = "/login"
  } else {
    window.location.href = "/profile"
  }
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
function generateEmailCode() {
  emailGeneratedCode.value = Math.random().toString().substring(2, 6)
}
function submitBind() {
  if (!phone.value || phone.value.length !== 11) return window.showToast("请输入正确的手机号", 'warning')
  if (!sms.value || sms.value.length !== 6) return window.showToast("请输入6位验证码", 'warning')
  window.showToast("绑定成功", 'success')
  // 等待提示框显示完毕后再跳转（Toast 显示 3000ms）
  setTimeout(() => window.location.href = "/profile", 3000)
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
      pwdSuccess.value = true
      window.showToast("密码修改成功，请使用新密码重新登录", 'success')
      // 等待提示框显示完毕后再退出（Toast 显示 3000ms）
      setTimeout(() => {
        oldPwd.value = ""
        newPwd.value = ""
        confirmPwd.value = ""
        pwdSms.value = ""
        pwdGeneratedCode.value = ""
        hasChanges.value = false
        // 清除登录状态并跳转到登录页
        localStorage.removeItem("user_id")
        localStorage.removeItem("username")
        localStorage.removeItem("email")
        localStorage.removeItem("is_admin")
        window.location.href = "/login"
      }, 3000)
    } else {
      window.showToast(data.message || '修改失败', 'error')
    }
  } catch (error) {
    window.showToast('网络错误', 'error')
    console.error(error)
  }
}
async function submitEmail() {
  if (!emailPwd.value) return window.showToast("请输入当前密码", 'warning')
  if (!newEmail.value || !newEmail.value.includes('@')) return window.showToast("请输入正确的邮箱地址", 'warning')
  if (newEmail.value !== confirmEmail.value) return window.showToast("两次输入的邮箱不一致", 'error')
  
  const user_id = localStorage.getItem("user_id")
  if (!user_id) return window.showToast("请先登录", 'warning')
  
  try {
    const response = await fetch('http://127.0.0.1:5000/api/auth/change-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: user_id,
        password: emailPwd.value,
        new_email: newEmail.value
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      emailSuccess.value = true
      window.showToast("邮箱修改成功", 'success')
      setTimeout(() => {
        emailPwd.value = ""
        newEmail.value = ""
        confirmEmail.value = ""
        emailSms.value = ""
        emailGeneratedCode.value = ""
        hasChanges.value = false
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
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('from') === 'login') {
    fromLogin.value = true;
  }
  
  const initial = (window.location.hash || "").replace("#", "")
  if (initial === "password") {
    tab.value = "password"
  } else if (initial === "email") {
    tab.value = "email"
  } else {
    tab.value = "bind"
  }
})
</script>

<template>
  <div class="page">
    <AppTopBar variant="inner" />
    <div class="container">
      <div class="content-card">
        <div class="card-header">
          <h1 class="card-title">账号安全中心</h1>
          <p class="card-desc">账号安全设置，包括绑定手机、修改密码和修改邮箱。</p>
        </div>
        <div class="tabs">
          <button class="tab" :class="{ active: tab === 'bind' }" @click="switchTab('bind')">绑定手机</button>
          <button class="tab" :class="{ active: tab === 'password' }" @click="switchTab('password')">修改密码</button>
          <button class="tab" :class="{ active: tab === 'email' }" @click="switchTab('email')">修改邮箱</button>
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
        <div v-show="tab === 'email'" class="panel active">
          <div v-show="emailSuccess" class="success-msg">邮箱修改成功！</div>
          <div class="form-group"><label>当前密码</label><input v-model="emailPwd" type="password" placeholder="请输入当前密码" @input="checkChanges" /></div>
          <div class="form-group"><label>新邮箱</label><input v-model="newEmail" type="email" placeholder="请输入新邮箱地址" @input="checkChanges" /></div>
          <div class="form-group"><label>确认新邮箱</label><input v-model="confirmEmail" type="email" placeholder="请再次输入新邮箱" @input="checkChanges" /></div>
          <div class="form-group">
            <label>验证码</label>
            <div class="input-group">
              <input v-model="emailSms" type="text" placeholder="请输入验证码" maxlength="4" @input="checkChanges" />
              <button class="btn" @click="generateEmailCode">{{ emailGeneratedCode || '获取验证码' }}</button>
            </div>
          </div>
          <div class="button-group">
            <button class="btn" @click="cancel">{{ hasChanges ? '取消' : '返回' }}</button>
            <button class="btn btn-primary submit-btn" @click="submitEmail">确认修改</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/account-security.css"></style>
