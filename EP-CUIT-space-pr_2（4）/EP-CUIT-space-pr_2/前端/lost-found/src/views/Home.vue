<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";
import SearchResultModal from "../components/SearchResultModal.vue";
import MarkerDetailModal from "../components/MarkerDetailModal.vue";
import PublishModal from "../components/PublishModal.vue";
import ListPanel from "../components/ListPanel.vue";

const router = useRouter();

const API_BASE = "http://127.0.0.1:5000/api";
const mapContainerId = "mapContainer";

const statusText = ref("点击地图任意位置可发布标记");
const searchInput = ref("");
const is3D = ref(true);
const mode = ref("normal");
const listExpanded = ref(false);
const filterStatus = ref("all");
const isDoubleClick = ref(false);
let clickTimer = null;

const markers = ref([]);
const markerObjs = ref([]);
const highlightId = ref("");
const selectedMarker = ref(null);
const pendingWorldPoint = ref(null);
const mapRef = ref(null);

const showPublishModal = ref(false);
const categories = ref([]);

const showDetailModal = ref(false);
const showSearchModal = ref(false);
const searchResults = ref([]);
const avatarUrl = ref("");
const username = ref("");

async function loadUserInfo() {
  const userId = localStorage.getItem("user_id");
  if (!userId) return;

  try {
    const res = await fetch(`http://127.0.0.1:5000/api/profile?user_id=${userId}`);
    const data = await res.json();
    if (data.success && data.data) {
      if (data.data.avatar) {
        avatarUrl.value = `http://127.0.0.1:5000${data.data.avatar}`;
      }
      username.value = data.data.username || "";
    }
  } catch (e) {
    console.error("加载用户信息失败:", e);
  }
}

async function loadCategories() {
  try {
    const res = await fetch(`${API_BASE}/admin/categories`);
    const data = await res.json();
    if (data && Array.isArray(data)) {
      categories.value = data;
      if (categories.value.length > 0) {
        pubCategory.value = categories.value[0].category_id;
      }
    }
  } catch (e) {
    console.error("加载分类失败:", e);
  }
}

function getInitial() {
  return username.value ? username.value.charAt(0).toUpperCase() : "用";
}

const appClass = computed(() => {
  if (mode.value === "fullmap") return "app fullmap";
  if (mode.value === "split") return "app split";
  return "app";
});

const leftArrowStyle = computed(() => ({
  left: listExpanded.value ? "50vw" : "var(--list-width)",
}));

const filteredMarkers = computed(() => {
  if (filterStatus.value === "all") return markers.value;
  const statusValue = filterStatus.value === "lost" ? 0 : 1;
  return markers.value.filter(m => m.status === statusValue);
});

const isMapClickAdd = computed(() => pendingWorldPoint.value !== null);

function setStatus(message) {
  statusText.value = message;
}

function centerToPoint(lng, lat) {
  if (!mapRef.value || !lng || !lat) return;
  mapRef.value.setCenter([lng, lat]);
}

function hasCoordinates(item) {
  return item.lng && item.lat && !isNaN(item.lng) && !isNaN(item.lat);
}

function handleRemoveMarker(markerId) {
  const index = markers.value.findIndex(m => m.id === markerId);
  if (index !== -1) {
    markers.value.splice(index, 1);
    renderMarkers();
  }
}

function renderMarkers() {
  if (!mapRef.value || !window.AMap) return;

  markerObjs.value.forEach((m) => m.setMap(null));
  markerObjs.value = [];

  filteredMarkers.value.forEach((m) => {
    if (!m.lng || !m.lat || isNaN(m.lng) || isNaN(m.lat)) return;

    const isLost = m.type === 0;
    const markerColor = isLost ? "marker-lost" : "marker-found";

    const marker = new window.AMap.Marker({
      position: [m.lng, m.lat],
      map: mapRef.value,
      title: m.title,
      offset: new window.AMap.Pixel(-17, -48),
      content: `
        <div class="marker-wrap ${markerColor} ${String(highlightId.value) === String(m.id) ? "highlight" : ""}">
          <div class="marker-wave"></div>
          <div class="marker-core"></div>
          <div class="marker-label">${m.title || "未命名标记"}</div>
        </div>
      `,
    });

    marker.on("click", () => {
      highlightId.value = m.id;
      selectedMarker.value = m;
      showDetailModal.value = true;
      renderMarkers();
    });

    markerObjs.value.push(marker);
  });
}

