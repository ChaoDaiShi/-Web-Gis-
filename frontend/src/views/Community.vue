<!-- 社区页面 -->
<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";

const showToast = window.showToast;
const API_BASE = "http://127.0.0.1:5000/api";
const IMAGE_BASE = "http://127.0.0.1:5000";
const userId = localStorage.getItem("user_id");
const username = localStorage.getItem("username") || "用户";
const router = useRouter();
const unreadCount = ref(0);

const activeTab = ref("recommend");
const notificationTab = ref("comments");
const posts = ref([]);
const currentPost = ref(null);
const showPostDetail = ref(false);
const showCreatePost = ref(false);
const comments = ref([]);
const newComment = ref("");
const replyingTo = ref(null);
const replyContent = ref("");
const notifications = ref([]);
const realNotifications = ref([]);
const followersList = ref([]);
let refreshInterval = null;

const newPost = ref({
  title: "",
  content: "",
  tags: []
});

const defaultImageUrl = ref("http://127.0.0.1:5000/images/tiezifengmian/no_picture_test.jpg");

const postImages = ref([]);
const MAX_IMAGES = 9;
const previewImage = ref(null);
const showImagePreviewModal = ref(false);

const myPosts = ref([]);
const likedPosts = ref([]);
const userProfile = ref({});
const stats = ref({
  post_count: 0,
  received_likes: 0,
  my_likes: 0,
  received_comments: 0,
  my_comments: 0,
  fans: 0,
  following: 0
});

const tags = ref([
  { id: 1, name: "全部", active: true },
  { id: 2, name: "校园生活", active: false },
  { id: 3, name: "学习交流", active: false },
  { id: 4, name: "失物招领", active: false },
  { id: 5, name: "二手交易", active: false },
  { id: 6, name: "活动公告", active: false }
]);

async function loadTags() {
  try {
    const res = await fetch(`${API_BASE}/community/tags`);
    const data = await res.json();
    if (data.success && data.data) {
      tags.value = data.data;
    }
  } catch (e) {
    console.error("加载标签失败:", e);
  }
}

const currentPosts = computed(() => {
  if (activeTab.value === 'recommend') return posts.value;
  if (activeTab.value === 'my') return myPosts.value;
  if (activeTab.value === 'liked') return likedPosts.value;
  return [];
});

const showNotificationsTab = computed(() => activeTab.value === 'notifications');

// 评论通知（所有回复该用户的评论）
const commentNotifications = computed(() => {
  return realNotifications.value.filter(n => 
    n.type === 'comment' || n.type === 'reply' || n.type === 'like_comment'
  );
});

// 关注通知（所有关注该用户的用户）
const followNotifications = computed(() => {
  return followersList.value.map(f => ({
    id: f.user_id,
    user_id: f.user_id,
    username: f.username,
    avatar: f.avatar_url,
    message: '关注了你',
    created_at: ''
  }));
});

// 加载粉丝列表
async function loadFollowersList() {
  if (!userId) return;
  
  try {
    const res = await fetch(`${API_BASE}/community/followers/${userId}?current_user_id=${userId}`);
    const data = await res.json();
    if (data.success) {
      followersList.value = data.data || [];
    }
  } catch (e) {
    console.error("加载粉丝列表失败:", e);
  }
}

function selectTag(tag) {
  tags.value.forEach(t => t.active = false);
  tag.active = true;
}

function formatTime(timeStr) {
  if (!timeStr) return '';
  const date = new Date(timeStr);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前';
  
  return date.toLocaleDateString();
}

function goToHome() {
  router.push("/home");
}

function goToUserProfile(userId) {
  console.log("点击用户主页，用户ID:", userId);
  if (userId) {
    router.push(`/user/${userId}`);
  } else {
    showToast("无法获取用户信息", "error");
  }
}

function showImagePreview(imgSrc) {
  previewImage.value = imgSrc;
  showImagePreviewModal.value = true;
}

function setActiveTab(tab) {
  activeTab.value = tab;
  if (tab === "recommend") {
    loadPosts();
  } else if (tab === "my") {
    loadMyPosts();
  } else if (tab === "liked") {
    loadLikedPosts();
  } else if (tab === "stats") {
    loadStats();
  }
}

async function loadPosts() {
  try {
    const res = await fetch(`${API_BASE}/community/posts?user_id=${userId}`);
    const data = await res.json();
    posts.value = data.success ? data.data : [];
  } catch (e) {
    console.error("加载帖子失败:", e);
    showToast("加载失败", "error");
  }
}

async function loadMyPosts() {
  try {
    const res = await fetch(`${API_BASE}/community/posts/user/${userId}`);
    const data = await res.json();
    myPosts.value = data.success ? data.data : [];
  } catch (e) {
    console.error("加载我的帖子失败:", e);
  }
}

async function loadLikedPosts() {
  try {
    const res = await fetch(`${API_BASE}/community/posts/liked?user_id=${userId}`);
    const data = await res.json();
    likedPosts.value = data.success ? data.data : [];
  } catch (e) {
    console.error("加载点赞帖子失败:", e);
  }
}

