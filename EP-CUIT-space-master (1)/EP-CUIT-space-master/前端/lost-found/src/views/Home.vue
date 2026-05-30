<!-- 主页 -->
<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import AppTopBar from "../components/AppTopBar.vue";
import SearchResultModal from "../components/SearchResultModal.vue";
import MarkerDetailModal from "../components/MarkerDetailModal.vue";
import PublishModal from "../components/PublishModal.vue";
import ListPanel from "../components/ListPanel.vue";
import RepairModal from "../components/RepairModal.vue";
import RepairList from "../components/RepairList.vue";
import RepairDetailModal from "../components/RepairDetailModal.vue";

const router = useRouter();

const API_BASE = "http://127.0.0.1:5000/api";
const mapContainerId = "mapContainer";

const statusText = ref("查看模式 - 点击标记查看详情");
const searchInput = ref("");
const is3D = ref(true);
const isSatellite = ref(false);
const mode = ref("normal");
const rotation = ref(0);
const showMenu = ref(false);
const showBuildings = ref(true);
const listExpanded = ref(false);
const filterStatus = ref("all");
let clickTimer = null;

const markers = ref([]);
const markerObjs = ref([]);
const highlightId = ref("");
const selectedMarker = ref(null);
const pendingWorldPoint = ref(null);
const mapRef = ref(null);

const showPublishModal = ref(false);
const categories = ref([]);

console.log('[Home.vue] categories initialized:', categories.value);

const showDetailModal = ref(false);
const showSearchModal = ref(false);
const searchResults = ref([]);
const avatarUrl = ref("");
const username = ref("");
const currentUserId = ref(localStorage.getItem("user_id"));

const showRepairModal = ref(false);
const repairLng = ref(0);
const repairLat = ref(0);
const repairMarkers = ref([]);
const showRepairDetailModal = ref(false);
const currentDetailRepair = ref(null);
const repairMarkerObjs = ref([]);
const currentMode = ref('lost'); // 'lost' | 'repair'
const mapMode = ref('view'); // 'view' | 'publish'

const showMarkerSelector = ref(false);
const nearbyMarkersList = ref([]);

const campuses = ref([]);

const currentCampus = ref(null);
const currentCampusId = ref('');

async function loadCampuses() {
  try {
    const res = await fetch(`${API_BASE}/map/campuses`);
    const data = await res.json();
    if (data.success && data.data) {
      campuses.value = data.data;
      if (campuses.value.length > 0) {
        if (!currentCampus.value) {
          currentCampus.value = campuses.value[0];
        }
        currentCampusId.value = currentCampus.value.id;
      }
    }
  } catch (e) {
    console.error("加载校区列表失败:", e);
    campuses.value = [
      { id: 'campus_1', name: '成都信息工程大学（航空港校区）', center: [103.9885, 30.5815], zoom: 19 }
    ];
    if (!currentCampus.value) {
      currentCampus.value = campuses.value[0];
    }
    currentCampusId.value = currentCampus.value.id;
  }
}

function handleCampusChange() {
  console.log('[handleCampusChange] 校区ID:', currentCampusId.value);
  const campus = campuses.value.find(c => c.id === currentCampusId.value);
  if (campus) {
    switchCampus(campus);
  } else {
    console.error('[handleCampusChange] 未找到校区:', currentCampusId.value);
  }
}

function switchCampus(campus) {
  console.log('[switchCampus] 切换校区:', campus);
  currentCampus.value = campus;
  if (mapRef.value && window.AMap) {
    console.log('[switchCampus] 设置地图中心:', campus.center, '缩放级别:', campus.zoom);
    mapRef.value.setZoomAndCenter(campus.zoom, campus.center);
  } else {
    console.error('[switchCampus] 地图对象未初始化');
  }
  renderMarkers();
  renderRepairMarkers();
}

