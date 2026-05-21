<script setup>
import { computed, onMounted, ref } from "vue";
import AppTopBar from "../components/AppTopBar.vue";
import MarkerDetailModal from "../components/MarkerDetailModal.vue";

const API_BASE = "http://127.0.0.1:5000/api";
const userId = localStorage.getItem("user_id");
const activePanel = ref("profile");
const activePublishTab = ref("all");
const username = ref("用户名");
const userIdText = ref("用户ID");
const email = ref("未填写");
const phone = ref("未绑定");
const createTime = ref("未知");
const bio = ref("暂无个人简介");
const signature = ref("暂无个性签名");
const avatarUrl = ref("");
const bgImage = ref("");

const pageStyle = computed(() => {
  if (bgImage.value) {
    return {
      background: `url(${bgImage.value}) center/cover`,
      minHeight: '100vh'
    };
  }
  return {};
});

const publishList = ref([]);
const claimList = ref([]);

const showDetailModal = ref(false);
const selectedMarker = ref(null);

const formatStatus = (status, type) => {
  if (status === 2) return "已关闭";
  if (type === 0) {
    return status === 0 ? "未找到" : "已找到";
  } else {
    return status === 0 ? "未被认领" : "已被认领";
  }
};
const formatType = (type) => (type === 0 ? "丢失" : "拾到");
const formatClaimStatus = (status) => {
  if (status === 'approved' || status === 1) return "已找到";
  if (status === 'pending' || status === 0) return "待审核";
  if (status === 'rejected') return "已拒绝";
  return status;
};

const panelClass = (name) => (activePanel.value === name ? "panel" : "panel hidden");
const activeBtn = (name) => (activePanel.value === name ? "nav-btn active" : "nav-btn");
const activePublishBtn = (name) => (activePublishTab.value === name ? "publish-tab active" : "publish-tab");

const filteredPublishList = computed(() => {
  if (activePublishTab.value === "all") {
    return publishList.value;
  } else if (activePublishTab.value === "lost") {
    return publishList.value.filter(item => item.type === 0);
  } else if (activePublishTab.value === "found") {
    return publishList.value.filter(item => item.type === 1);
  }
  return publishList.value;
});

const profileRows = computed(() => [
  { label: "邮箱：", value: email.value },
  { label: "手机号：", value: phone.value },
  { label: "注册时间：", value: createTime.value },
]);

async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile?user_id=${userId}`);
    const data = await res.json();
    if (data.success && data.data) {
      const user = data.data;
      username.value = user.username || "用户名";
      userIdText.value = `ID: ${user.user_id || userId}`;
      email.value = user.email || "未填写";
      phone.value = user.phone || "未绑定";
      createTime.value = user.create_time || "未知";
      bio.value = user.bio || "暂无个人简介";
      signature.value = user.signature || "暂无个性签名";
      avatarUrl.value = user.avatar ? `http://127.0.0.1:5000${user.avatar}` : "";
      bgImage.value = user.bg_image ? `http://127.0.0.1:5000${user.bg_image}` : "";
      if (bgImage.value) {
        document.body.style.background = `url(${bgImage.value}) center/cover fixed`;
        document.body.style.minHeight = '100vh';
      }
    }
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

function switchPanel(panel) {
  activePanel.value = panel;
  if (panel === "publish") loadPublish();
  if (panel === "claim") loadClaim();
}

function goTo(action) {
  if (action === "home") window.location.href = "/home";
  if (action === "security") window.location.href = "/security";
  if (action === "edit") window.location.href = "/edit";
  if (action === "about") window.location.href = "/about";
  if (action === "messages") window.location.href = "/messages?from=profile";
  if (action === "claim") window.location.href = "/claim-form";
}

function logout() {
  window.showToast('退出成功', 'success');
  setTimeout(() => {
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    localStorage.removeItem("email");
    localStorage.removeItem("is_admin");
    window.location.href = "/login";
  }, 1000);
}

function viewDetail(item) {
  selectedMarker.value = {
    id: item.item_id,
    title: item.title,
    detail: item.description || '',
    status: item.status,
    time: item.create_time,
    images: item.image_urls || [],
    type: item.type,
    publisher_id: item.publisher_id
  };
  showDetailModal.value = true;
}