async function loadStats() {
  if (!userId) {
    console.warn("用户未登录，无法加载统计数据");
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/community/posts/stats/${userId}`);
    
    if (!res.ok) {
      console.error(`加载统计数据失败: HTTP ${res.status}`);
      return;
    }
    
    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (parseError) {
      console.error("解析统计数据失败，响应内容:", text.substring(0, 200));
      return;
    }
    
    if (data.success && data.data) {
      stats.value.post_count = data.data.post_count || 0;
      stats.value.received_likes = data.data.received_likes || 0;
      stats.value.my_likes = data.data.my_likes || 0;
      stats.value.received_comments = data.data.received_comments || 0;
      stats.value.my_comments = data.data.my_comments || 0;
      stats.value.fans = data.data.fans || 0;
      stats.value.following = data.data.following || 0;
    }
  } catch (e) {
    console.error("加载统计数据失败:", e);
  }
}

async function loadUserProfile() {
  try {
    const res = await fetch(`${API_BASE}/profile?user_id=${userId}`);
    const data = await res.json();
    if (data.success && data.data) {
      userProfile.value = data.data;
    }
  } catch (e) {
    console.error("加载用户信息失败:", e);
  }
}

async function viewPost(postId) {
  try {
    const res = await fetch(`${API_BASE}/community/posts/${postId}?user_id=${userId}`);
    const data = await res.json();
    if (data.success) {
      console.log("帖子详情数据:", data.data);
      currentPost.value = data.data;
      showPostDetail.value = true;
      loadComments(postId);
    }
  } catch (e) {
    console.error("加载帖子详情失败:", e);
  }
}

async function loadComments(postId) {
  try {
    const res = await fetch(`${API_BASE}/community/posts/${postId}/comments?user_id=${userId}`);
    const data = await res.json();
    if (data.success) {
      comments.value = buildCommentTree(data.data);
    } else {
      comments.value = [];
    }
  } catch (e) {
    console.error("加载评论失败:", e);
  }
}

function buildCommentTree(flatComments) {
  const commentMap = new Map();
  const rootComments = [];
  
  flatComments.forEach(comment => {
    comment.replies = [];
    commentMap.set(comment.comment_id, comment);
  });
  
  flatComments.forEach(comment => {
    if (comment.parent_id && commentMap.has(comment.parent_id)) {
      commentMap.get(comment.parent_id).replies.push(comment);
    } else {
      rootComments.push(comment);
    }
  });
  
  return rootComments;
}

async function loadUnreadCount() {
  try {
    const res = await fetch(`${API_BASE}/community/notifications/unread?user_id=${userId}`);
    const data = await res.json();
    unreadCount.value = data.success ? data.count : 0;
  } catch (e) {
    console.error("加载未读数量失败:", e);
    unreadCount.value = 0;
  }
}

async function loadRealNotifications() {
  try {
    const res = await fetch(`${API_BASE}/community/notifications?user_id=${userId}`);
    const data = await res.json();
    if (data.success && data.data) {
      // 保存原始数据
      notifications.value = data.data;
      // 转换数据格式，适配UI显示
      realNotifications.value = data.data.map(n => ({
        id: n.notification_id,
        type: n.type,  // 保存原始类型用于过滤
        username: n.trigger_username || '匿名用户',
        avatar: n.trigger_avatar ? (n.trigger_avatar.startsWith('http') ? n.trigger_avatar : IMAGE_BASE + n.trigger_avatar) : null,
        action: n.type === 'like' ? '赞了你的帖子' : n.type === 'comment' ? '评论了你的帖子' : n.type === 'reply' ? '回复了你的评论' : n.type === 'follow' ? '关注了你' : '系统通知',
        message: n.content || '',
        postImage: n.post_image ? (n.post_image.startsWith('http') ? n.post_image : IMAGE_BASE + n.post_image) : null,
        is_read: n.is_read,
        created_at: n.created_at,
        post_id: n.post_id
      }));
    }
  } catch (e) {
    console.error("加载真实通知失败:", e);
  }
}

async function loadNotifications() {
  try {
    const res = await fetch(`${API_BASE}/community/notifications?user_id=${userId}`);
    const data = await res.json();
    if (data.success) {
      notifications.value = data.data;
    }
  } catch (e) {
    console.error("加载通知失败:", e);
  }
}

function openNotifications() {
  activeTab.value = 'notifications';
  loadRealNotifications();
  loadFollowersList();
}

async function markNotificationAsRead(notificationId) {
  try {
    const res = await fetch(`${API_BASE}/community/notifications/${notificationId}/read?user_id=${userId}`, {
      method: "POST"
    });
    const data = await res.json();
    if (data.success) {
      const notification = realNotifications.value.find(n => n.id === notificationId);
      if (notification) {
        notification.is_read = true;
      }
      loadUnreadCount();
    }
  } catch (e) {
    console.error("标记已读失败:", e);
  }
}

function handleNotificationClick(notification) {
  markNotificationAsRead(notification.id);
  // 在真实数据中找到对应的post_id
  const realNotification = notifications.value.find(n => n.notification_id === notification.id);
  if (realNotification && realNotification.post_id) {
    viewPost(realNotification.post_id);
  }
}

function getTotalCommentsCount() {
  let count = 0;
  
  function countComments(commentList) {
    commentList.forEach(comment => {
      count++;
      if (comment.replies && comment.replies.length > 0) {
        countComments(comment.replies);
      }
    });
  }
  
  countComments(comments.value);
  return count;
}

async function createPost() {
  if (!newPost.value.title.trim() || !newPost.value.content.trim()) {
    showToast("标题和内容不能为空", "warning");
    return;
  }

  try {
    const imagesData = postImages.value.map(img => img.data);
    
    const res = await fetch(`${API_BASE}/community/posts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        title: newPost.value.title,
        content: newPost.value.content,
        images: imagesData,
        tags: newPost.value.tags
      })
    });
    
    const data = await res.json();
    if (data.success) {
      showToast("发布成功", "success");
      // 等待提示框显示完毕后再关闭弹窗（Toast 显示 3000ms）
      setTimeout(() => {
        showCreatePost.value = false;
        newPost.value = { title: "", content: "", tags: [] };
        postImages.value = [];
        loadPosts();
        loadMyPosts();
      }, 3000);
    } else {
      showToast(data.message || "发布失败", "error");
    }
  } catch (e) {
    console.error("发布失败:", e);
    showToast("发布失败", "error");
  }
}

function handleImageUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  if (postImages.value.length >= MAX_IMAGES) {
    showToast(`最多只能上传 ${MAX_IMAGES} 张图片`, "warning");
    return;
  }
  
  const reader = new FileReader();
  reader.onload = function(e) {
    postImages.value.push({
      id: Date.now(),
      data: e.target.result,
      name: file.name
    });
  };
  reader.readAsDataURL(file);
}

function removeImage(index) {
  postImages.value.splice(index, 1);
}

const newTag = ref("");

function addTag() {
  const tag = newTag.value.trim();
  if (tag && !newPost.value.tags.includes(tag)) {
    if (newPost.value.tags.length < 5) {
      newPost.value.tags.push(tag);
      newTag.value = "";
    } else {
      showToast("最多只能添加5个标签", "warning");
    }
  }
}

function removeTag(index) {
  newPost.value.tags.splice(index, 1);
}

function handleTagKeydown(event) {
  if (event.key === 'Enter' || event.key === ',') {
    event.preventDefault();
    addTag();
  }
}

async function toggleLike(post) {
  try {
    const res = await fetch(`${API_BASE}/community/posts/${post.post_id}/like`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      post.likes_count = data.likes_count;
      post.is_liked = data.action === 'liked';
      
      if (currentPost.value && currentPost.value.post_id === post.post_id) {
        currentPost.value.likes_count = data.likes_count;
        currentPost.value.is_liked = data.action === 'liked';
      }
    }
  } catch (e) {
    console.error("点赞失败:", e);
  }
}

async function toggleCommentLike(comment) {
  try {
    const res = await fetch(`${API_BASE}/community/comments/${comment.comment_id}/like`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    
    const data = await res.json();
    if (data.success) {
      comment.likes_count = data.likes_count;
      comment.is_liked = data.action === 'liked';
      
      if (comment.replies && comment.replies.length > 0) {
        comment.replies.forEach(reply => {
          if (reply.comment_id === comment.comment_id) {
            reply.likes_count = data.likes_count;
            reply.is_liked = data.action === 'liked';
          }
        });
      }
    }
  } catch (e) {
    console.error("评论点赞失败:", e);
  }
}

async function submitComment() {
  if (!newComment.value.trim()) {
    showToast("评论内容不能为空", "warning");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/community/posts/${currentPost.value.post_id}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        content: newComment.value
      })
    });
    
    const data = await res.json();
    if (data.success) {
      showToast("评论成功", "success");
      newComment.value = "";
      loadComments(currentPost.value.post_id);
      
      if (currentPost.value.comments_count !== undefined) {
        currentPost.value.comments_count += 1;
      }
      
      const listPost = posts.value.find(p => p.post_id === currentPost.value.post_id);
      if (listPost) {
        listPost.comments_count = (listPost.comments_count || 0) + 1;
      }
    } else {
      showToast(data.message || "评论失败", "error");
    }
  } catch (e) {
    console.error("评论失败:", e);
  }
}

function replyToComment(comment) {
  replyingTo.value = comment.comment_id;
  replyContent.value = "";
}

function cancelReply() {
  replyingTo.value = null;
  replyContent.value = "";
}