function isMarkerInCampusBounds(lng, lat, campus) {
  // 暂时禁用边界过滤，确保所有标记都能显示
  return true;
}

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
    console.log("[DEBUG] 开始加载分类...");
    const res = await fetch(`${API_BASE}/map/categories`);
    console.log("[DEBUG] 分类API响应状态:", res.status);
    const data = await res.json();
    console.log("[DEBUG] 分类API响应数据:", data);
    if (data.success && data.data && Array.isArray(data.data)) {
      categories.value = data.data;
      console.log("[DEBUG] 加载到的分类:", categories.value);
      console.log("[DEBUG] 分类数量:", categories.value.length);
    } else {
      categories.value = [];
      console.log("[DEBUG] 未获取到分类数据");
    }
  } catch (e) {
    console.error("加载分类失败:", e);
    categories.value = [];
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

  if (currentMode.value === 'repair') return;

  let markersToRender = filteredMarkers.value;
  
  if (mapMode.value === 'publish') {
    const currentUserId = localStorage.getItem("user_id");
    markersToRender = markersToRender.filter(m => 
      String(m.publisher_id) === String(currentUserId)
    );
  }

  markersToRender.forEach((m) => {
    console.log(`[DEBUG] Processing lost item marker: id=${m.id}, title=${m.title}, lng=${m.lng}, lat=${m.lat}`);
    console.log(`[DEBUG] lng type: ${typeof m.lng}, lat type: ${typeof m.lat}`);
    console.log(`[DEBUG] lng isFinite: ${Number.isFinite(m.lng)}, lat isFinite: ${Number.isFinite(m.lat)}`);
    
    if (!m.lng || !m.lat || isNaN(m.lng) || isNaN(m.lat) || !Number.isFinite(m.lng) || !Number.isFinite(m.lat)) {
      console.log(`[DEBUG] 跳过无效坐标的标记: ${m.title}, lng=${m.lng}, lat=${m.lat}`);
      return;
    }
    
    if (!isMarkerInCampusBounds(m.lng, m.lat, currentCampus.value)) {
      console.log(`[DEBUG] 标记 ${m.title} 不在当前校区范围内，跳过渲染`);
      return;
    }

    const isLost = m.type === 0;
    const markerColor = isLost ? "marker-lost" : "marker-found";
    
    const position = [Number(m.lng), Number(m.lat)];
    console.log(`[DEBUG] Creating marker with position:`, position);

    const marker = new window.AMap.Marker({
      position: position,
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
      if (mapMode.value === 'view') {
        highlightId.value = m.id;
        selectedMarker.value = m;
        showDetailModal.value = true;
        renderMarkers();
      } else {
        // 发布模式下，点击标记也打开该位置的发布弹窗
        pendingWorldPoint.value = { lng: m.lng, lat: m.lat };
        showPublishModal.value = true;
      }
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
      const lngValue = item.lng !== undefined ? item.lng : item.longitude;
      const latValue = item.lat !== undefined ? item.lat : item.latitude;
      const lngNum = lngValue !== undefined ? Number(lngValue) : null;
      const latNum = latValue !== undefined ? Number(latValue) : null;
      
      return {
        id: item.item_id || item.location_id || index + 1,
        title: item.title || item.name || "未命名标记",
        detail: item.description || "",
        lng: Number.isFinite(lngNum) ? lngNum : null,
        lat: Number.isFinite(latNum) ? latNum : null,
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

async function loadRepairMarkers() {
  try {
    console.log(`[DEBUG] Loading repair markers from: ${API_BASE}/repair`);
    const res = await fetch(`${API_BASE}/repair`);
    console.log(`[DEBUG] Response status: ${res.status}`);
    const data = await res.json();
    console.log(`[DEBUG] Repair data received:`, data);
    
    if (!data.success) {
      console.log(`[DEBUG] API returned success=false, message: ${data.message}`);
      return;
    }

    repairMarkers.value = (data.data || []).map((item) => {
      const lngValue = item.lng !== undefined ? item.lng : item.longitude;
      const latValue = item.lat !== undefined ? item.lat : item.latitude;
      const lngNum = lngValue !== undefined ? Number(lngValue) : null;
      const latNum = latValue !== undefined ? Number(latValue) : null;
      const lng = Number.isFinite(lngNum) ? lngNum : null;
      const lat = Number.isFinite(latNum) ? latNum : null;
      console.log(`[DEBUG] Repair item: ${item.title}, lng=${lng}, lat=${lat}`);
      return ({
        id: item.repair_id,
        repair_id: item.repair_id,
        title: item.title,
        description: item.description,
        lng: lng,
        lat: lat,
        status: item.status,
        priority: item.priority,
        create_time: item.create_time,
        category_name: item.category_name,
        location_name: item.location_name,
        location_detail: item.location_detail,
        reporter_id: item.reporter_id,
        images: item.images || [],
        repair_category_id: item.repair_category_id,
        location_id: item.location_id,
      });
    });

    console.log(`[DEBUG] Total repair markers loaded: ${repairMarkers.value.length}`);
    renderRepairMarkers();
  } catch (error) {
    console.error("加载报修标记失败:", error);
  }
}

function renderRepairMarkers() {
  console.log(`[DEBUG] renderRepairMarkers called`);
  console.log(`[DEBUG] mapRef exists: ${!!mapRef.value}`);
  console.log(`[DEBUG] AMap exists: ${!!window.AMap}`);
  console.log(`[DEBUG] Current mode: ${currentMode.value}`);
  console.log(`[DEBUG] Repair markers count: ${repairMarkers.value.length}`);
  
  if (!mapRef.value || !window.AMap) {
    console.log(`[DEBUG] Early return: mapRef or AMap not ready`);
    return;
  }

  repairMarkerObjs.value.forEach((m) => m.setMap(null));
  repairMarkerObjs.value = [];

  if (currentMode.value !== 'repair') {
    console.log(`[DEBUG] Early return: not in repair mode`);
    return;
  }

  let markersToRender = repairMarkers.value;
  
  if (mapMode.value === 'publish') {
    const currentUserId = localStorage.getItem("user_id");
    markersToRender = markersToRender.filter(m => 
      String(m.reporter_id) === String(currentUserId)
    );
  }

  let renderedCount = 0;
  markersToRender.forEach((m) => {
    console.log(`[DEBUG] Processing marker: ${m.title}, lng=${m.lng}, lat=${m.lat}, priority=${m.priority}`);
    if (!m.lng || !m.lat || isNaN(m.lng) || isNaN(m.lat) || !Number.isFinite(m.lng) || !Number.isFinite(m.lat)) {
      console.log(`[DEBUG] Skipping marker: invalid coordinates`);
      return;
    }
    
    if (!isMarkerInCampusBounds(m.lng, m.lat, currentCampus.value)) {
      console.log(`[DEBUG] 报修标记 ${m.title} 不在当前校区范围内，跳过渲染`);
      return;
    }

    // 根据优先级确定颜色
    const priority = parseInt(m.priority);
    let color = '#28a745'; // 默认绿色
    
    if (priority === 3) {
      color = '#dc3545'; // 红色
    } else if (priority === 2) {
      color = '#ffc107'; // 黄色
    }

    const svgContent = `
      <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 60 60">
        <defs>
          <radialGradient id="coreGrad${m.repair_id}" cx="30%" cy="30%">
            <stop offset="0%" style="stop-color:${color};stop-opacity:1" />
            <stop offset="100%" style="stop-color:${color};stop-opacity:0.8" />
          </radialGradient>
        </defs>
        <circle cx="30" cy="30" r="22" fill="none" stroke="${color}" stroke-width="3" opacity="0.4">
          <animate attributeName="r" from="15" to="25" dur="2s" repeatCount="indefinite"/>
          <animate attributeName="opacity" from="1" to="0" dur="2s" repeatCount="indefinite"/>
        </circle>
        <circle cx="30" cy="30" r="15" fill="url(#coreGrad${m.repair_id})" stroke="#fff" stroke-width="3"/>
        <text x="30" y="35" text-anchor="middle" font-size="16" fill="#fff">🔧</text>
      </svg>
    `;

    const iconBase64 = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgContent)));
    
    const icon = new window.AMap.Icon({
      size: new window.AMap.Size(60, 60),
      image: iconBase64,
      imageSize: new window.AMap.Size(60, 60),
      imageOffset: new window.AMap.Pixel(0, 0)
    });

    const marker = new window.AMap.Marker({
      position: [m.lng, m.lat],
      map: mapRef.value,
      title: m.title,
      icon: icon,
      offset: new window.AMap.Pixel(-30, -50),
      label: {
        content: `<span style="font-size:12px;color:#333;text-align:center;display:block;max-width:60px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${m.title || "报修"}</span>`,
        offset: new window.AMap.Pixel(-30, -45),
        direction: 'top'
      }
    });

    marker.on('click', function() {
      if (mapMode.value === 'view') {
        centerToPoint(m.lng, m.lat);
        showRepairDetail(m);
      } else {
        // 发布模式下，点击标记也打开该位置的报修弹窗
        repairLng.value = m.lng;
        repairLat.value = m.lat;
        showRepairModal.value = true;
      }
    });

    repairMarkerObjs.value.push(marker);
    renderedCount++;
  });
  
  console.log(`[DEBUG] Rendered ${renderedCount} repair markers`);
}

function handleSubmitRepair() {
  showRepairModal.value = false;
  loadRepairMarkers();
}

function showRepairDetail(repair) {
  currentDetailRepair.value = repair;
  showRepairDetailModal.value = true;
}

function openRepairModal(e) {
  const lng = e.lnglat.lng;
  const lat = e.lnglat.lat;
  repairLng.value = lng;
  repairLat.value = lat;
  showRepairModal.value = true;
}

function initMap(config) {
  console.log('[initMap] 开始初始化地图');
  console.log('[initMap] 配置:', config);
  
  const AMap = window.AMap;
  console.log('[initMap] AMap SDK 是否加载:', !!AMap);
  
  const mapContainer = document.getElementById(mapContainerId);
  console.log('[initMap] 地图容器:', mapContainer);
  console.log('[initMap] 容器尺寸:', mapContainer ? { width: mapContainer.offsetWidth, height: mapContainer.offsetHeight } : '不存在');
  
  if (!mapContainer) {
    console.error('[initMap] 错误：地图容器不存在');
    setStatus("地图容器初始化失败");
    return;
  }
  
  if (!AMap) {
    console.error('[initMap] 错误：AMap SDK 未加载');
    setStatus("地图SDK加载失败");
    return;
  }
  
  if (!config || !config.center_lng || !config.center_lat) {
    console.error('[initMap] 错误：地图配置不完整');
    setStatus("地图配置加载失败");
    return;
  }

  try {
    const initialViewMode = is3D.value ? "3D" : "2D";
    const initialPitch = is3D.value ? 45 : 0;
    
    mapRef.value = new AMap.Map(mapContainerId, {
      zoom: config.zoom || 18,
      center: [parseFloat(config.center_lng), parseFloat(config.center_lat)],
      viewMode: initialViewMode,
      pitch: initialPitch,
      showIndoorMap: false,
      highAccuracy: true,
      animateEnable: true,
      resizeEnable: true,
    });
    console.log('[initMap] 地图创建成功:', mapRef.value);
    
    // 如果3D模式开启，添加建筑层
    if (is3D.value && showBuildings.value) {
      mapRef.value.addLayer(new AMap.Buildings({
        heightFactor: 1.5,
        shadow: true
      }));
    }
  } catch (e) {
    console.error('[initMap] 地图创建失败:', e);
    setStatus("地图创建失败: " + e.message);
    return;
  }

  mapRef.value.setBounds(new AMap.Bounds(
    [config.sw_lng, config.sw_lat],
    [config.ne_lng, config.ne_lat],
  ));
  mapRef.value.setZooms([16, 20]);

  mapRef.value.on("click", function(e) {
    if (e && e.lnglat) {
      const lng = parseFloat(e.lnglat.lng.toFixed(8));
      const lat = parseFloat(e.lnglat.lat.toFixed(8));
      
      if (mapMode.value === 'view') {
        const nearbyMarkers = findNearbyMarkers(lng, lat);
        if (nearbyMarkers.length > 0) {
          if (nearbyMarkers.length === 1) {
            openMarkerDetail(nearbyMarkers[0]);
          } else {
            openMarkerSelector(nearbyMarkers);
          }
        }
      } else {
        if (currentMode.value === 'repair') {
          repairLng.value = lng;
          repairLat.value = lat;
          showRepairModal.value = true;
        } else {
          pendingWorldPoint.value = { lng, lat };
          showPublishModal.value = true;
        }
      }
    }
  });
}

function toggleMapMode() {
  mapMode.value = mapMode.value === 'view' ? 'publish' : 'view';
  updateStatusText();
  renderMarkers();
  renderRepairMarkers();
}

function updateStatusText() {
  const modeText = currentMode.value === 'lost' ? '失物招领' : '报修';
  if (mapMode.value === 'view') {
    statusText.value = `查看模式 - 点击标记查看${modeText}详情`;
  } else {
    statusText.value = `发布模式 - 点击地图发布${modeText}`;
  }
}

function findNearbyMarkers(lng, lat, threshold = 0.0001) {
  const targetMarkers = currentMode.value === 'lost' ? filteredMarkers.value : repairMarkers.value;
  
  return targetMarkers.filter(m => {
    if (!m.lng || !m.lat) return false;
    const distance = Math.sqrt(
      Math.pow(m.lng - lng, 2) + Math.pow(m.lat - lat, 2)
    );
    return distance <= threshold;
  });
}

function openMarkerDetail(marker) {
  highlightId.value = marker.id;
  
  if (currentMode.value === 'lost') {
    selectedMarker.value = marker;
    showDetailModal.value = true;
  } else {
    currentDetailRepair.value = marker;
    showRepairDetailModal.value = true;
  }
  
  renderMarkers();
  renderRepairMarkers();
}

function openMarkerSelector(markers) {
  nearbyMarkersList.value = markers;
  showMarkerSelector.value = true;
}

function selectMarkerFromList(marker) {
  showMarkerSelector.value = false;
  openMarkerDetail(marker);
}

function closeMarkerSelector() {
  showMarkerSelector.value = false;
}

async function loadDefaultMap() {
  console.log('[loadDefaultMap] 开始加载地图配置');
  try {
    console.log('[loadDefaultMap] 请求地址:', `${API_BASE}/map/default`);
    const res = await fetch(`${API_BASE}/map/default`);
    console.log('[loadDefaultMap] 响应状态:', res.status);
    const config = await res.json();
    console.log('[loadDefaultMap] 配置数据:', config);
    
    if (!config || config.error) {
      console.error('[loadDefaultMap] 配置错误:', config);
      setStatus("地图加载失败");
      return;
    }
    initMap(config);
  } catch (error) {
    console.error('[loadDefaultMap] 请求失败:', error);
    setStatus("地图接口异常: " + error.message);
  }
}

function handleModeSwitch(mode) {
  if (currentMode.value === mode) return;
  
  if (mapRef.value && window.AMap) {
    const AMap = window.AMap;
    const allOverlays = mapRef.value.getAllOverlays();
    allOverlays.forEach(overlay => {
      if (overlay instanceof AMap.Marker) {
        mapRef.value.remove(overlay);
      }
    });
  }
  
  currentMode.value = mode;
  listExpanded.value = false;
  highlightId.value = null;
  
  if (mode === 'lostFound') {
    loadMarkers();
  } else if (mode === 'repair') {
    loadRepairMarkers();
  }
}

async function openAddModal() {
  pendingWorldPoint.value = null;
  showPublishModal.value = true;
}

function handlePublishSubmit() {
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
  
  const AMap = window.AMap;
  if (is3D.value) {
    mapRef.value.setPitch(45);
    mapRef.value.setViewMode('3D');
    if (showBuildings.value) {
      mapRef.value.addLayer(new AMap.Buildings({
        heightFactor: 1.5,
        shadow: true
      }));
    }
  } else {
    mapRef.value.setPitch(0);
    mapRef.value.setViewMode('2D');
    const buildingsLayer = mapRef.value.getLayers().find(layer => layer instanceof AMap.Buildings);
    if (buildingsLayer) {
      mapRef.value.removeLayer(buildingsLayer);
    }
  }
}

function toggleBuildings() {
  if (!mapRef.value) return;
  const AMap = window.AMap;
  showBuildings.value = !showBuildings.value;
  
  const buildingsLayer = mapRef.value.getLayers().find(layer => layer instanceof AMap.Buildings);
  
  if (showBuildings.value && is3D.value && !buildingsLayer) {
    mapRef.value.addLayer(new AMap.Buildings({
      heightFactor: 1.5,
      shadow: true
    }));
  } else if (!showBuildings.value && buildingsLayer) {
    mapRef.value.removeLayer(buildingsLayer);
  }
}

function toggleSatelliteMode() {
  if (!mapRef.value) return;
  const AMap = window.AMap;
  
  if (isSatellite.value) {
    const layers = [new AMap.TileLayer()];
    if (is3D.value && showBuildings.value) {
      layers.push(new AMap.Buildings({ heightFactor: 1.5, shadow: true }));
    }
    mapRef.value.setLayers(layers);
    isSatellite.value = false;
  } else {
    const layers = [new AMap.TileLayer.Satellite()];
    if (is3D.value && showBuildings.value) {
      layers.push(new AMap.Buildings({ heightFactor: 1.5, shadow: true }));
    }
    mapRef.value.setLayers(layers);
    isSatellite.value = true;
  }
}

function rotateMap(angle) {
  if (!mapRef.value) return;
  rotation.value = (rotation.value + angle) % 360;
  mapRef.value.setRotation(rotation.value);
}

function resetRotation() {
  if (!mapRef.value) return;
  rotation.value = 0;
  mapRef.value.setRotation(0);
}

function toggleMenu() {
  showMenu.value = !showMenu.value;
}

function closeMenu() {
  showMenu.value = false;
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
  await loadCampuses();
  await loadDefaultMap();
  await loadMarkers();
  await loadRepairMarkers();
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
        v-if="currentMode !== 'repair'"
        :markers="markers"
        v-model:filterStatus="filterStatus"
        v-model:expanded="listExpanded"
        @itemClick="handleItemClick"
        @itemDoubleClick="openDetail"
        @add="openAddModal"
        @modeSwitch="handleModeSwitch"
      />
      
      <RepairList
        v-if="currentMode === 'repair'"
        :repairs="repairMarkers"
        :expanded="listExpanded"
        @update:expanded="(val) => listExpanded = val"
        @itemDoubleClick="(r) => { highlightId = r.repair_id; centerToPoint(r.lng, r.lat); showRepairDetail(r); }"
        @refresh="loadRepairMarkers"
        @modeSwitch="handleModeSwitch"
        @add="openRepairModal"
      />



      <section class="map-panel">
        <div :id="mapContainerId"></div>
        <div
          :style="{
            position: 'absolute',
            top: '0',
            left: '0',
            width: showMenu ? '200px' : '320px',
            height: showMenu ? '350px' : '44px',
            zIndex: '99',
            background: 'transparent',
          }"
          @click.stop
        ></div>
        
        <div
          :style="{
            position: 'absolute',
            top: '12px',
            left: '12px',
            zIndex: '100',
          }"
        >
          <select
            v-model="currentCampusId"
            @change="handleCampusChange"
            :style="{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #374151',
              background: '#111827',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '14px',
              outline: 'none',
              marginRight: '8px'
            }"
          >
            <option v-for="campus in campuses" :key="campus.id" :value="campus.id">
              {{ campus.name }}
            </option>
          </select>
          
          <button
            id="mapMenuBtn"
            :style="{
              padding: '6px 14px',
              borderRadius: '6px',
              border: 'none',
              background: '#111827',
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }"
            @click="toggleMenu"
          >
            ⚙ 地图操作
            <span>{{ showMenu ? '▲' : '▼' }}</span>
          </button>
          
          <div
            v-if="showMenu"
            :style="{
              position: 'absolute',
              top: '100%',
              left: '0',
              marginTop: '4px',
              background: '#111827',
              borderRadius: '6px',
              padding: '4px',
              minWidth: '140px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
            }"
          >
            <button
              :style="{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '4px',
                border: 'none',
                background: 'transparent',
                color: '#fff',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }"
              @click="toggle3DMode(); closeMenu()"
            >
              🔹 {{ is3D ? '2D视角' : '3D视角' }}
            </button>
            <button
              :style="{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '4px',
                border: 'none',
                background: 'transparent',
                color: '#fff',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }"
              @click="toggleSatelliteMode(); closeMenu()"
            >
              {{ isSatellite ? '🗺 普通地图' : '🛰 卫星视图' }}
            </button>
            <button
              :style="{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '4px',
                border: 'none',
                background: 'transparent',
                color: '#fff',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }"
              @click="rotateMap(45)"
            >
              ↻ 向右旋转45°
            </button>
            <button
              :style="{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '4px',
                border: 'none',
                background: 'transparent',
                color: '#fff',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }"
              @click="resetRotation()"
            >
              📍 重置方向 ({{ rotation }}°)
            </button>
            <hr :style="{ borderColor: '#374151', margin: '4px 0' }" />
            <button
              :style="{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '4px',
                border: 'none',
                background: 'transparent',
                color: '#fff',
                cursor: 'pointer',
                textAlign: 'left',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }"
              @click="mode === 'fullmap' ? backToSplit() : enterFullMap(); closeMenu()"
            >
              {{ mode === 'fullmap' ? '📊 分栏模式' : '🗺️ 全图模式' }}
            </button>
            <hr :style="{ borderColor: '#374151', margin: '4px 0' }" />
            <button
            :style="{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '4px',
              border: 'none',
              background: showBuildings ? '#10B981' : 'transparent',
              color: '#fff',
              cursor: 'pointer',
              textAlign: 'left',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }"
            @click="toggleBuildings()"
            :disabled="!is3D"
          >
            🏢 3D建筑 {{ showBuildings ? '开' : '关' }}
          </button>
        </div>
      </div>
      
      <div
        :style="{
          position: 'absolute',
          top: '-10px',
          right: '-10px',
          zIndex: '100',
          display: 'flex',
          gap: '8px',
          padding: '30px',
          pointerEvents: 'auto'
        }"
      >
        <div
          :style="{
            display: 'flex',
            alignItems: 'center',
            background: '#374151',
            borderRadius: '8px',
            padding: '2px',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)'
          }"
        >
          <button
            :style="{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              background: mapMode === 'view' ? '#3B82F6' : 'transparent',
              color: mapMode === 'view' ? '#fff' : '#9CA3AF',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: mapMode === 'view' ? '700' : '500',
              transition: 'all 0.3s ease',
              transform: mapMode === 'view' ? 'scale(1.05)' : 'scale(1)'
            }"
            @click="toggleMapMode"
          >
            查看
          </button>
          <span :style="{ color: '#6B7280', margin: '0 4px', fontSize: '16px' }">|</span>
          <button
            :style="{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              background: mapMode === 'publish' ? '#10B981' : 'transparent',
              color: mapMode === 'publish' ? '#fff' : '#9CA3AF',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: mapMode === 'publish' ? '700' : '500',
              transition: 'all 0.3s ease',
              transform: mapMode === 'publish' ? 'scale(1.05)' : 'scale(1)'
            }"
            @click="toggleMapMode"
          >
            发布
          </button>
        </div>
      </div>
    </section>
  </main>

    <PublishModal
      :show="showPublishModal"
      :pendingLocation="pendingWorldPoint"
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
      :show-publisher-info="true"
      @close="showDetailModal = false"
      @remove="handleRemoveMarker"
      @locate="(m) => { highlightId = m.id; centerToPoint(m.lng, m.lat); renderMarkers(); }"
    />

    <RepairModal
      :visible="showRepairModal"
      :initialLng="repairLng"
      :initialLat="repairLat"
      @close="showRepairModal = false"
      @submit="handleSubmitRepair"
    />
    
    <RepairDetailModal
      :visible="showRepairDetailModal"
      :repair="currentDetailRepair"
      @close="showRepairDetailModal = false"
    />
    
    <div 
      v-if="showMarkerSelector" 
      class="modal-overlay" 
      @click.self="closeMarkerSelector"
    >
      <div class="marker-selector-modal">
        <div class="modal-header">
          <h3>选择标记</h3>
          <button class="close-btn" @click="closeMarkerSelector">×</button>
        </div>
        <div class="modal-body">
          <p>该位置附近有多个标记，请选择要查看的标记：</p>
          <div class="marker-list">
            <div 
              v-for="marker in nearbyMarkersList" 
              :key="marker.id"
              class="marker-item"
              @click="selectMarkerFromList(marker)"
            >
              <div class="marker-icon">
                {{ currentMode === 'lost' ? (marker.type === 0 ? '🔴' : '🟢') : '🔧' }}
              </div>
              <div class="marker-info">
                <div class="marker-title">{{ marker.title }}</div>
                <div class="marker-time">{{ marker.time || marker.create_time }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notification-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.25);
  color: #1f2937;
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  backdrop-filter: blur(4px);
}