async function updateItemStatus(item, newStatus) {
  const isMarkingFound = newStatus === 1;
  const isLostItem = item.type === 0;
  
  let confirmMessage;
  let successMessage;
  
  if (isMarkingFound) {
    confirmMessage = isLostItem ? '确定要标记为"已找到"吗？' : '确定要标记为"已归还"吗？';
    successMessage = isLostItem ? '标记为"已找到"成功！' : '标记为"已归还"成功！';
  } else {
    confirmMessage = isLostItem ? '确定要取消"已找到"吗？物品状态将变为"未找到"。' : '确定要取消"已归还"吗？物品状态将变为"未被认领"。';
    successMessage = isLostItem ? '已取消"已找到"，状态变为"未找到"' : '已取消"已归还"，状态变为"未被认领"';
  }
    
  if (!confirm(confirmMessage)) {
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/map/update-status/${item.item_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        status: newStatus,
        user_id: userId
      })
    });
    
    const data = await res.json();
    
    if (data.success) {
      window.showToast(successMessage, 'success');
      
      if (isLostItem) {
        if (isMarkingFound) {
          await syncToClaimRecords(item, true);
        } else {
          await syncToClaimRecords(item, false);
        }
      }
      
      loadPublish();
    } else {
      window.showToast(data.message || '操作失败', 'error');
    }
  } catch (error) {
    console.error('更新状态失败:', error);
    window.showToast('更新状态失败，请重试', 'error');
  }
}

async function syncToClaimRecords(item, shouldCreate) {
  try {
    if (shouldCreate) {
      console.log('正在创建认领记录，物品ID:', item.item_id);
      const response = await fetch(`${API_BASE}/my/claim`, {
        method: "POST",
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          item_id: item.item_id,
          user_id: userId
        })
      });
      
      const data = await response.json();
      console.log('创建认领记录结果:', data);
      
      if (data.success) {
        loadClaim();
      } else {
        console.warn('创建认领记录失败:', data.message);
      }
    } else {
      console.log('正在删除认领记录，物品ID:', item.item_id);
      const response = await fetch(`${API_BASE}/my/claim/by-item/${item.item_id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId
        })
      });
      
      const data = await response.json();
      console.log('删除认领记录结果:', data);
      
      if (data.success) {
        loadClaim();
      } else {
        console.warn('删除认领记录失败:', data.message);
      }
    }
  } catch (error) {
    console.error('同步认领记录失败:', error);
  }
}

async function deleteItem(itemId) {
  if (!confirm('确定要删除这条发布记录吗？删除后将无法恢复。')) {
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/map/delete-marker/${itemId}`, {
      method: 'DELETE'
    });
    
    if (!res.ok) {
      window.showToast('删除失败，请重试', 'error');
      return;
    }
    
    const data = await res.json();
    
    if (data.success) {
      window.showToast('删除成功', 'success');
      loadPublish();
    } else {
      window.showToast('删除失败: ' + (data.message || '请重试'), 'error');
    }
  } catch (error) {
    console.error('删除失败:', error);
    window.showToast('删除失败，请检查网络连接', 'error');
  }
}

async function deleteClaim(claimId) {
  if (!confirm('确定要删除这条认领记录吗？删除后将无法恢复。')) {
    return;
  }
  
  try {
    console.log(`[DEBUG] Deleting claim with id: ${claimId}`);
    console.log(`[DEBUG] Request URL: ${API_BASE}/admin/claim-forms/${claimId}`);
    
    const res = await fetch(`${API_BASE}/admin/claim-forms/${claimId}`, {
      method: 'DELETE'
    });
    
    console.log(`[DEBUG] Response status: ${res.status}`);
    console.log(`[DEBUG] Response ok: ${res.ok}`);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.log(`[DEBUG] Error response: ${errorText}`);
      window.showToast('删除失败，请重试', 'error');
      return;
    }
    
    const data = await res.json();
    console.log(`[DEBUG] Response data:`, data);
    
    if (data.success) {
      window.showToast('删除成功', 'success');
      loadClaim();
    } else {
      window.showToast('删除失败: ' + (data.message || '请重试'), 'error');
    }
  } catch (error) {
    console.error('删除认领记录失败:', error);
    window.showToast('删除失败，请检查网络连接', 'error');
  }
}

async function cancelClaim(item) {
  if (!confirm('确定要取消找到吗？取消后物品状态将变为"未找到"。')) {
    return;
  }
  
  try {
    await fetch(`${API_BASE}/map/update-status/${item.item_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        status: 0,
        user_id: userId
      })
    });
    
    const res = await fetch(`${API_BASE}/my/claim/${item.claim_id}/cancel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        item_id: item.item_id
      })
    });
    
    const data = await res.json();
    
    if (data.success) {
      window.showToast('取消找到成功', 'success');
      loadClaim();
    } else {
      window.showToast('取消失败: ' + (data.message || '请重试'), 'error');
    }
  } catch (error) {
    console.error('取消认领失败:', error);
    window.showToast('取消失败，请检查网络连接', 'error');
  }
}

onMounted(() => {
  if (!userId) {
    window.showToast("请先登录", 'warning');
    setTimeout(() => window.location.href = "/login", 1000);
    return;
  }
  loadProfile();
});
</script>