async function loadMarkers() {
  try {
    const res = await fetch(`${API_BASE}/map/markers`);
    const data = await res.json();
    if (!data.success) {
      setStatus("标记加载失败");
      return;
    }

    const currentUserId = localStorage.getItem("user_id");

    markers.value = (data.data || []).map((item, index) => {
      let images = [];
      if (item.image_urls) {
        if (Array.isArray(item.image_urls)) {
          images = item.image_urls;
        } else if (typeof item.image_urls === 'string' && item.image_urls.trim()) {
          try {
            const trimmed = item.image_urls.trim();
            if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
              images = JSON.parse(trimmed);
            } else if (trimmed.includes(',')) {
              images = trimmed.split(',').map(url => url.trim()).filter(url => url);
            } else {
              images = [trimmed];
            }
          } catch (e) {
            console.warn("解析图片URL失败:", e);
            images = [];
          }
        }
      }
      return {
        id: item.item_id || item.location_id || index + 1,
        title: item.title || item.name || "未命名标记",
        detail: item.description || "",
        lng: item.lng || item.longitude ? Number(item.lng ?? item.longitude) : null,
        lat: item.lat ?? item.latitude ? Number(item.lat ?? item.latitude) : null,
        time: item.create_time || "",
        status: item.status ?? 0,
        phone: item.phone || "",
        publisher_id: item.publisher_id,
        type: item.type ?? 0,
        images: Array.isArray(images) ? images.map(img => {
          if (typeof img === 'string') {
            if (img.startsWith('http://') || img.startsWith('https://')) {
              return img;
            }
            if (img.startsWith('/')) {
              return `http://127.0.0.1:5000${img}`;
            }
            return `http://127.0.0.1:5000/${img}`;
          }
          return '';
        }).filter(img => img) : [],
      };
    }).sort((a, b) => {
      const isCurrentUserA = String(a.publisher_id) === String(currentUserId);
      const isCurrentUserB = String(b.publisher_id) === String(currentUserId);
      const statusA = a.status;
      const statusB = b.status;

      const getPriority = (isCurrentUser, status) => {
        if (isCurrentUser && status === 0) return 0;
        if (isCurrentUser && status === 1) return 1;
        if (!isCurrentUser && status === 0) return 2;
        return 3;
      };

      return getPriority(isCurrentUserA, statusA) - getPriority(isCurrentUserB, statusB);
    });

    renderMarkers();
    setStatus("标记加载成功");
  } catch (error) {
    console.error(error);
    setStatus("标记接口异常");
  }
}

function initMap(config) {
  mapRef.value = new window.AMap.Map(mapContainerId, {
    zoom: config.zoom || 18,
    center: [config.center_lng, config.center_lat],
    viewMode: "3D",
    pitch: 45,
    showIndoorMap: false,
  });

  const bounds = new window.AMap.Bounds(
    [config.sw_lng, config.sw_lat],
    [config.ne_lng, config.ne_lat],
  );
  mapRef.value.setBounds(bounds);
  mapRef.value.setZooms([16, 20]);

  mapRef.value.on("click", (e) => {
    pendingWorldPoint.value = { lng: e.lnglat.lng, lat: e.lnglat.lat };
    showPublishModal.value = true;
  });
}

async function loadDefaultMap() {
  try {
    const res = await fetch(`${API_BASE}/map/default`);
    const config = await res.json();
    if (!config || config.error) {
      setStatus("地图加载失败");
      return;
    }
    initMap(config);
  } catch (error) {
    console.error(error);
    setStatus("地图接口异常");
  }
}

async function openAddModal() {
  pendingWorldPoint.value = null;
  showPublishModal.value = true;
}

function handlePublishSubmit(data) {
  setStatus("发布成功");
  pendingWorldPoint.value = null;
  loadMarkers();
}

function handlePublishClose() {
  pendingWorldPoint.value = null;
  showPublishModal.value = false;
}

function handleClearLocation() {
  pendingWorldPoint.value = null;
}

function handleSelectLocation() {
  showPublishModal.value = false;
  setStatus('请在地图上点击选择位置');
}

function handleItemClick(item) {
  highlightId.value = item.id;
  
  if (clickTimer) {
    clearTimeout(clickTimer);
    return;
  }
  
  clickTimer = setTimeout(() => {
    if (hasCoordinates(item)) {
      centerToPoint(item.lng, item.lat);
      renderMarkers();
    }
    clickTimer = null;
  }, 250);
}

function calculateSimilarity(text, keyword) {
  const textLower = text.toLowerCase();
  const keywordLower = keyword.toLowerCase();
  
  if (!keywordLower || !textLower) return 0;
  
  const textLen = textLower.length;
  const keyLen = keywordLower.length;
  
  if (keyLen > textLen) return 0;
  
  let matchCount = 0;
  let lastIndex = -1;
  let positionBonus = 0;
  
  for (let i = 0; i < keyLen; i++) {
    const idx = textLower.indexOf(keywordLower[i], lastIndex + 1);
    if (idx === -1) return 0;
    
    matchCount++;
    if (i === 0 && idx === 0) {
      positionBonus += 0.3;
    } else if (idx === lastIndex + 1) {
      positionBonus += 0.1;
    }
    lastIndex = idx;
  }
  
  const matchRatio = matchCount / keyLen;
  const textCoverage = keyLen / Math.min(textLen, keyLen * 2);
  const titleBonus = textLower.startsWith(keywordLower) ? 0.2 : 0;
  
  return matchRatio * 0.5 + textCoverage * 0.2 + positionBonus + titleBonus;
}

