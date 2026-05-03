<script setup>
import { computed, onMounted, ref } from "vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");
const activePanel = ref("profile");
const username = ref("用户名");
const userIdText = ref("用户ID");
const email = ref("未填写");
const phone = ref("未绑定");
const createTime = ref("未知");
const bio = ref("暂无个人简介");

const publishList = ref([]);
const claimList = ref([]);
const unreadCount = ref(0);

const formatStatus = (status) => ({ 0: "待认领", 1: "已认领", 2: "已关闭" }[status] || "未知");
const formatClaimStatus = (status) => ({ 0: "待审核", 1: "审核通过", 2: "审核驳回", 3: "已取消" }[status] || "未知");

const panelClass = (name) => (activePanel.value === name ? "panel" : "panel hidden");
const activeBtn = (name) => (activePanel.value === name ? "nav-btn active" : "nav-btn");

const profileRows = computed(() => [
  { label: "邮箱：", value: email.value },
  { label: "手机号：", value: phone.value },
  { label: "注册时间：", value: createTime.value },
]);

async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/auth/users`);
    const data = await res.json();
    const user = (data || []).find((u) => String(u.user_id) === String(userId));
    if (!user) return;
    username.value = user.username || "用户名";
    userIdText.value = `ID: ${user.user_id || user.id}`;
    email.value = user.email || "未填写";
    phone.value = user.phone || "未绑定";
    createTime.value = user.create_time ? String(user.create_time).slice(0, 10) : "未知";
    bio.value = user.bio || "暂无个人简介";
  } catch (e) {
    console.error(e);
  }
}

async function loadPublish() {
  try {
    const res = await fetch(`${API_BASE}/my/publish?user_id=${userId}`);
    const data = await res.json();
    publishList.value = data.success ? data.data || [] : [];
  } catch {
    publishList.value = [];
  }
}

async function loadClaim() {
  try {
    const res = await fetch(`${API_BASE}/my/claim?user_id=${userId}`);
    const data = await res.json();
    claimList.value = data.success ? data.data || [] : [];
  } catch {
    claimList.value = [];
  }
}

async function loadUnreadCount() {
  try {
    const res = await fetch(`${API_BASE}/my/messages/unread-count?user_id=${userId}`);
    const data = await res.json();
    unreadCount.value = data.success ? data.unread_count : 0;
  } catch {
    unreadCount.value = 0;
  }
}

function switchPanel(panel) {
  activePanel.value = panel;
  if (panel === "publish") loadPublish();
  if (panel === "claim") loadClaim();
}

function goTo(action) {
  if (action === "home") window.location.href = "/home";
  if (action === "bind") window.location.href = "/security#bind";
  if (action === "password") window.location.href = "/security#password";
  if (action === "edit") window.location.href = "/edit";
  if (action === "about") window.location.href = "/about";
  if (action === "admin") window.location.href = "/admin";
  if (action === "messages") window.location.href = "/messages";
  if (action === "lost-items") window.location.href = "/lost-items";
}

async function cancelClaim(claimId) {
  if (!confirm("确定要取消这个认领申请吗？取消后将无法恢复。")) return;
  
  try {
    const res = await fetch(`${API_BASE}/claims/${claimId}/cancel`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId
      }),
    });
    
    const data = await res.json();
    
    if (data.success) {
      alert("认领申请已取消");
      loadClaim(); // 重新加载认领记录
    } else {
      alert("取消失败: " + (data.message || "请重试"));
    }
  } catch (error) {
    console.error("取消认领申请失败:", error);
    alert("取消失败，请检查网络连接后重试");
  }
}

function logout() {
  if (!confirm("确定要退出登录吗？")) return;
  localStorage.removeItem("user_id");
  localStorage.removeItem("username");
  localStorage.removeItem("email");
  window.location.href = "/login";
}

onMounted(() => {
  if (!userId) {
    alert("请先登录");
    window.location.href = "/login";
    return;
  }
  loadProfile();
  loadUnreadCount();
});
</script>

<template>
  <div>
    <div class="topbar">
      <div class="topbar-title">校园失物招领与位置追踪系统</div>
      <div class="topbar-user">管</div>
    </div>
    <div class="container">
      <div class="sidebar">
        <div class="avatar-container">
          <div class="avatar">👤</div>
          <div>
            <div class="username">{{ username }}</div>
            <div class="user-id">{{ userIdText }}</div>
          </div>
        </div>

        <div class="nav-buttons">
          <button :class="activeBtn('profile')" @click="switchPanel('profile')">个人资料</button>
          <button class="nav-btn" @click="goTo('lost-items')">📦 失物列表</button>
          <button :class="activeBtn('publish')" @click="switchPanel('publish')">失物发布记录</button>
          <button :class="activeBtn('claim')" @click="switchPanel('claim')">失物认领记录</button>
          <button class="nav-btn" @click="goTo('messages')">
            消息通知
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
          </button>
          <button class="nav-btn" @click="goTo('bind')">账号安全（手机）</button>
          <button class="nav-btn" @click="goTo('password')">账号安全（密码）</button>
          <button class="nav-btn" @click="goTo('edit')">修改个人资料</button>
          <button class="nav-btn" @click="goTo('home')">返回主页</button>
          <button class="nav-btn" @click="goTo('admin')">后台面板</button>
        </div>
        <div class="sidebar-footer">
          <a @click="logout">退出登录</a>
          <a @click="goTo('about')">关于我们</a>
        </div>
      </div>

      <div class="main-content">
        <div class="content-panel">
          <div :class="panelClass('profile')">
            <div class="panel-header">
              <div class="panel-tab active">基本信息</div>
            </div>
            <div class="info-grid">
              <div v-for="row in profileRows" :key="row.label" class="info-item">
                <span class="info-label">{{ row.label }}</span>
                <span class="info-value">{{ row.value }}</span>
              </div>
            </div>
            <div class="description-area">
              <label>个人简介：</label>
              <textarea :value="bio" readonly />
            </div>
          </div>

          <div :class="panelClass('publish')">
            <div class="panel-header"><div class="panel-tab active">全部记录</div></div>
            <table class="data-table">
              <thead><tr><th>物品名称</th><th>发布时间</th><th>状态</th><th>操作</th></tr></thead>
              <tbody>
                <tr v-for="item in publishList" :key="item.item_id">
                  <td>{{ item.title }}</td>
                  <td>{{ item.create_time }}</td>
                  <td>{{ formatStatus(item.status) }}</td>
                  <td><a href="#">查看</a></td>
                </tr>
                <tr v-if="publishList.length === 0"><td colspan="4">暂无数据</td></tr>
              </tbody>
            </table>
          </div>

          <div :class="panelClass('claim')">
            <div class="panel-header">
              <div class="panel-tab active">认领申请记录</div>
              <div class="panel-stats">共 {{ claimList.length }} 条记录</div>
            </div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>物品名称</th>
                  <th>认领时间</th>
                  <th>审核状态</th>
                  <th>审核时间</th>
                  <th>审核备注</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in claimList" :key="item.claim_id">
                  <td>{{ item.title || item.item_name }}</td>
                  <td>{{ item.create_time }}</td>
                  <td>
                    <span :class="`status-badge status-${item.status}`">
                      {{ formatClaimStatus(item.status) }}
                    </span>
                  </td>
                  <td>{{ item.review_time || '待审核' }}</td>
                  <td>{{ item.review_remark || '-' }}</td>
                  <td>
                    <button 
                      v-if="item.status === 0" 
                      class="btn-cancel"
                      @click="cancelClaim(item.claim_id)"
                    >
                      取消申请
                    </button>
                    <span v-else>-</span>
                  </td>
                </tr>
                <tr v-if="claimList.length === 0">
                  <td colspan="6" class="no-data">暂无认领申请记录</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="../assets/个人中心.css"></style>