.notification-btn:hover {
  background: rgba(255, 255, 255, 0.4);
  transform: scale(1.08);
}

.notification-btn:active {
  transform: scale(0.95);
}

.avatar-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  background: #111827;
  color: #fff;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: all 0.2s;
}

.avatar-btn:hover {
  transform: scale(1.08);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.marker-wrap.marker-repair {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.marker-repair .repair-core {
  width: 34px;
  height: 34px;
  border-radius: 50% !important;
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
  border: 3px solid #fff !important;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.5) !important;
  position: relative !important;
  top: auto !important;
  left: auto !important;
  transform: none !important;
  z-index: 1;
}

.marker-repair .repair-core::before {
  content: '🔧';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 14px;
}

.marker-repair .repair-wave {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(220, 53, 69, 0.4);
  animation: repairPulse 2s ease-out infinite;
  z-index: 0;
}

@keyframes repairPulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(2);
    opacity: 0;
  }
}

/* 报修标记 - 高优先级 (红色) */
.marker-repair .repair-core.priority-high {
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.5) !important;
}
.marker-repair .repair-wave.priority-high {
  background: rgba(220, 53, 69, 0.4);
}

/* 报修标记 - 中优先级 (黄色) */
.marker-repair .repair-core.priority-medium {
  background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%) !important;
  box-shadow: 0 4px 12px rgba(255, 193, 7, 0.5) !important;
}
.marker-repair .repair-wave.priority-medium {
  background: rgba(255, 193, 7, 0.4);
}

/* 报修标记 - 低优先级 (绿色) */
.marker-repair .repair-core.priority-low {
  background: linear-gradient(135deg, #28a745 0%, #218838 100%) !important;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.5) !important;
}
.marker-repair .repair-wave.priority-low {
  background: rgba(40, 167, 69, 0.4);
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
  z-index: 2000;
}

.marker-selector-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  overflow: hidden;
}

.marker-selector-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e5e5;
  background: #f8fafc;
}

.marker-selector-modal .modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
}

.marker-selector-modal .close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #64748b;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.marker-selector-modal .close-btn:hover {
  background: rgba(0, 0, 0, 0.1);
}

.marker-selector-modal .modal-body {
  padding: 20px;
}

.marker-selector-modal .modal-body p {
  margin: 0 0 16px 0;
  color: #64748b;
  font-size: 14px;
}

.marker-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.marker-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.marker-item:hover {
  background: #f1f5f9;
  border-color: #3b82f6;
}

.marker-icon {
  font-size: 24px;
}

.marker-info {
  flex: 1;
}

.marker-title {
  font-weight: 500;
  color: #1e293b;
  font-size: 14px;
}

.marker-time {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}
</style>