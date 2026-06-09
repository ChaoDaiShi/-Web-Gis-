<script setup>
defineProps({
  type: {
    type: String,
    default: 'card'
  },
  count: {
    type: Number,
    default: 3
  }
});
</script>

<template>
  <div class="skeleton-container">
    <template v-if="type === 'card'">
      <div v-for="i in count" :key="i" class="skeleton-card">
        <div class="skeleton-image"></div>
        <div class="skeleton-content">
          <div class="skeleton-title"></div>
          <div class="skeleton-text"></div>
          <div class="skeleton-text short"></div>
        </div>
      </div>
    </template>

    <template v-else-if="type === 'list'">
      <div v-for="i in count" :key="i" class="skeleton-list-item">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-info">
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
      </div>
    </template>

    <template v-else-if="type === 'profile'">
      <div class="skeleton-profile">
        <div class="skeleton-avatar-lg"></div>
        <div class="skeleton-profile-content">
          <div class="skeleton-title-lg"></div>
          <div class="skeleton-text"></div>
        </div>
        <div class="skeleton-stats">
          <div class="skeleton-stat">
            <div class="skeleton-number"></div>
            <div class="skeleton-label"></div>
          </div>
          <div class="skeleton-stat">
            <div class="skeleton-number"></div>
            <div class="skeleton-label"></div>
          </div>
          <div class="skeleton-stat">
            <div class="skeleton-number"></div>
            <div class="skeleton-label"></div>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="type === 'empty'">
      <div class="skeleton-empty">
        <div class="skeleton-circle"></div>
        <div class="skeleton-text"></div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.skeleton-container {
  width: 100%;
}

.skeleton-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  margin-bottom: 12px;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-image {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
}

.skeleton-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-title {
  height: 24px;
  width: 70%;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
}

.skeleton-text {
  height: 16px;
  width: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
}

.skeleton-text.short {
  width: 60%;
}

.skeleton-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skeleton-line {
  height: 14px;
  width: 80%;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
}

.skeleton-line.short {
  width: 50%;
}

.skeleton-profile {
  text-align: center;
  padding: 30px;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-avatar-lg {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  margin: 0 auto 20px;
}

.skeleton-profile-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  margin-bottom: 24px;
}

.skeleton-title-lg {
  height: 28px;
  width: 30%;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
}

.skeleton-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.skeleton-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.skeleton-number {
  height: 24px;
  width: 40px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
}

.skeleton-label {
  height: 12px;
  width: 60px;
  border-radius: 4px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
}

.skeleton-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

.skeleton-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  margin-bottom: 16px;
}

@keyframes skeleton-loading {
  0% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.8;
  }
  100% {
    opacity: 0.4;
  }
}
</style>