async function submitReply(comment) {
  if (!replyContent.value.trim()) {
    showToast("回复内容不能为空", "warning");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/community/posts/${currentPost.value.post_id}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        content: replyContent.value,
        parent_id: comment.comment_id
      })
    });
    
    const data = await res.json();
    if (data.success) {
      showToast("回复成功", "success");
      cancelReply();
      loadComments(currentPost.value.post_id);
      
      if (currentPost.value.comments_count !== undefined) {
        currentPost.value.comments_count += 1;
      }
      
      const listPost = posts.value.find(p => p.post_id === currentPost.value.post_id);
      if (listPost) {
        listPost.comments_count = (listPost.comments_count || 0) + 1;
      }
    } else {
      showToast(data.message || "回复失败", "error");
    }
  } catch (e) {
    console.error("回复失败:", e);
  }
}

async function deletePost(postId) {
  if (!confirm("确定要删除这篇帖子吗？")) return;
  
  try {
    const res = await fetch(`${API_BASE}/community/posts/${postId}?user_id=${userId}`, {
      method: "DELETE"
    });
    
    const data = await res.json();
    if (data.success) {
      showToast("删除成功", "success");
      showPostDetail.value = false;
      currentPost.value = null;
      loadPosts();
      loadMyPosts();
    } else {
      showToast(data.message || "删除失败", "error");
    }
  } catch (e) {
    console.error("删除失败:", e);
  }
}

async function toggleFollow(followeeId) {
  if (!userId) {
    showToast("请先登录", "warning");
    return;
  }
  
  if (parseInt(userId) === parseInt(followeeId)) {
    return;
  }
  
  try {
    const res = await fetch(`${API_BASE}/community/follow`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        follower_id: userId,
        followee_id: followeeId
      })
    });
    
    const data = await res.json();
    if (data.success) {
      // 更新帖子列表中的关注状态
      posts.value.forEach(post => {
        if (post.user_id === followeeId) {
          post.is_following = data.action === 'followed';
        }
      });
      
      // 更新当前帖子详情中的关注状态
      if (currentPost.value && currentPost.value.user_id === followeeId) {
        currentPost.value.is_following = data.action === 'followed';
      }
      
      // 更新我的帖子列表中的关注状态
      myPosts.value.forEach(post => {
        if (post.user_id === followeeId) {
          post.is_following = data.action === 'followed';
        }
      });
      
      // 更新点赞帖子列表中的关注状态
      likedPosts.value.forEach(post => {
        if (post.user_id === followeeId) {
          post.is_following = data.action === 'followed';
        }
      });
      
      showToast(data.action === 'followed' ? '关注成功' : '已取消关注', 'success');
    } else {
      showToast(data.message || '操作失败', 'error');
    }
  } catch (e) {
    console.error("关注操作失败:", e);
    showToast("操作失败", "error");
  }
}

function canDeleteComment(comment) {
  if (!userId) return false;
  const isPostOwner = currentPost.value && currentPost.value.user_id == userId;
  const isCommentOwner = comment.user_id == userId;
  return isPostOwner || isCommentOwner;
}

async function deleteComment(commentId) {
  if (!confirm("确定要删除这条评论吗？")) return;
  
  try {
    const res = await fetch(`${API_BASE}/community/comments/${commentId}?user_id=${userId}`, {
      method: "DELETE"
    });
    
    const data = await res.json();
    if (data.success) {
      showToast("删除成功", "success");
      loadComments(currentPost.value.post_id);
      
      if (currentPost.value.comments_count !== undefined) {
        currentPost.value.comments_count = Math.max(0, currentPost.value.comments_count - 1);
      }
    }
  } catch (e) {
    console.error("删除评论失败:", e);
  }
}

