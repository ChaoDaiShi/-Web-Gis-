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
import NavPanel from "../components/NavPanel.vue";
import AppointmentModal from "../components/AppointmentModal.vue";
import { loadAMap, resetAMapLoader } from "../utils/amapLoader.js";

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
const isDoubleClick = ref(false);
let clickTimer = null;

const markers = ref([]);
const markerObjs = ref([]);
const highlightId = ref("");
const selectedMarker = ref(null);
const pendingWorldPoint = ref(null);
const mapRef = ref(null);
const mapLoadError = ref(false);
const mapLoadErrorMsg = ref("");

const showPublishModal = ref(false);
const categories = ref([]);

const showDetailModal = ref(false);
const showSearchModal = ref(false);
const showAppointmentModal = ref(false);
const searchResults = ref([]);
const avatarUrl = ref("");
const username = ref("");
const currentUserRole = ref("");
const currentUserId = ref("");

const showRepairModal = ref(false);
const repairLng = ref(0);
const repairLat = ref(0);
const repairMarkers = ref([]);

const overlappingMarkers = ref([]);
const showClusterModal = ref(false);
const showRepairDetailModal = ref(false);
const currentDetailRepair = ref(null);
const repairMarkerObjs = ref([]);
const currentMode = ref('lost'); // 'lost' | 'repair'
const mapMode = ref('view'); // 'view' | 'publish'

const showMarkerSelector = ref(false);
const nearbyMarkersList = ref([]);
const selectorPosition = ref({ lng: 0, lat: 0 });
const showNavPanel = ref(false);
const leftPanelMode = ref('list'); // 'list' | 'nav'

// 集中点（失物招领处）信息
const centralLocation = ref(null);
const centralMarkerObj = ref(null);

// 校区相关 - 从API获取
const campuses = ref([])
const currentCampus = ref({ id: '', name: '加载中...', center: [0, 0], zoom: 19, bounds: null })
const campusesLoaded = ref(false)

