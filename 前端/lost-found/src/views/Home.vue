<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";

const API_BASE = "http://127.0.0.1:5000/api";
const mapContainerId = "mapContainer";

const statusText = ref("点击地图任意位置可发布标记");
const searchInput = ref("");
const is3D = ref(true);
const mode = ref("normal");
const listExpanded = ref(false);

const markers = ref([]);
const markerObjs = ref([]);
const highlightId = ref("");
const selectedMarker = ref(null);
const pendingWorldPoint = ref(null);
const mapRef = ref(null);

const showPublishModal = ref(false);
const pubTitle = ref("");
const pubDetail = ref("");
const pubPhone = ref("");

const showDetailModal = ref(false);

const appClass = computed(() => {
  if (mode.value === "fullmap") return "app fullmap";
  if (mode.value === "split") return "app split";
  return "app";
});

const leftArrowStyle = computed(() => ({
  left: listExpanded.value ? "calc(50vw - 32px)" : "calc(var(--list-width) - 32px)",
}));

function setStatus(message) {
  statusText.value = message;
}

function centerToPoint(lng, lat) {
  if (!mapRef.value) return;
  mapRef.value.setCenter([lng, lat]);
}

function renderMarkers() {
  if (!mapRef.value || !window.AMap) return;

  markerObjs.value.forEach((m) => m.setMap(null));
  markerObjs.value = [];

  markers.value.forEach((m) => {
    if (!m.lng || !m.lat) return;

    const marker = new window.AMap.Marker({
      position: [m.lng, m.lat],
      map: mapRef.value,
      title: m.title,
      offset: new window.AMap.Pixel(-17, -48),
      content: `
        <div class="marker-wrap ${String(highlightId.value) === String(m.id) ? "highlight" : ""}">
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

    markers.value = (data.data || []).map((item, index) => ({
      id: item.item_id || item.location_id || index + 1,
      title: item.title || item.name || "未命名标记",
      detail: item.description || "",
      lng: Number(item.lng ?? item.longitude),
      lat: Number(item.lat ?? item.latitude),
      time: item.create_time || "",
      status: item.status ?? 0,
      phone: item.phone || "",
    }));

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
    pubTitle.value = "";
    pubDetail.value = "";
    pubPhone.value = "";
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

async function submitPublish() {
  const title = pubTitle.value.trim();
  const detail = pubDetail.value.trim();
  const phone = pubPhone.value.trim();

  if (!title || !detail || !pendingWorldPoint.value) {
    setStatus("标题和描述不能为空");
    return;
  }

  const userId = localStorage.getItem("user_id");

  try {
    const res = await fetch(`${API_BASE}/map/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        title,
        detail,
        phone,
        lng: pendingWorldPoint.value.lng,
        lat: pendingWorldPoint.value.lat,
      }),
    });
    const data = await res.json();
    if (data.success) {
      setStatus("发布成功");
      showPublishModal.value = false;
      await loadMarkers();
    } else {
      setStatus(data.message || "发布失败");
    }
  } catch (error) {
    console.error(error);
    setStatus("发布接口异常");
  }
}

function searchByKeyword() {
  const key = searchInput.value.trim().toLowerCase();
  const hit = markers.value.find((m) =>
    `${m.title}${m.detail}`.toLowerCase().includes(key),
  );
  if (!hit) {
    setStatus("未找到");
    return;
  }
  highlightId.value = hit.id;
  centerToPoint(hit.lng, hit.lat);
  renderMarkers();
}

function toggle3DMode() {
  if (!mapRef.value) return;
  is3D.value = !is3D.value;
  // 保持 3D 渲染模式，仅切换 pitch，避免 setViewMode 引发重绘卡顿
  mapRef.value.setPitch(is3D.value ? 45 : 0);
}

function enterFullMap() {
  mode.value = "fullmap";
}

function backToSplit() {
  mode.value = "normal";
}

function onListDoubleClick() {
  listExpanded.value = !listExpanded.value;
}

function openDetail(item) {
  highlightId.value = item.id;
  selectedMarker.value = item;
  showDetailModal.value = true;
  renderMarkers();
}

function goProfile() {
  window.location.href = "/profile";
}

watch(
  () => mode.value,
  () => nextTick(() => mapRef.value && mapRef.value.resize()),
);

onMounted(async () => {
  await loadDefaultMap();
  await loadMarkers();
});
</script>

<template>
  <div>
    <header class="topbar">
      <h1 class="topbar-title">校园失物招领与位置追踪系统</h1>
      <div class="topbar-actions">
        <div class="search-wrap">
          <input
            v-model="searchInput"
            type="text"
            placeholder="搜索标题/描述并定位"
            @keydown.enter="searchByKeyword"
          />
        </div>
        <button class="avatar-btn" title="前往个人主页" @click="goProfile">管</button>
      </div>
    </header>

    <main :class="appClass">
      <aside
        class="list-panel"
        :class="{ expanded: listExpanded }"
        title="双击展开/收起详情"
        @dblclick="onListDoubleClick"
      >
        <div class="list-header">
          标记列表
          <div class="list-tip">双击黄色区域展开详细列表（50/50）</div>
        </div>
        <ul class="item-list">
          <li
            v-for="item in markers"
            :key="item.id"
            class="item-card"
            :class="{ expanded: listExpanded }"
            @click="centerToPoint(item.lng, item.lat); highlightId = item.id; renderMarkers()"
            @dblclick.stop="openDetail(item)"
          >
            <div class="item-card-title">{{ item.title }}</div>
            <div>ID：{{ item.id }}</div>
            <div class="item-card-detail">
              <div>描述：{{ item.detail || "无" }}</div>
              <div>时间：{{ item.time || "未知" }}</div>
            </div>
          </li>
        </ul>
      </aside>

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

    <div class="modal-mask" :style="{ display: showPublishModal ? 'flex' : 'none' }">
      <div class="modal">
        <h3>发布信息</h3>
        <div class="form-row">
          <label for="pubTitle">标题</label>
          <input id="pubTitle" v-model="pubTitle" type="text" placeholder="请输入标题" />
        </div>
        <div class="form-row">
          <label for="pubDetail">描述</label>
          <textarea id="pubDetail" v-model="pubDetail" placeholder="请输入详细描述"></textarea>
        </div>
        <div class="form-row">
          <label for="pubPhone">联系方式</label>
          <input id="pubPhone" v-model="pubPhone" type="text" placeholder="请输入联系方式" />
        </div>
        <div class="modal-actions">
          <button class="btn" type="button" @click="showPublishModal = false">取消</button>
          <button class="btn primary" type="button" @click="submitPublish">发布</button>
        </div>
      </div>
    </div>

    <div class="modal-mask" :style="{ display: showDetailModal ? 'flex' : 'none' }">
      <div class="modal">
        <h3>{{ selectedMarker?.title || "详情" }}</h3>
        <div style="line-height: 1.7; font-size: 14px">
          <div>描述：{{ selectedMarker?.detail || "无" }}</div>
          <div>时间：{{ selectedMarker?.time || "未知" }}</div>
          <div v-if="selectedMarker?.phone">联系方式：{{ selectedMarker.phone }}</div>
        </div>
        <div class="modal-actions">
          <button class="btn primary" type="button" @click="showDetailModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>