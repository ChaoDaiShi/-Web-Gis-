<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const mode = ref("login");
const loginMethod = ref("email");
const username = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const adminUsername = ref("");
const adminPassword = ref("");
const captcha = ref("");
const showPassword = ref(false);

const captchaCode = ref(generateCaptcha());

function generateCaptcha() {
  const chars = '0123456789';
  let result = '';
  for (let i = 0; i < 5; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

function refreshCaptcha() {
  captchaCode.value = generateCaptcha();
}

function switchToLogin() {
  mode.value = "login";
}

function switchToRegister() {
  mode.value = "register";
}

function switchToAdmin() {
  mode.value = "admin";
}

function goToResetPassword() {
  router.push("/security#password");
}

function showToast(message) {
  const existingToast = document.querySelector('.login-toast');
  if (existingToast) {
    existingToast.remove();
  }
  
  const toast = document.createElement('div');
  toast.className = 'login-toast';
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.85);
    color: #fff;
    padding: 16px 32px;
    border-radius: 12px;
    font-size: 16px;
    z-index: 9999;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    animation: toastFadeIn 0.3s ease;
  `;
  
  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    @keyframes toastFadeIn {
      from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
      to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
    }
    @keyframes toastFadeOut {
      from { opacity: 1; transform: translate(-50%, -50%) scale(1); }
      to { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
    }
    .login-toast.fade-out {
      animation: toastFadeOut 0.3s ease forwards;
    }
  `;
  document.head.appendChild(styleSheet);
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => {
      toast.remove();
      styleSheet.remove();
    }, 300);
  }, 1500);
}

async function submit() {
  const emailVal = email.value.trim();
  const passwordVal = password.value.trim();
  const usernameVal = username.value.trim();
  const captchaVal = captcha.value.trim();

  if (mode.value === "login") {
    const loginValue = loginMethod.value === 'email' ? emailVal : usernameVal;
    if (!loginValue || !passwordVal) {
      showToast("请输入完整信息", 'warning');
      return;
    }
    
    if (captchaVal !== captchaCode.value) {
      showToast("验证码错误", 'error');
      refreshCaptcha();
      captcha.value = "";
      return;
    }
  } else {
    if (!usernameVal || !emailVal || !passwordVal || !confirmPassword.value.trim()) {
      showToast("请输入完整信息", 'warning');
      return;
    }
    
    if (passwordVal !== confirmPassword.value.trim()) {
      showToast("两次输入的密码不一致", 'error');
      return;
    }
  }

  try {
    if (mode.value === "login") {
      const loginValue = loginMethod.value === 'email' ? emailVal : usernameVal;
      const res = await fetch("http://127.0.0.1:5000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          [loginMethod.value === 'email' ? 'email' : 'username']: loginValue, 
          password: passwordVal 
        }),
      });

      const data = await res.json();
      if (res.status === 200) {
        localStorage.removeItem("is_admin");
        localStorage.setItem("user_id", data.user.user_id);
        localStorage.setItem("username", data.user.username);
        localStorage.setItem("email", data.user.email);
        showToast("登录成功");
        setTimeout(() => router.push("/home"), 1000);
      } else {
        showToast(data.message || "登录失败");
      }
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
      showToast("注册成功，请登录");
      setTimeout(() => switchToLogin(), 1000);
    } else {
      showToast(data.message || "注册失败");
    }
  } catch (err) {
    console.error(err);
    showToast("服务器连接失败");
  }
}