<template>
  <div :style="pageStyle">
    <AppTopBar variant="inner" />
    <div class="container">
      <div class="sidebar">
        <div class="avatar-container">
          <div class="avatar">
            <img v-if="avatarUrl" :src="avatarUrl" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;" />
            <span v-else>👤</span>
          </div>
          <div>
            <div class="username">{{ username }}</div>
            <div class="user-id">{{ userIdText }}</div>
            <div class="signature">{{ signature }}</div>
          </div>
        </div>

        <div class="nav-buttons">
          <button :class="activeBtn('profile')" @click="switchPanel('profile')">个人资料</button>
          <button :class="activeBtn('publish')" @click="switchPanel('publish')">物品发布记录</button>
          <button :class="activeBtn('claim')" @click="switchPanel('claim')">物品认领记录</button>
          <button class="nav-btn" @click="goTo('messages')">通知消息</button>
          <button class="nav-btn" @click="goTo('security')">安全中心</button>
          <button class="nav-btn" @click="goTo('edit')">修改个人资料</button>
          <button class="nav-btn" @click="goTo('home')">返回主页</button>
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
              <label>个性签名：</label>
              <textarea :value="signature" readonly style="margin-bottom: 15px;" />
            </div>
            <div class="description-area">
              <label>个人简介：</label>
              <textarea :value="bio" readonly />
            </div>
          </div>

          <div :class="panelClass('publish')">
            <div class="panel-header">
              <button :class="activePublishBtn('all')" @click="activePublishTab = 'all'">全部记录</button>
              <button :class="activePublishBtn('lost')" @click="activePublishTab = 'lost'">丢失物品</button>
              <button :class="activePublishBtn('found')" @click="activePublishTab = 'found'">拾到物品</button>
            </div>
            <table class="data-table">
              <thead><tr><th>物品名称</th><th>类型</th><th>发布时间</th><th>状态</th><th>操作</th></tr></thead>
              <tbody>
                <tr v-for="item in filteredPublishList" :key="item.item_id">
                  <td>{{ item.title }}</td>
                  <td :class="item.type === 0 ? 'type-lost' : 'type-found'">{{ formatType(item.type) }}</td>
                  <td>{{ item.create_time }}</td>
                  <td>{{ formatStatus(item.status, item.type) }}</td>
                  <td>
                    <a href="#" @click.stop="viewDetail(item)">查看</a>
                    <a v-if="item.status === 0 && item.type === 0" href="#" @click.stop="updateItemStatus(item, 1)" class="status-btn">已找到</a>
                    <a v-if="item.status === 0 && item.type === 1" href="#" @click.stop="updateItemStatus(item, 1)" class="status-btn">已归还</a>
                    <a v-if="item.status === 1 && item.type === 0" href="#" @click.stop="updateItemStatus(item, 0)" class="status-btn cancel">取消找到</a>
                    <a v-if="item.status === 1 && item.type === 1" href="#" @click.stop="updateItemStatus(item, 0)" class="status-btn cancel">取消归还</a>
                    <a href="#" @click.stop="deleteItem(item.item_id)" class="delete-link">删除</a>
                  </td>
                </tr>
                <tr v-if="filteredPublishList.length === 0"><td colspan="5">暂无数据</td></tr>
              </tbody>
            </table>
          </div>

          <div :class="panelClass('claim')">
            <div class="panel-header">
              <div class="panel-tab active">全部记录</div>
            </div>
            <table class="data-table">
              <thead><tr><th>物品名称</th><th>类型</th><th>认领时间</th><th>状态</th><th>操作</th></tr></thead>
              <tbody>
                <tr v-for="item in claimList" :key="item.claim_id">
                  <td>{{ item.title }}</td>
                  <td :class="item.type === 0 ? 'type-lost' : 'type-found'">{{ formatType(item.type) }}</td>
                  <td>{{ item.create_time }}</td>
                  <td>{{ formatClaimStatus(item.status) }}</td>
                  <td>
                    <a href="#" @click.stop="viewDetail(item)">查看</a>
                    <a v-if="item.status === 'approved' || item.status === 1" href="#" @click.stop="cancelClaim(item)" class="status-btn cancel">取消找到</a>
                    <a href="#" @click.stop="deleteClaim(item.claim_id)" class="delete-link">删除</a>
                  </td>
                </tr>
                <tr v-if="claimList.length === 0"><td colspan="5">暂无数据</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <MarkerDetailModal
    :show="showDetailModal"
    :marker="selectedMarker"
    :show-action-buttons="false"
    @close="showDetailModal = false"
  />
</template>

<style scoped src="../assets/个人中心.css"></style>