function searchByKeyword() {
  const key = searchInput.value.trim().toLowerCase();
  if (!key) {
    setStatus("请输入搜索关键词");
    highlightId.value = "";
    renderMarkers();
    return;
  }

  const hitsWithSimilarity = markers.value.map((m) => {
    const text = `${m.title}${m.detail}`;
    const similarity = calculateSimilarity(text, key);
    return { ...m, similarity };
  }).filter((m) => m.similarity > 0);

  hitsWithSimilarity.sort((a, b) => b.similarity - a.similarity);

  searchResults.value = hitsWithSimilarity;
  showSearchModal.value = true;
}

function handleSearchResultSelect(item) {
  showSearchModal.value = false;
  highlightId.value = item.id;
  selectedMarker.value = item;
  showDetailModal.value = true;
  
  if (hasCoordinates(item)) {
    centerToPoint(item.lng, item.lat);
    renderMarkers();
  }
}

function closeSearchModal() {
  showSearchModal.value = false;
}

function toggle3DMode() {
  if (!mapRef.value) return;
  is3D.value = !is3D.value;
  mapRef.value.setPitch(is3D.value ? 45 : 0);
}

function enterFullMap() {
  mode.value = "fullmap";
}

function backToSplit() {
  mode.value = "normal";
}

function openDetail(item) {
  highlightId.value = item.id;
  selectedMarker.value = item;
  showDetailModal.value = true;
  renderMarkers();
}

function goProfile() {
  router.push("/profile");
}

function goToMessages() {
  router.push("/messages?from=home");
}

watch(
  () => mode.value,
  () => nextTick(() => mapRef.value && mapRef.value.resize()),
);

watch(filterStatus, () => {
  renderMarkers();
});

onMounted(async () => {
  await loadDefaultMap();
  await loadMarkers();
  await loadUserInfo();
  await loadCategories();
});
</script>

<template>
  <div class="app-home">
    <AppTopBar variant="home">
      <template #center>
        <div class="search-wrap">
          <input
            v-model="searchInput"
            type="text"
            placeholder="搜索标题/描述并定位"
            @keydown.enter="searchByKeyword"
          />
        </div>
      </template>
      <template #actions>
        <button class="notification-btn" type="button" title="通知消息" @click="goToMessages">
          🔔
        </button>
        <button class="avatar-btn" type="button" title="前往个人主页" @click="goProfile">
          <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" />
          <span v-else>{{ getInitial() }}</span>
        </button>
      </template>
    </AppTopBar>

    <main :class="appClass">
      <ListPanel
        :markers="markers"
        v-model:filterStatus="filterStatus"
        v-model:expanded="listExpanded"
        @itemClick="handleItemClick"
        @itemDoubleClick="openDetail"
        @add="openAddModal"
      />

      <button
        class="side-toggle"
        :style="leftArrowStyle"
        :class="{ hidden: mode === 'fullmap' }"
        title="切入全图模式"
        @click="enterFullMap"
      >
        ◀
      </button>
      <button
        class="side-toggle right-mode"
        :class="{ hidden: mode !== 'fullmap' }"
        title="返回分栏模式"
        @click="backToSplit"
      >
        ▶
      </button>

      <section class="map-panel">
        <div :id="mapContainerId"></div>
        <div class="status">{{ statusText }}</div>
        <button
          id="toggle3D"
          style="
            position: absolute;
            top: 12px;
            left: 12px;
            z-index: 10;
            padding: 6px 10px;
            border-radius: 6px;
            border: none;
            background: #111827;
            color: #fff;
            cursor: pointer;
          "
          @click="toggle3DMode"
        >
          切换3D
        </button>
      </section>
    </main>

    <PublishModal
      :show="showPublishModal"
      :pendingLocation="pendingWorldPoint"
      :categories="categories"
      @close="handlePublishClose"
      @submit="handlePublishSubmit"
      @clearLocation="handleClearLocation"
      @selectLocation="handleSelectLocation"
    />

    <SearchResultModal
      :show="showSearchModal"
      :results="searchResults"
      :keyword="searchInput"
      @close="closeSearchModal"
      @select="handleSearchResultSelect"
    />

    <MarkerDetailModal
      :show="showDetailModal"
      :marker="selectedMarker"
      :hidePublisher="true"
      @close="showDetailModal = false"
      @remove="handleRemoveMarker"
      @locate="(m) => { highlightId = m.id; centerToPoint(m.lng, m.lat); renderMarkers(); }"
    />
  </div>
</template>