async function submitAdmin() {
  const usernameVal = adminUsername.value.trim();
  const passwordVal = adminPassword.value.trim();
  if (!usernameVal || !passwordVal) {
    showToast("请输入管理员用户名与密码");
    return;
  }
  try {
    const res = await fetch("http://127.0.0.1:5000/api/auth/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: usernameVal, password: passwordVal }),
    });
    const data = await res.json();
    if (res.status === 200) {
      localStorage.removeItem("user_id");
      localStorage.removeItem("username");
      localStorage.removeItem("email");
      localStorage.setItem("is_admin", "1");
      showToast("管理员登录成功");
      setTimeout(() => router.push("/admin"), 1000);
    } else {
      showToast(data.message || "管理员登录失败");
    }
  } catch (err) {
    console.error(err);
    showToast("服务器连接失败");
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <h2 class="login-title">欢迎登录</h2>

        <div class="tabs">
          <button :class="{ active: mode === 'login' }" type="button" @click="switchToLogin">登录</button>
          <button :class="{ active: mode === 'register' }" type="button" @click="switchToRegister">注册</button>
          <button :class="{ active: mode === 'admin' }" type="button" @click="switchToAdmin">管理员登录</button>
        </div>

        <div v-show="mode !== 'admin'" class="form-container">
          <div v-show="mode === 'register'" class="form-group">
            <label class="form-label">用户名</label>
            <div class="input-wrapper">
              <span class="input-icon">👤</span>
              <input v-model="username" type="text" placeholder="请输入用户名（2-20个字符）" />
            </div>
          </div>

          <div v-show="mode === 'login'" class="login-method-switch">
            <button :class="{ active: loginMethod === 'email' }" @click="loginMethod = 'email'">邮箱登录</button>
            <button :class="{ active: loginMethod === 'username' }" @click="loginMethod = 'username'">用户名登录</button>
          </div>

          <div class="form-group">
            <label class="form-label">{{ loginMethod === 'email' ? '邮箱' : '用户名' }}</label>
            <div class="input-wrapper">
              <span class="input-icon">{{ loginMethod === 'email' ? '✉️' : '👤' }}</span>
              <input v-if="loginMethod === 'email'" v-model="email" type="email" placeholder="请输入邮箱地址" />
              <input v-else v-model="username" type="text" placeholder="请输入用户名" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">密码</label>
            <div class="input-wrapper">
              <span class="input-icon">🔒</span>
              <input 
                v-model="password" 
                :type="showPassword ? 'text' : 'password'" 
                placeholder="请输入密码（8-32个字符）" 
              />
              <button class="password-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? '🙈' : '👁' }}
              </button>
            </div>
          </div>

          <div v-show="mode === 'register'" class="form-group">
            <label class="form-label">确认密码</label>
            <div class="input-wrapper">
              <span class="input-icon">🔑</span>
              <input 
                v-model="confirmPassword" 
                :type="showPassword ? 'text' : 'password'" 
                placeholder="请再次输入密码" 
              />
              <button class="password-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? '🙈' : '👁' }}
              </button>
            </div>
          </div>

          <div v-show="mode === 'login'" class="form-group captcha-group">
            <label class="form-label">人机验证码</label>
            <div class="captcha-wrapper">
              <div class="input-wrapper captcha-input">
                <span class="input-icon">🛡</span>
                <input v-model="captcha" type="text" placeholder="请输入右侧验证码" maxlength="5" />
              </div>
              <div class="captcha-code" @click="refreshCaptcha">
                {{ captchaCode }}
              </div>
            </div>
          </div>

          <button class="login-btn" type="button" @click="submit">
            {{ mode === "login" ? "登录" : "注册" }}
          </button>

          <div v-show="mode === 'login'" class="forgot-password">
            <span>忘记密码？</span>
            <button class="forgot-btn" @click="goToResetPassword">点击修改</button>
          </div>
        </div>

        <div v-show="mode === 'admin'" class="form-container">
          <div class="form-group">
            <label class="form-label">管理员用户名</label>
            <div class="input-wrapper">
              <span class="input-icon">👤</span>
              <input v-model="adminUsername" type="text" placeholder="请输入管理员用户名" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">管理员密码</label>
            <div class="input-wrapper">
              <span class="input-icon">🔒</span>
              <input 
                v-model="adminPassword" 
                :type="showPassword ? 'text' : 'password'" 
                placeholder="请输入管理员密码" 
              />
              <button class="password-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? '🙈' : '👁' }}
              </button>
            </div>
          </div>

          <button class="login-btn" type="button" @click="submitAdmin">进入后台</button>

          <div class="footer-links">
            <span>返回</span>
            <a href="#" @click.prevent="switchToLogin">用户登录</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 50%, #0d1b2a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 420px;
}

.login-card {
  background: rgba(15, 23, 42, 0.95);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.05);
}

.login-title {
  text-align: center;
  color: #fff;
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 30px 0;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

.tabs button {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tabs button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.tabs button.active {
  background: #3b82f6;
  color: #fff;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 15px;
  font-size: 16px;
  color: #64748b;
}

.input-wrapper input {
  width: 100%;
  padding: 14px 15px 14px 45px;
  border: none;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.3);
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
}

.input-wrapper input:focus {
  background: rgba(0, 0, 0, 0.4);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.input-wrapper input::placeholder {
  color: #64748b;
}

.password-toggle {
  position: absolute;
  right: 15px;
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #64748b;
  transition: color 0.3s ease;
}

.password-toggle:hover {
  color: #94a3b8;
}

.login-method-switch {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.login-method-switch button {
  flex: 1;
  padding: 10px;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-method-switch button:hover {
  background: rgba(59, 130, 246, 0.1);
}

.login-method-switch button.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #3b82f6;
}

.captcha-group {
  flex-direction: row;
  align-items: flex-start;
}

.captcha-wrapper {
  display: flex;
  gap: 12px;
  width: 100%;
}

.captcha-input {
  flex: 1;
}

.captcha-code {
  padding: 14px 20px;
  background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
  border-radius: 12px;
  color: #3b82f6;
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 4px;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.captcha-code:hover {
  border-color: rgba(59, 130, 246, 0.6);
  transform: scale(1.02);
}

.login-btn {
  padding: 16px;
  border: 2px solid #3b82f6;
  border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(59, 130, 246, 0.4);
}

.forgot-password {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
  font-size: 14px;
  margin-top: 8px;
}

.forgot-btn {
  background: none;
  border: none;
  color: #3b82f6;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.forgot-btn:hover {
  background: rgba(59, 130, 246, 0.1);
  text-decoration: underline;
}

.divider {
  display: flex;
  align-items: center;
  gap: 15px;
  margin: 10px 0;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
}

.divider-text {
  color: #64748b;
  font-size: 14px;
}

.social-buttons {
  display: flex;
  gap: 12px;
}

.social-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  color: #94a3b8;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.social-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.social-icon {
  font-size: 16px;
}

.footer-links {
  display: flex;
  justify-content: center;
  gap: 8px;
  color: #94a3b8;
  font-size: 14px;
}

.footer-links a {
  color: #3b82f6;
  text-decoration: none;
}

.footer-links a:hover {
  text-decoration: underline;
}

.agreement {
  text-align: center;
  color: #64748b;
  font-size: 12px;
}

.agreement a {
  color: #3b82f6;
  text-decoration: none;
}

.agreement a:hover {
  text-decoration: underline;
}

.login-toast {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.85);
  color: #fff;
  padding: 16px 32px;
  border-radius: 12px;
  font-size: 16px;
  z-index: 9999;
  animation: fadeIn 0.3s ease;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.login-toast.fade-out {
  animation: fadeOut 0.3s ease forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.9);
  }
}
</style>