onMounted(() => {
  loadPosts();
  loadUserProfile();
  loadUnreadCount();
  loadTags();
  refreshInterval = setInterval(loadUnreadCount, 30000);
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>

<template>
  <div class="community-page">
    <AppTopBar variant="home">
      <template #back>
        <button class="app-topbar__back-btn" @click="goToHome" title="返回主页">
          ←
        </button>
      </template>
    </AppTopBar>
    
    <div class="community-container">
      <div class="sidebar-wrapper">
        <div class="sidebar">
          <div class="user-card">
            <div class="avatar">
              <img v-if="userProfile.avatar" :src="userProfile.avatar.startsWith('http') ? userProfile.avatar : IMAGE_BASE + userProfile.avatar" alt="头像" />
              <div v-else class="avatar-placeholder">{{ username.charAt(0) }}</div>
            </div>
            <div class="user-info">
              <div class="username">{{ username }}</div>
            </div>
          </div>
          
          <div class="nav-menu">
            <div 
              class="nav-item" 
              :class="{ active: activeTab === 'recommend' }"
              @click="setActiveTab('recommend')"
            >
              <span class="text">社区</span>
            </div>
            <div 
              class="nav-item" 
              :class="{ active: activeTab === 'my' }"
              @click="setActiveTab('my')"
            >
              <span class="text">我的帖子</span>
            </div>
            <div 
              class="nav-item" 
              :class="{ active: activeTab === 'notifications' }"
              @click="openNotifications"
            >
              <span class="text">消息通知</span>
              <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
            </div>
            <div 
              class="nav-item" 
              :class="{ active: activeTab === 'stats' }"
              @click="setActiveTab('stats')"
            >
              <span class="text">数据汇总</span>
            </div>
          </div>
          
          <button class="create-btn" @click="showCreatePost = true">
            <span>+ 发布帖子</span>
          </button>
        </div>
      </div>
      
      <div class="main-content">
        <div v-if="activeTab === 'recommend' || activeTab === 'my' || activeTab === 'liked'" class="content-area">
          <div class="tags-bar">
            <div 
              v-for="tag in tags" 
              :key="tag.id"
              class="tag-item"
              :class="{ active: tag.active }"
              @click="selectTag(tag)"
            >
              {{ tag.name }}
            </div>
          </div>
          
          <div class="posts-grid">
            <div 
              v-for="post in currentPosts" 
              :key="post.post_id" 
              class="post-card"
              @click="viewPost(post.post_id)"
            >
              <div class="post-image-wrapper">
                <img 
                  :src="post.images && post.images.length > 0 ? (post.images[0].startsWith('http') ? post.images[0] : IMAGE_BASE + post.images[0]) : defaultImageUrl" 
                  alt="帖子图片"
                  class="post-image"
                />
              </div>
              <div class="post-info">
                <div class="post-title">{{ post.title }}</div>
                <div class="post-tags" v-if="post.tags && post.tags.length > 0">
                  <span v-for="(tag, idx) in post.tags.slice(0, 3)" :key="idx" class="post-tag">
                    #{{ tag }}
                  </span>
                </div>
                <div class="post-meta">
                  <span class="author-avatar-mini" @click.stop="goToUserProfile(post.user_id)" style="cursor: pointer;">
                    <img 
                      v-if="post.author_avatar" 
                      :src="IMAGE_BASE + post.author_avatar" 
                      alt="头像"
                      @error="(e) => { e.target.style.display = 'none'; e.target.parentElement.classList.add('no-image'); }"
                    />
                    <span v-else>{{ post.author_name?.charAt(0) || '匿' }}</span>
                  </span>
                  <span class="author-name" @click.stop="goToUserProfile(post.user_id)" style="cursor: pointer;">{{ post.author_name || '匿名用户' }}</span>
                  <button 
                    v-if="post.user_id != userId"
                    class="follow-btn-small"
                    :class="{ following: post.is_following }"
                    @click.stop="toggleFollow(post.user_id)"
                  >
                    {{ post.is_following ? '已关注' : '+关注' }}
                  </button>
                  <span class="stats">
                    <span class="like-icon">{{ post.is_liked ? '❤️' : '🤍' }}</span>
                    <span>{{ post.likes_count || 0 }}</span>
                    <span class="comment-icon">💬</span>
                    <span>{{ post.comments_count || 0 }}</span>
                  </span>
                </div>
              </div>
            </div>
            
            <div v-if="currentPosts.length === 0" class="empty-state">
              <p>暂无内容</p>
            </div>
          </div>
        </div>
        
        <div v-if="activeTab === 'notifications'" class="notifications-area">
          <h2>消息通知</h2>
          
          <div class="notification-tabs">
            <button 
              :class="{ active: notificationTab === 'comments' }"
              @click="notificationTab = 'comments'"
            >
              新增评论
            </button>
            <button 
              :class="{ active: notificationTab === 'follows' }"
              @click="notificationTab = 'follows'"
            >
              新增关注
            </button>
          </div>
          
          <div v-if="notificationTab === 'comments'" class="notification-list-container">
            <div v-if="commentNotifications.length === 0" class="empty-state">
              <p>暂无新评论</p>
            </div>
            <div v-else class="notifications-list">
              <div 
                v-for="notification in commentNotifications" 
                :key="notification.id"
                class="notification-item"
                :class="{ unread: !notification.is_read }"
                @click="handleNotificationClick(notification)"
              >
                <div class="notification-avatar">
                  <img v-if="notification.avatar" :src="notification.avatar.startsWith('http') ? notification.avatar : IMAGE_BASE + notification.avatar" alt="头像" />
                  <div v-else class="avatar-placeholder">{{ notification.username?.charAt(0) || '匿' }}</div>
                </div>
                <div class="notification-content">
                  <div class="notification-name">{{ notification.username }}</div>
                  <div class="notification-message">{{ notification.message }}</div>
                </div>
                <div class="notification-image" v-if="notification.postImage">
                  <img :src="notification.postImage.startsWith('http') ? notification.postImage : IMAGE_BASE + notification.postImage" alt="帖子图片" />
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="notificationTab === 'follows'" class="notification-list-container">
            <div v-if="followNotifications.length === 0" class="empty-state">
              <p>暂无新关注</p>
            </div>
            <div v-else class="notifications-list">
              <div 
                v-for="notification in followNotifications" 
                :key="notification.id"
                class="notification-item"
                :class="{ unread: !notification.is_read }"
                @click="handleNotificationClick(notification)"
              >
                <div class="notification-avatar">
                  <img v-if="notification.avatar" :src="notification.avatar.startsWith('http') ? notification.avatar : IMAGE_BASE + notification.avatar" alt="头像" />
                  <div v-else class="avatar-placeholder">{{ notification.username?.charAt(0) || '匿' }}</div>
                </div>
                <div class="notification-content">
                  <div class="notification-name">{{ notification.username }}</div>
                  <div class="notification-message">{{ notification.message }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="activeTab === 'stats'" class="stats-area">
          <h2>数据汇总</h2>
          <div class="stats-section">
            <h3>互动数据</h3>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-value">{{ stats.post_count }}</div>
                <div class="stat-label">我的帖子</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ stats.fans }}</div>
                <div class="stat-label">我的粉丝</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ stats.following }}</div>
                <div class="stat-label">我的关注</div>
              </div>
            </div>
          </div>
          
          <div class="stats-section">
            <h3>点赞</h3>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-value">{{ stats.received_likes }}</div>
                <div class="stat-label">获得点赞</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ stats.my_likes }}</div>
                <div class="stat-label">我的点赞</div>
              </div>
            </div>
          </div>
          
          <div class="stats-section">
            <h3>评论</h3>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-value">{{ stats.received_comments }}</div>
                <div class="stat-label">收到评论</div>
              </div>
              <div class="stat-card">
                <div class="stat-value">{{ stats.my_comments }}</div>
                <div class="stat-label">我的评论</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showPostDetail && currentPost" class="modal-overlay" @click="showPostDetail = false">
      <div class="modal-content post-detail-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ currentPost.title }}</h3>
          <button class="close-btn" @click="showPostDetail = false">×</button>
        </div>
        <div class="modal-body">
          <div class="post-author">
            <div class="author-avatar" @click="goToUserProfile(currentPost.user_id)" style="cursor: pointer;">
              <img v-if="currentPost.author_avatar" :src="IMAGE_BASE + currentPost.author_avatar" alt="头像" />
              <div v-else class="avatar-placeholder">{{ currentPost.author_name?.charAt(0) || '匿' }}</div>
            </div>
            <div class="author-info">
              <span class="name" @click="goToUserProfile(currentPost.user_id)" style="cursor: pointer;">{{ currentPost.author_name || '匿名用户' }}</span>
              <span class="time">{{ formatTime(currentPost.created_at) }}</span>
            </div>
            <div class="author-actions">
              <button 
                v-if="currentPost.user_id != userId" 
                class="follow-btn"
                :class="{ following: currentPost.is_following }"
                @click="toggleFollow(currentPost.user_id)"
              >
                {{ currentPost.is_following ? '已关注' : '+关注' }}
              </button>
              <button 
                v-if="currentPost.user_id == userId" 
                class="delete-btn"
                @click="deletePost(currentPost.post_id)"
              >删除</button>
            </div>
          </div>
          
          <div class="post-content-full">{{ currentPost.content }}</div>
          
          <div v-if="currentPost.images && currentPost.images.length > 0" class="post-images-full">
            <img 
              v-for="(img, idx) in currentPost.images" 
              :key="idx" 
              :src="img.startsWith('http') ? img : IMAGE_BASE + img" 
              alt="帖子图片"
              @click="showImagePreview(img)"
            />
          </div>
          
          <div class="post-actions">
            <div class="action-item" @click="toggleLike(currentPost)">
              <span :class="{ liked: currentPost.is_liked }">{{ currentPost.is_liked ? '❤️' : '🤍' }}</span>
              <span>{{ currentPost.likes_count || 0 }}</span>
            </div>
            <div class="action-item">
              <span>💬</span>
              <span>{{ currentPost.comments_count || 0 }}</span>
            </div>
          </div>
          
          <div class="comments-section">
            <h4>评论 ({{ getTotalCommentsCount() }})</h4>
            
            <div class="comment-input">
              <textarea v-model="newComment" placeholder="写下你的评论..."></textarea>
              <button @click="submitComment">发送</button>
            </div>
            
            <div class="comments-list">
              <div v-for="comment in comments" :key="comment.comment_id" class="comment-item">
                <div class="comment-avatar" @click="goToUserProfile(comment.user_id)" style="cursor: pointer;">
                  <img v-if="comment.author_avatar" :src="comment.author_avatar.startsWith('http') ? comment.author_avatar : IMAGE_BASE + comment.author_avatar" alt="头像" />
                  <div v-else class="avatar-placeholder">{{ comment.author_name?.charAt(0) || '匿' }}</div>
                </div>
                <div class="comment-body">
                  <div class="comment-header">
                    <span class="comment-author" @click="goToUserProfile(comment.user_id)" style="cursor: pointer;">{{ comment.author_name || '匿名用户' }}</span>
                    <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
                  </div>
                  <div class="comment-content">{{ comment.content }}</div>
                  <div class="comment-actions">
                    <span class="action" @click="toggleCommentLike(comment)">
                      {{ comment.is_liked ? '❤️' : '🤍' }} {{ comment.likes_count || 0 }}
                    </span>
                    <span class="action" @click="replyToComment(comment)">回复</span>
                    <span v-if="canDeleteComment(comment)" class="action delete" @click="deleteComment(comment.comment_id)">删除</span>
                  </div>
                  
                  <div v-if="replyingTo === comment.comment_id" class="reply-input">
                    <textarea v-model="replyContent" placeholder="写下你的回复..."></textarea>
                    <div class="reply-actions">
                      <button @click="cancelReply">取消</button>
                      <button @click="submitReply(comment)">发送</button>
                    </div>
                  </div>
                  
                  <div v-if="comment.replies && comment.replies.length > 0" class="replies">
                    <div v-for="reply in comment.replies" :key="reply.comment_id" class="reply-item">
                      <div class="comment-avatar small" @click="goToUserProfile(reply.user_id)" style="cursor: pointer;">
                        <img v-if="reply.author_avatar" :src="reply.author_avatar.startsWith('http') ? reply.author_avatar : IMAGE_BASE + reply.author_avatar" alt="头像" />
                        <div v-else class="avatar-placeholder">{{ reply.author_name?.charAt(0) || '匿' }}</div>
                      </div>
                      <div class="reply-body">
                        <span class="reply-author" @click="goToUserProfile(reply.user_id)" style="cursor: pointer;">{{ reply.author_name || '匿名用户' }}</span>
                        <span class="reply-content">{{ reply.content }}</span>
                        <span class="reply-time">{{ formatTime(reply.created_at) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showCreatePost" class="modal-overlay" @click="showCreatePost = false">
      <div class="modal-content create-post-modal" @click.stop>
        <div class="modal-header">
          <h3>发布帖子</h3>
          <button class="close-btn" @click="showCreatePost = false">×</button>
        </div>
        <div class="modal-body">
          <input v-model="newPost.title" type="text" placeholder="标题" class="title-input" />
          <textarea v-model="newPost.content" placeholder="分享你的想法..." class="content-input"></textarea>
          
          <div class="tags-input-section">
            <div class="tags-display">
              <span v-for="(tag, idx) in newPost.tags" :key="idx" class="tag-chip">
                {{ tag }}
                <button class="tag-remove" @click="removeTag(idx)">×</button>
              </span>
            </div>
            <input 
              v-model="newTag" 
              type="text" 
              placeholder="输入标签，按回车添加（最多5个）" 
              class="tag-input"
              @keydown="handleTagKeydown"
              @blur="addTag"
            />
          </div>
          
          <div class="images-upload">
            <div v-for="(img, idx) in postImages" :key="img.id" class="image-preview">
              <img :src="img.data" alt="预览" />
              <button class="remove-btn" @click="removeImage(idx)">×</button>
            </div>
            <label v-if="postImages.length < MAX_IMAGES" class="upload-btn">
              <input type="file" accept="image/*" @change="handleImageUpload" hidden />
              <span>+</span>
            </label>
          </div>
          
          <button class="submit-btn" @click="createPost">发布</button>
        </div>
      </div>
    </div>
    
    <div v-if="showImagePreviewModal" class="modal-overlay" @click="showImagePreviewModal = false">
      <div class="image-preview-modal" @click.stop>
        <img :src="previewImage" alt="预览" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.community-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.community-container {
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  gap: 20px;
}

.sidebar-wrapper {
  width: 200px;
  flex-shrink: 0;
  position: sticky;
  top: 20px;
  align-self: flex-start;
}

.sidebar {
  width: 100%;
}

.user-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  margin-bottom: 16px;
}

.avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  margin: 0 auto 12px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.username {
  font-weight: 600;
  color: #333;
}

.nav-menu {
  background: white;
  border-radius: 12px;
  padding: 8px;
  margin-bottom: 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #f5f5f5;
}

.nav-item.active {
  background: #e8f4fd;
  color: #1890ff;
}

.nav-item .icon {
  margin-right: 8px;
}

.create-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  margin-bottom: 16px;
}