async function loadCampuses() {
  if (campusesLoaded.value) return;
  try {
    const res = await fetch(`${API_BASE}/map/campuses`)
    const data = await res.json()
    if (data.success && data.data) {
      // 转换校区ID为数字格式并去重
      const seen = new Set();
      campuses.value = data.data
        .map(c => ({
          ...c,
          id: parseInt(c.id) // 转换为数字ID
        }))
        .filter(c => {
          if (seen.has(c.id)) return false;
          seen.add(c.id);
          return true;
        });
      // 如果当前校区未设置或仍在加载中，则设置为第一个校区
      if (campuses.value.length > 0 && (!currentCampus.value || currentCampus.value.id === '')) {
        currentCampus.value = campuses.value[0]
      }
      campusesLoaded.value = true
      console.log('[校区加载] 成功加载校区:', campuses.value)
    }
  } catch (e) {
    console.error('[校区加载] 失败:', e)
  }
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
      currentUserRole.value = data.data.role || data.data.identity || "";
      currentUserId.value = userId;
      const roleStr = (data.data.role || '').toString();
      if (!currentUserRole.value && roleStr) {
        currentUserRole.value = roleStr;
      }
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

async function loadCentralLocation() {
  try {
    const res = await fetch(`${API_BASE}/appointments/central-location`);
    const data = await res.json();
    console.log('[集中点加载] 接口返回:', data);
    if (data.success && data.data) {
      const lng = Number(data.data.longitude);
      const lat = Number(data.data.latitude);
      console.log('[集中点加载] 坐标:', lng, lat);
      centralLocation.value = {
        id: data.data.location_id,
        name: data.data.name,
        lng: lng,
        lat: lat
      };
      renderCentralMarker();
    }
  } catch (e) {
    console.error("加载集中点信息失败:", e);
  }
}

function renderCentralMarker() {
  console.log('[集中点渲染] 开始渲染集中点');
  console.log('[集中点渲染] mapRef:', !!mapRef.value);
  console.log('[集中点渲染] AMap:', !!window.AMap);
  console.log('[集中点渲染] centralLocation:', centralLocation.value);
  
  if (!mapRef.value || !window.AMap || !centralLocation.value) {
    console.log('[集中点渲染] 条件不满足，跳过');
    return;
  }
  
  if (centralMarkerObj.value) {
    centralMarkerObj.value.setMap(null);
    centralMarkerObj.value = null;
  }

  const { lng, lat, name } = centralLocation.value;
  
  console.log('[集中点渲染] 创建标记:', name, lng, lat);
  
  const marker = new window.AMap.Marker({
    position: [lng, lat],
    map: mapRef.value,
    title: name,
    offset: new window.AMap.Pixel(-20, -52),
    content: `
      <div class="marker-wrap marker-central" style="position: relative; display: flex; flex-direction: column; align-items: center;">
        <div class="marker-wave-central" style="position: absolute; width: 40px; height: 40px; border-radius: 50%; background: rgba(251, 191, 36, 0.3); animation: centralPulse 2s ease-out infinite; top: 50%; left: 50%; transform: translate(-50%, -50%);"></div>
        <div class="marker-core-central" style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); display: flex; align-items: center; justify-content: center; font-size: 20px; box-shadow: 0 4px 12px rgba(251, 191, 36, 0.5); position: relative; z-index: 1; border: 3px solid #fff;">🏠</div>
        <div class="marker-label" style="margin-top: 4px; font-size: 12px; white-space: nowrap;">${name}</div>
      </div>
    `,
    zIndex: 1000
  });

  marker.on("click", () => {
    if (mapMode.value === 'view') {
      highlightId.value = 'central';
      selectedMarker.value = {
        id: 'central',
        title: name,
        detail: '失物招领集中点，可在此发布拾物信息或预约领取',
        lng,
        lat,
        isCentral: true
      };
      showDetailModal.value = true;
    }
  });

  centralMarkerObj.value = marker;
  console.log('[集中点渲染] 标记创建成功');
}

function getDefaultAvatar() {
  return "👤";
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
  if (!mapRef.value || lng === null || lng === undefined || lat === null || lat === undefined) return;
  if (isNaN(lng) || isNaN(lat)) return;
  console.log('[centerToPoint] 跳转到坐标:', lng, lat);
  mapRef.value.setCenter([lng, lat]);
}

function hasCoordinates(item) {
  const lng = item.lng;
  const lat = item.lat;
  if (lng === null || lng === undefined || lat === null || lat === undefined) return false;
  if (isNaN(lng) || isNaN(lat)) return false;
  return true;
}

function handleRemoveMarker(markerId) {
  const index = markers.value.findIndex(m => m.id === markerId);
  if (index !== -1) {
    markers.value.splice(index, 1);
    renderMarkers();
  }
}

function selectClusterMarker(marker) {
  showClusterModal.value = false;
  highlightId.value = marker.id;
  selectedMarker.value = marker;
  showDetailModal.value = true;
  renderMarkers();
}

const overlapDistance = 50;

function findOverlappingMarkers(markers) {
  const overlapMap = new Map();
  
  markers.forEach((m, i) => {
    if (!m.lng || !m.lat || isNaN(m.lng) || isNaN(m.lat)) return;
    
    markers.forEach((other, j) => {
      if (i >= j || !other.lng || !other.lat || isNaN(other.lng) || isNaN(other.lat)) return;
      
      const distance = Math.sqrt(
        Math.pow(m.lng - other.lng, 2) + Math.pow(m.lat - other.lat, 2)
      );
      
      if (distance < overlapDistance / 111000) {
        if (!overlapMap.has(m.id)) overlapMap.set(m.id, []);
        if (!overlapMap.has(other.id)) overlapMap.set(other.id, []);
        overlapMap.get(m.id).push(other);
        overlapMap.get(other.id).push(m);
      }
    });
  });
  
  return overlapMap;
}

function renderMarkers() {
  if (!mapRef.value || !window.AMap) return;

  markerObjs.value.forEach((m) => m.setMap(null));
  markerObjs.value = [];

  if (currentMode.value === 'repair') return;
  
  if (leftPanelMode.value === 'nav') return;

  let markersToRender = filteredMarkers.value;
  
  const currentUserId = localStorage.getItem("user_id");
  
  if (mapMode.value === 'publish') {
    markersToRender = markersToRender.filter(m => 
      String(m.publisher_id) === String(currentUserId)
    );
  } else {
    markersToRender = markersToRender.filter(m => 
      m.audit_status !== 'pending' || String(m.publisher_id) === String(currentUserId)
    );
  }

  const overlapMap = findOverlappingMarkers(markersToRender);

  markersToRender.forEach((m) => {
    if (!m.lng || !m.lat || isNaN(m.lng) || isNaN(m.lat)) return;

    const isLost = m.status === 0;
    const isPendingAudit = m.audit_status === 'pending';
    const markerColor = isPendingAudit ? "marker-pending" : (isLost ? "marker-lost" : "marker-found");
    const isOverlapping = overlapMap.has(m.id);
    const overlapClass = isOverlapping ? "overlap" : "";
    const isHighlighted = String(highlightId.value) === String(m.id);
    const isOwnPending = isPendingAudit && String(m.publisher_id) === String(localStorage.getItem('user_id'));
    const labelHtml = isHighlighted ? `<div class="marker-label">${isPendingAudit ? '⏳ ' : ''}${m.title || "未命名标记"}</div>` : "";
    const badgeHtml = isOverlapping && !isHighlighted ? `<div class="marker-badge">${overlapMap.get(m.id).length + 1}</div>` : "";

    const marker = new window.AMap.Marker({
      position: [m.lng, m.lat],
      map: mapRef.value,
      title: m.title,
      offset: new window.AMap.Pixel(-17, -48),
      content: `
        <div class="marker-wrap ${markerColor} ${overlapClass} ${isHighlighted ? "highlight" : ""}">
          <div class="marker-wave"></div>
          <div class="marker-core"></div>
          ${labelHtml}
          ${badgeHtml}
        </div>
      `,
    });

    marker.on("click", () => {
      if (mapMode.value === 'view') {
        if (isOverlapping) {
          const relatedMarkers = [m, ...overlapMap.get(m.id)];
          overlappingMarkers.value = relatedMarkers;
          showClusterModal.value = true;
        } else {
          highlightId.value = m.id;
          selectedMarker.value = m;
          showDetailModal.value = true;
          renderMarkers();
        }
      } else {
        pendingWorldPoint.value = { lng: m.lng, lat: m.lat };
        showPublishModal.value = true;
      }
    });

    markerObjs.value.push(marker);
  });
}

async function loadMarkers() {
  try {
    const campusId = currentCampus.value ? currentCampus.value.id : '';
    const viewerId = localStorage.getItem('user_id') || '';
    const timestamp = Date.now();
    const params = new URLSearchParams({ t: String(timestamp) });
    if (campusId) params.set('campus_id', campusId);
    if (viewerId) params.set('viewer_id', viewerId);
    const url = `${API_BASE}/map/markers?${params.toString()}`;
    console.log('[loadMarkers] 请求 URL:', url, '当前校区ID:', campusId, 'viewerId:', viewerId);
    const res = await fetch(url);
    const data = await res.json();
    console.log('[loadMarkers] 返回数据数量:', data.data?.length || 0);
    console.log('[loadMarkers] 原始返回数据示例:', data.data?.[0] ? {
      item_id: data.data[0].item_id,
      title: data.data[0].title,
      status: data.data[0].status,
      audit_status: data.data[0].audit_status,
      publisher_id: data.data[0].publisher_id
    } : '无数据');
    if (!data.success) {
      setStatus("标记加载失败");
      return;
    }

    const currentUserId = localStorage.getItem("user_id");
    console.log('[loadMarkers] 当前用户ID:', currentUserId);

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
        audit_status: item.audit_status || 'pending',
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
    repairMarkerObjs.value.forEach((m) => m.setMap && m.setMap(null));
    repairMarkerObjs.value = [];
    
    const campusId = currentCampus.value ? currentCampus.value.id : '';
    const url = campusId ? `${API_BASE}/repair?campus_id=${campusId}` : `${API_BASE}/repair`;
    console.log(`[DEBUG] Loading repair markers from: ${url}`);
    const res = await fetch(url);
    console.log(`[DEBUG] Response status: ${res.status}`);
    const data = await res.json();
    console.log(`[DEBUG] Repair data received:`, data);
    
    if (!data.success) {
      console.log(`[DEBUG] API returned success=false, message: ${data.message}`);
      return;
    }

    repairMarkers.value = (data.data || []).map((item) => {
      const lng = item.lng ? Number(item.lng) : null;
      const lat = item.lat ? Number(item.lat) : null;
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

  if (leftPanelMode.value === 'nav') {
    console.log(`[DEBUG] Early return: in navigation mode`);
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
    console.log(`[DEBUG] Processing marker: ${m.title}, lng=${m.lng}, lat=${m.lat}`);
    if (!m.lng || !m.lat || isNaN(m.lng) || isNaN(m.lat)) {
      console.log(`[DEBUG] Skipping marker: invalid coordinates`);
      return;
    }

    const marker = new window.AMap.Marker({
      position: [m.lng, m.lat],
      map: mapRef.value,
      title: m.title,
      offset: new window.AMap.Pixel(-17, -48),
      extData: { repair_id: m.repair_id, status: m.status },
      content: `
        <div class="marker-wrap marker-repair priority-${m.priority || 2}">
          <div class="marker-wave repair-wave"></div>
          <div class="marker-core repair-core"></div>
          <div class="marker-label">${m.title || "报修"}</div>
        </div>
      `,
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

function handleSubmitRepair(data) {
  showRepairModal.value = false;
  loadRepairMarkers();
}

function handleRepairDoubleClick(repair) {
  centerToPoint(repair.lng, repair.lat);
  showRepairDetail(repair);
}

function showRepairDetail(repair) {
  currentDetailRepair.value = repair;
  showRepairDetailModal.value = true;
}

function handleRepairUpdated(payload) {
  if (!payload || !payload.repair) return;
  if (payload.action === 'complete') {
    const repairId = payload.repair.repair_id;
    repairMarkers.value = repairMarkers.value.filter(m => m.repair_id !== repairId);
    const idx = repairMarkerObjs.value.findIndex(m => {
      const pos = m.getPosition && m.getPosition();
      return pos && String(m.getExtData && m.getExtData().repair_id) === String(repairId);
    });
    if (idx !== -1) {
      const marker = repairMarkerObjs.value[idx];
      if (marker && marker.setMap) {
        marker.setMap(null);
      }
      repairMarkerObjs.value.splice(idx, 1);
    } else {
      repairMarkerObjs.value.forEach(m => m.setMap && m.setMap(null));
      repairMarkerObjs.value = [];
      renderRepairMarkers();
    }
  } else if (payload.action === 'start') {
    renderRepairMarkers();
  }
}

function openRepairModal(e) {
  const lng = e.lnglat.lng;
  const lat = e.lnglat.lat;
  repairLng.value = lng;
  repairLat.value = lat;
  showRepairModal.value = true;
}

function initMap(config) {
  const AMap = window.AMap;
  if (!AMap) {
    throw new Error('高德地图 SDK 未就绪');
  }

  try {
    mapRef.value = new AMap.Map(mapContainerId, {
      zoom: config.zoom || 18,
      center: [config.center_lng, config.center_lat],
      viewMode: "2D",
      showIndoorMap: false,
      resizeEnable: true,
    });
  } catch (err) {
    console.warn('2D 地图初始化失败，尝试备用配置', err);
    mapRef.value = new AMap.Map(mapContainerId, {
      zoom: config.zoom || 16,
      center: [config.center_lng, config.center_lat],
      resizeEnable: true,
    });
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

function toggleMode() {
  currentMode.value = currentMode.value === 'lost' ? 'repair' : 'lost';
  updateStatusText();
  renderMarkers();
  renderRepairMarkers();
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

// 校区切换函数
function switchCampus(campus) {
  console.log('[校区切换] 切换到:', campus.name, campus.id, '坐标:', campus.center);
  currentCampus.value = campus;
  if (mapRef.value && window.AMap) {
    console.log('[校区切换] 设置地图中心:', campus.center, '缩放级别:', campus.zoom);
    // 跳转效果 - 无动画直接切换到新校区
    mapRef.value.setZoomAndCenter(campus.zoom, campus.center, false);
    // 重置pitch为0（完全俯视），避免中心点在边缘的问题
    mapRef.value.setPitch(0);
    // 如果校区有bounds，则设置地图的边界
    if (campus.bounds) {
      const bounds = new window.AMap.Bounds(
        campus.bounds.sw,
        campus.bounds.ne
      );
      mapRef.value.setBounds(bounds, false);
    }
  }
  // 切换校区时，只有不在导航模式才重新加载对应校区的数据
  if (leftPanelMode.value !== 'nav') {
    console.log('[校区切换] 调用 loadMarkers()');
    loadMarkers();
    loadRepairMarkers();
  }
}

async function loadDefaultMap() {
  try {
    const res = await fetch(`${API_BASE}/map/default`);
    const config = await res.json();
    if (!config || config.error) {
      setStatus("地图配置加载失败");
      return;
    }
    await loadAMap({ plugins: ['AMap.Driving'] });
    mapLoadError.value = false;
    mapLoadErrorMsg.value = "";
    initMap(config);
  } catch (error) {
    console.error(error);
    mapLoadError.value = true;
    mapLoadErrorMsg.value = error.message || "高德地图加载失败";
    setStatus(mapLoadErrorMsg.value);
  }
}

async function retryLoadMap() {
  resetAMapLoader();
  mapLoadError.value = false;
  mapLoadErrorMsg.value = "";
  setStatus("正在重新加载地图...");
  await loadDefaultMap();
  if (!mapLoadError.value) {
    await loadMarkers();
    await loadRepairMarkers();
  }
}

function handleModeSwitch(mode) {
  if (currentMode.value === mode) return;
  
  if (mapRef.value) {
    const allOverlays = mapRef.value.getAllOverlays();
    allOverlays.forEach(overlay => {
      if (overlay instanceof window.AMap.Marker) {
        mapRef.value.remove(overlay);
      }
    });
  }
  
  currentMode.value = mode;
  listExpanded.value = false;
  highlightId.value = null;
  
  if (mode === 'lostFound' || mode === 'lost') {
    loadMarkers();
    renderCentralMarker();
  } else if (mode === 'repair') {
    loadRepairMarkers();
  }
}

function handleModeSwitchFromNav(mode) {
  // 先切换回列表模式
  leftPanelMode.value = 'list';
  
  // 然后处理模式切换
  if (mode === 'navigation') {
    // 已经在导航模式了，不做处理
    return;
  }
  
  // 强制刷新标记
  currentMode.value = mode;
  
  if (mode === 'lostFound' || mode === 'lost') {
    loadMarkers();
  } else if (mode === 'repair') {
    loadRepairMarkers();
  }
}

function toggleNavPanel() {
  showNavPanel.value = !showNavPanel.value;
}

function handleOpenNav() {
  leftPanelMode.value = 'nav';
  // 清除地图上的标记
  if (mapRef.value) {
    const allOverlays = mapRef.value.getAllOverlays();
    allOverlays.forEach(overlay => {
      if (overlay instanceof window.AMap.Marker) {
        overlay.setMap(null);
      }
    });
    markerObjs.value = [];
    repairMarkerObjs.value = [];
  }
}

function switchToList() {
  leftPanelMode.value = 'list';
  // 重新加载标记
  if (currentMode.value === 'lost') {
    renderMarkers();
    renderCentralMarker();
  } else {
    renderRepairMarkers();
  }
}

async function openAddModal() {
  pendingWorldPoint.value = null;
  showPublishModal.value = true;
}

function handlePublishSubmit(data) {
  setStatus("发布成功，等待审核");
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
  // 位置选择现在由PublishModal内部处理
}

function handleItemClick(item) {
  highlightId.value = item.id;
  console.log('[handleItemClick] 点击物品:', item.title, '坐标:', item.lng, item.lat, 'hasCoordinates:', hasCoordinates(item));
  
  if (clickTimer) {
    clearTimeout(clickTimer);
    return;
  }
  
  clickTimer = setTimeout(() => {
    if (hasCoordinates(item)) {
      console.log('[handleItemClick] 执行跳转');
      centerToPoint(item.lng, item.lat);
      renderMarkers();
    } else {
      console.log('[handleItemClick] 物品无有效坐标，跳转取消');
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

function goToCommunity() {
  router.push("/community");
}

function goToMessages() {
  router.push("/messages?from=home");
}

function goToAppointmentList() {
  showAppointmentModal.value = true;
}

watch(
  () => mode.value,
  () => nextTick(() => mapRef.value && mapRef.value.resize()),
);

watch(filterStatus, () => {
  renderMarkers();
});

onMounted(async () => {
  await loadCampuses()
  await loadDefaultMap();
  await loadMarkers();
  await loadRepairMarkers();
  await loadUserInfo();
  await loadCategories();
  // 延迟加载集中点，确保地图完全初始化
  setTimeout(() => {
    loadCentralLocation();
  }, 500);
  
  const locateMarker = sessionStorage.getItem('locateMarker');
  if (locateMarker) {
    try {
      const marker = JSON.parse(locateMarker);
      if (marker.lat && marker.lng) {
        setTimeout(() => {
          centerToPoint(marker.lng, marker.lat);
          window.showToast(`已定位到: ${marker.title || '该位置'}`, 'success');
        }, 500);
      }
    } catch (e) {
      console.error('解析定位信息失败:', e);
    } finally {
      sessionStorage.removeItem('locateMarker');
    }
  }
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
        <button class="community-btn" type="button" title="校园社区" @click="goToCommunity">
          📢
        </button>
        <button class="notification-btn" type="button" title="预约领取" @click="goToAppointmentList">
          📅
        </button>
        <button class="notification-btn" type="button" title="通知消息" @click="goToMessages">
          🔔
        </button>
        <button class="avatar-btn" type="button" title="前往个人主页" @click="goProfile">
          <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" />
          <span v-else>{{ getDefaultAvatar() }}</span>
        </button>
      </template>
    </AppTopBar>

    <main :class="appClass">
      <div class="list-wrapper">
        <!-- 列表面板 -->
        <template v-if="leftPanelMode === 'list'">
          <ListPanel
            v-if="currentMode !== 'repair'"
            :markers="markers"
            v-model:filterStatus="filterStatus"
            v-model:expanded="listExpanded"
            :currentCampus="currentCampus"
            @itemClick="handleItemClick"
            @itemDoubleClick="openDetail"
            @add="openAddModal"
            @modeSwitch="handleModeSwitch"
            @openNav="handleOpenNav"
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
            @openNav="handleOpenNav"
          />
        </template>
        
        <!-- 导航面板 -->
      <template v-else>
        <NavPanel 
          :visible="true" 
          :mapRef="mapRef"
          :currentCampus="currentCampus"
          @close="switchToList"
          @modeSwitch="handleModeSwitchFromNav"
        />
      </template>
      </div>

      <section class="map-panel">
        <div :id="mapContainerId"></div>

        <div v-if="mapLoadError" class="map-error-overlay">
          <div class="map-error-card">
            <p class="map-error-title">地图加载失败</p>
            <p class="map-error-desc">{{ mapLoadErrorMsg }}</p>
            <ul class="map-error-tips">
              <li>请检查网络是否能访问高德地图服务</li>
              <li>关闭广告拦截插件后重试</li>
              <li>确认高德控制台 Key 白名单包含 localhost 和 127.0.0.1</li>
            </ul>
            <button type="button" class="map-error-retry" @click="retryLoadMap">重新加载</button>
          </div>
        </div>

        
        <div
          :style="{
            position: 'absolute',
            top: '12px',
            left: '12px',
            zIndex: '100',
          }"
        >
          <!-- 校区选择器 -->
          <div
            :style="{
              marginBottom: '8px'
            }"
          >
            <select
              :value="currentCampus ? currentCampus.id : ''"
              @change="(e) => {
                const selectedId = Number(e.target.value);
                const campus = campuses.find(c => c.id === selectedId);
                if (campus) switchCampus(campus);
              }"
              :style="{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                background: '#111827',
                color: '#fff',
                cursor: 'pointer',
                fontSize: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }"
            >
              <option
                v-for="campus in campuses"
                :key="campus.id"
                :value="campus.id"
              >
                {{ campus.name }}
              </option>
            </select>
          </div>

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
          <button
            :style="{
              width: '100%',
              padding: '8px 12px',
              borderRadius: '4px',
              border: 'none',
              background: mode === 'fullmap' ? '#3B82F6' : 'transparent',
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
            {{ mode === 'fullmap' ? '◀ 返回分栏' : '▶ 全图模式' }}
          </button>
        </div>
      </div>
      
      <div
        v-if="leftPanelMode !== 'nav'"
        :style="{
          position: 'absolute',
          top: '12px',
          right: '12px',
          zIndex: '100',
          display: 'flex',
          gap: '8px'
        }"
      >
        <button
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
          @click="toggleMapMode"
        >
          <span :style="{ color: mapMode === 'view' ? '#fff' : '#6B7280', fontWeight: mapMode === 'view' ? '600' : '400' }">查看</span>
          <span style="color: '#6B7280';">|</span>
          <span :style="{ color: mapMode === 'publish' ? '#fff' : '#6B7280', fontWeight: mapMode === 'publish' ? '600' : '400' }">发布</span>
        </button>
      </div>
    </section>
  </main>

    <PublishModal
      :show="showPublishModal"
      :pendingLocation="pendingWorldPoint"
      :categories="categories"
      :currentCampus="currentCampus"
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
      @close="showDetailModal = false"
      @remove="handleRemoveMarker"
      @locate="(m) => { highlightId = m.id; centerToPoint(m.lng, m.lat); renderMarkers(); }"
    />

    <div v-if="showClusterModal" class="cluster-modal-overlay" @click="showClusterModal = false">
      <div class="cluster-modal" @click.stop>
        <div class="cluster-modal-header">
          <h3>重叠标记 ({{ overlappingMarkers.length }}个)</h3>
          <button class="cluster-modal-close" @click="showClusterModal = false">×</button>
        </div>
        <div class="cluster-modal-list">
          <div 
            v-for="m in overlappingMarkers" 
            :key="m.id" 
            class="cluster-item"
            @click="selectClusterMarker(m)"
          >
            <div :class="['cluster-item-icon', m.status === 0 ? 'lost' : 'found']"></div>
            <div class="cluster-item-info">
              <div class="cluster-item-title">{{ m.title || '未命名标记' }}</div>
              <div class="cluster-item-status">{{ m.status === 0 ? '丢失物品' : '拾获物品' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

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
      :currentUserId="currentUserId"
      :currentUserRole="currentUserRole"
      @close="showRepairDetailModal = false"
      @updated="handleRepairUpdated"
    />
    
    <AppointmentModal
      v-if="showAppointmentModal"
      @close="showAppointmentModal = false"
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
                {{ currentMode === 'lost' ? (marker.status === 0 ? '🔴' : '🟢') : '🔧' }}
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
/* 社区按钮样式 */
.community-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
  font-size: 18px;
  border: none;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
  padding: 0;
  margin: 0;
  line-height: 42px;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  transition: transform 0.2s;
}

.community-btn:hover {
  transform: scale(1.08);
}

/* 顶部栏按钮样式 - 与AppTopBar保持一致 */
.notification-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 18px;
  border: none;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
  padding: 0;
  margin: 0;
  line-height: 42px;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  transition: transform 0.2s;
}

.notification-btn:hover {
  transform: scale(1.08);
}

.avatar-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 18px;
  border: none;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
  padding: 0;
  margin: 0;
  line-height: 42px;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  transition: transform 0.2s;
}

.avatar-btn:hover {
  transform: scale(1.08);
}

.avatar-btn img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-btn span {
  display: inline-block;
  vertical-align: middle;
  line-height: normal;
}

.marker-wrap.marker-repair {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
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

.list-wrapper {
  position: relative;
}

/* 集中点（失物招领处）标记样式 - 黄色 */
.marker-wrap.marker-central {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1000;
}

.marker-wave-central {
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(251, 191, 36, 0.3);
  animation: centralPulse 2s ease-out infinite;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

@keyframes centralPulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.8;
  }
  100% {
    transform: translate(-50%, -50%) scale(2.5);
    opacity: 0;
  }
}

.marker-core-central {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(251, 191, 36, 0.5);
  position: relative;
  z-index: 1;
  border: 3px solid #fff;
}

.back-to-list-btn:hover {
  background: #2563eb !important;
}</style>