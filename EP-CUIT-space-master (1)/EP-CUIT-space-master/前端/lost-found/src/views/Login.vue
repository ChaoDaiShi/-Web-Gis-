<!-- 登录页面 -->
<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";

const router = useRouter();
const showToast = window.showToast;
const mode = ref("login");
const loginInput = ref("");
const password = ref("");
const confirmPassword = ref("");
const regUsername = ref("");
const regEmail = ref("");
const regPassword = ref("");
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
  router.push("/security?from=login#password");
}

async function submit() {
  const loginInputVal = loginInput.value.trim();
  const passwordVal = password.value.trim();
  const captchaVal = captcha.value.trim();
  const regUsernameVal = regUsername.value.trim();
  const regEmailVal = regEmail.value.trim();
  const regPasswordVal = regPassword.value.trim();

  if (mode.value === "login") {
    if (!loginInputVal || !passwordVal) {
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
    if (!regUsernameVal || !regEmailVal || !regPasswordVal || !confirmPassword.value.trim()) {
      showToast("请输入完整信息", 'warning');
      return;
    }
    
    if (regPasswordVal !== confirmPassword.value.trim()) {
      showToast("两次输入的密码不一致", 'error');
      return;
    }
  }

  try {
    if (mode.value === "login") {
      const isEmail = loginInputVal.includes('@');
      const res = await fetch("http://127.0.0.1:5000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          [isEmail ? 'email' : 'username']: loginInputVal, 
          password: passwordVal 
        }),
      });

      const data = await res.json();
      if (res.status === 200) {
        localStorage.removeItem("is_admin");
        localStorage.setItem("user_id", data.user.user_id);
        localStorage.setItem("username", data.user.username);
        localStorage.setItem("email", data.user.email);
        showToast("登录成功", "success");
        setTimeout(() => router.push("/home"), 1000);
      } else {
        showToast(data.message || "登录失败", "error");
      }
      return;
    }

    const res = await fetch("http://127.0.0.1:5000/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: regUsernameVal,
        email: regEmailVal,
        password: regPasswordVal,
      }),
    });
    const data = await res.json();
    if (res.status === 201) {
      showToast("注册成功，请登录", "success");
      setTimeout(() => switchToLogin(), 1000);
    } else {
      showToast(data.message || "注册失败", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("服务器连接失败", "error");
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
      showToast("管理员登录成功", "success");
      setTimeout(() => router.push("/admin"), 1000);
    } else {
      showToast(data.message || "管理员登录失败", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("服务器连接失败", "error");
  }
}
</script>

<template>
  <div class="login-page">
    <div class="video-background">
      <video autoplay muted loop class="background-video">
        <source src="/登录背景.mp4" type="video/mp4">
      </video>
      <div class="video-overlay"></div>
    </div>
    
    <AppTopBar variant="home">
      <template #actions>
        <button class="nav-link-btn" @click="router.push('/home')">首页</button>
        <button class="nav-link-btn" @click="router.push('/about')">关于我们</button>
      </template>
    </AppTopBar>
    
    <div class="login-container">
      <div class="login-card">
        <h2 class="login-title">欢迎</h2>

        <div class="tabs">
          <button :class="{ active: mode === 'login' }" type="button" @click="switchToLogin">登录</button>
          <button :class="{ active: mode === 'register' }" type="button" @click="switchToRegister">注册</button>
          <button :class="{ active: mode === 'admin' }" type="button" @click="switchToAdmin">管理员登录</button>
        </div>

        <div v-show="mode !== 'admin'" class="form-container">
          <div v-show="mode === 'register'" class="form-group">
            <label class="form-label">用户名</label>
            <div class="input-wrapper">
              <input v-model="regUsername" type="text" placeholder="请输入用户名（2-20个字符）" />
            </div>
          </div>

          <div v-show="mode === 'register'" class="form-group">
            <label class="form-label">邮箱</label>
            <div class="input-wrapper">
              <input v-model="regEmail" type="email" placeholder="请输入邮箱地址" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">账号</label>
            <div class="input-wrapper">
              <input v-model="loginInput" type="text" placeholder="邮箱或用户名（含@为邮箱）" />
            </div>
          </div>

          <div v-show="mode === 'login'" class="form-group">
            <label class="form-label">密码</label>
            <div class="input-wrapper">
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
            <label class="form-label">密码</label>
            <div class="input-wrapper">
              <input 
                v-model="regPassword" 
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
            <label class="form-label">人机验证</label>
            <div class="captcha-wrapper">
              <div class="captcha-input-wrapper">
                <input v-model="captcha" type="text" placeholder="请输入验证码" maxlength="5" />
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
              <input v-model="adminUsername" type="text" placeholder="请输入管理员用户名" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">管理员密码</label>
            <div class="input-wrapper">
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
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.video-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.background-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
}

.nav-link-btn {
  text-decoration: none;
  color: #1f2937;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
  background: transparent;
  border: none;
  cursor: pointer;
}

.nav-link-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.login-container {
  flex: 1;
  width: 100%;
  max-width: 520px;
  margin: auto;
  padding: 40px 20px;
}

.login-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 45px 50px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.15),
              0 10px 30px rgba(0, 0, 0, 0.1),
              0 2px 8px rgba(0, 0, 0, 0.06),
              0 0 0 1px rgba(0, 0, 0, 0.04);
  transform: perspective(1000px) rotateX(0deg);
}

.login-title {
  text-align: center;
  color: #1e293b;
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
  background: #f1f5f9;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tabs button:hover {
  background: #e2e8f0;
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
  flex-direction: row;
  align-items: center;
  gap: 15px;
}

.form-label {
  color: #475569;
  font-size: 14px;
  font-weight: 500;
  width: 70px;
  flex-shrink: 0;
  text-align: right;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper input {
  width: 100%;
  padding: 14px 15px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
  color: #1e293b;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
}

.input-wrapper input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-wrapper input::placeholder {
  color: #94a3b8;
}

.password-toggle {
  position: absolute;
  right: 15px;
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #94a3b8;
  transition: color 0.3s ease;
}

.password-toggle:hover {
  color: #64748b;
}

.captcha-group {
  align-items: center;
}

.captcha-wrapper {
  display: flex;
  gap: 12px;
  width: 100%;
}

.captcha-input-wrapper {
  flex: 1;
  position: relative;
}

.captcha-input-wrapper input {
  width: 100%;
  padding: 14px 15px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #ffffff;
  color: #1e293b;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
}

.captcha-input-wrapper input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.captcha-input-wrapper input::placeholder {
  color: #94a3b8;
}

.captcha-code {
  padding: 14px 18px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 12px;
  color: #2563eb;
  font-size: 18px;
  font-weight: bold;
  letter-spacing: 8px;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease;
  border: 1px solid #bfdbfe;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.15),
              0 2px 6px rgba(59, 130, 246, 0.1);
  min-width: 110px;
  text-align: center;
  line-height: 1.2;
}

.captcha-code:hover {
  border-color: #93c5fd;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.25),
              0 3px 8px rgba(59, 130, 246, 0.15);
}

.login-btn {
  padding: 16px;
  border: none;
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
  box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
}

.forgot-password {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: #64748b;
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
  background: #e2e8f0;
}

.divider-text {
  color: #94a3b8;
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
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #ffffff;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.social-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.social-icon {
  font-size: 16px;
}

.footer-links {
  display: flex;
  justify-content: center;
  gap: 8px;
  color: #64748b;
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
  color: #94a3b8;
  font-size: 12px;
}

.agreement a {
  color: #3b82f6;
  text-decoration: none;
}

.agreement a:hover {
  text-decoration: underline;
}
</style>