.create-btn:hover {
  opacity: 0.9;
}

.notification-entry {
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.notification-entry .icon {
  margin-right: 8px;
}

.notification-entry .badge {
  margin-left: auto;
  background: #ff4d4f;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.content-area {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.notifications-area {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.notifications-area h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: #333;
}

.notification-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.notification-tabs button {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}

.notification-tabs button:hover {
  border-color: #667eea;
  color: #667eea;
}

.notification-tabs button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.notification-list-container {
  min-height: 200px;
}

.tags-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tag-item {
  padding: 6px 16px;
  background: #f5f5f5;
  border-radius: 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.tag-item:hover {
  background: #e8e8e8;
}

.tag-item.active {
  background: #1890ff;
  color: white;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.post-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.post-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.post-image-wrapper {
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  background: #f5f5f5;
}

.post-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.post-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.placeholder-icon {
  font-size: 48px;
  opacity: 0.5;
}

.post-info {
  padding: 12px;
}

.post-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.post-tag {
  font-size: 12px;
  color: #667eea;
  background: #f0f2ff;
  padding: 2px 8px;
  border-radius: 8px;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.author-avatar-mini {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 12px;
  border: none;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
  padding: 0;
  margin: 0;
  line-height: 24px;
  text-align: center;
  vertical-align: middle;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.author-avatar-mini img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.author-avatar-mini span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.author-name {
  color: #666;
  flex-shrink: 0;
}

.stats {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  color: #999;
}

.like-icon, .comment-icon {
  font-size: 12px;
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.author-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.author-avatar .avatar-placeholder {
  font-size: 14px;
}

.post-time {
  font-size: 12px;
  color: #999;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #666;
}

.stat-item .liked {
  color: #ff4d4f;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.stats-area {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.stats-area h2 {
  margin-bottom: 20px;
  color: #333;
}

.stats-section {
  margin-bottom: 24px;
}

.stats-section h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #666;
  font-weight: normal;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-card {
  background: #fafafa;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #1890ff;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 20px;
}

.post-detail-modal {
  width: 700px;
}

.post-author {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.post-author .author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.post-author .name {
  font-weight: 600;
}

.post-author .time {
  font-size: 12px;
  color: #999;
}

.delete-btn {
  padding: 4px 12px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.post-content-full {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
  margin-bottom: 16px;
}

.post-images-full {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.post-images-full img {
  width: 150px;
  height: 150px;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
}

.post-actions {
  display: flex;
  gap: 20px;
  padding: 12px 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.comments-section {
  margin-top: 20px;
}

.comments-section h4 {
  margin-bottom: 16px;
}

.comment-input {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.comment-input textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  height: 60px;
}

.comment-input button {
  padding: 0 20px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.comment-avatar.small {
  width: 28px;
  height: 28px;
}

.comment-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.comment-body {
  flex: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.comment-author {
  font-weight: 600;
  font-size: 14px;
}

.comment-time {
  font-size: 12px;
  color: #999;
}

.comment-content {
  font-size: 14px;
  line-height: 1.5;
}

.comment-actions {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.comment-actions .action {
  font-size: 12px;
  color: #666;
  cursor: pointer;
}

.comment-actions .action.delete {
  color: #ff4d4f;
}

.reply-input {
  margin-top: 12px;
}

.reply-input textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  height: 50px;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.reply-actions button {
  padding: 4px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  background: white;
}

.reply-actions button:last-child {
  background: #1890ff;
  color: white;
  border-color: #1890ff;
}

.replies {
  margin-top: 12px;
  padding-left: 20px;
  border-left: 2px solid #eee;
}

.reply-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.reply-body {
  font-size: 13px;
}

.reply-author {
  font-weight: 600;
  margin-right: 8px;
}

.reply-content {
  color: #333;
}

.reply-time {
  color: #999;
  margin-left: 8px;
}

.create-post-modal {
  width: 500px;
}

.title-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 16px;
}

.content-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  height: 150px;
  margin-bottom: 12px;
}

.tags-input-section {
  margin-bottom: 12px;
}

.tags-display {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px;
  font-size: 14px;
}

.tag-remove {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  margin-left: 4px;
  opacity: 0.8;
}

.tag-remove:hover {
  opacity: 1;
}

.tag-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.images-upload {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.image-preview {
  position: relative;
  width: 80px;
  height: 80px;
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.image-preview .remove-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
}

.upload-btn {
  width: 80px;
  height: 80px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.upload-btn span {
  font-size: 24px;
  color: #999;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}

.image-preview-modal {
  max-width: 90vw;
  max-height: 90vh;
}

.image-preview-modal img {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
}

.notifications-modal {
  width: 100%;
  max-width: 900px;
  height: 80vh;
  display: flex;
  flex-direction: column;
  background: #f4f4f5;
  border-radius: 16px;
  overflow: hidden;
}

.notifications-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.notifications-tabs {
  display: flex;
  gap: 12px;
}

.notification-tab {
  padding: 8px 24px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  transition: all 0.2s;
  background: transparent;
}

.notification-tab:hover {
  background: #f3f4f6;
}

.notification-tab.active {
  background: #000;
  color: white;
}

.notifications-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #e9e9eb;
  cursor: pointer;
  transition: all 0.2s;
}

.notification-item:hover {
  background: #dcdcdc;
}

.notification-item.unread {
  background: #e5e7eb;
}

.notification-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.notification-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-name {
  font-size: 14px;
  font-weight: 600;
  color: #000;
  margin-bottom: 2px;
}

.notification-action {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 14px;
  color: #374151;
  line-height: 1.4;
}

.notification-image {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.notification-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.notifications-footer {
  padding: 16px 20px;
  background: transparent;
  display: flex;
  justify-content: flex-end;
}

.notification-settings-btn {
  padding: 10px 28px;
  background: #ff6b9d;
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.notification-settings-btn:hover {
  background: #ff5288;
}

.follow-btn-small {
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.follow-btn-small:hover {
  opacity: 0.9;
}

.follow-btn-small.following {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.follow-btn-small.following:hover {
  background: #e5e7eb;
}

.follow-btn {
  padding: 8px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.follow-btn:hover {
  opacity: 0.9;
}

.follow-btn.following {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.follow-btn.following:hover {
  background: #e5e7eb;
}

.author-actions {
  display: flex;
  gap: 8px;
}
</style>