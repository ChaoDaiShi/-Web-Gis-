<!-- 导航面板 - 参照ListPanel样式 -->
<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from "vue";
const showToast = window.showToast;

const props = defineProps({
  mapRef: Object,
  visible: Boolean,
  currentCampus: Object
});

const emit = defineEmits(["close", "modeSwitch"]);

const showModeMenu = ref(false);
const API_BASE = "http://127.0.0.1:5000";
const startPoint = ref({ lng: null, lat: null, name: "" });
const endPoint = ref({ lng: null, lat: null, name: "" });
const selectedStartNodeId = ref(null);
const selectedEndNodeId = ref(null);
const nodes = ref([]);
const routes = ref([]);
const isCalculating = ref(false);
const showPath = ref(false);
const selectedRouteIndex = ref(0);
let drivingInstance = null;

const optimalRouteIndex = computed(() => {
  if (routes.value.length === 0) return 0;
  let minTime = Infinity;
  let index = 0;
  routes.value.forEach((route, i) => {
    if (route.time < minTime) {
      minTime = route.time;
      index = i;
    }
  });
  return index;
});

async function loadNodes() {
  try {
    let campusId = 'campus_1';
    if (props.currentCampus && props.currentCampus.id) {
      campusId = props.currentCampus.id;
    }
    const res = await fetch(`${API_BASE}/api/nav/nodes?campus_id=${campusId}`);
    const data = await res.json();
    if (data.success && data.data) {
      nodes.value = data.data;
    } else {
      nodes.value = [];
    }
  } catch (e) {
    console.error("加载导航节点失败:", e);
    nodes.value = [];
  }
}

async function calculatePath() {
  if (!startPoint.value.lng || !endPoint.value.lng) {
    showToast("请选择起点和终点", "warning");
    return;
  }
  isCalculating.value = true;
  showPath.value = false;
  routes.value = [];
  selectedRouteIndex.value = 0;
  
  if (!window.AMap) {
    showToast("高德地图未加载", "error");
    isCalculating.value = false;
    return;
  }
  if (!window.AMap.Driving) {
    showToast("高德地图导航插件未加载", "error");
    isCalculating.value = false;
    return;
  }
  
  if (drivingInstance) {
    drivingInstance.clear();
  }
  
  const timeout = setTimeout(() => {
    showToast("路径计算超时", "error");
    isCalculating.value = false;
  }, 15000);
  
  try {
    drivingInstance = new window.AMap.Driving({
      map: props.mapRef,
      policy: window.AMap.DrivingPolicy.LEAST_TIME,
      alternativePolicy: 2
    });
    
    drivingInstance.search(
      new window.AMap.LngLat(startPoint.value.lng, startPoint.value.lat),
      new window.AMap.LngLat(endPoint.value.lng, endPoint.value.lat),
      function(status, result) {
        clearTimeout(timeout);
        isCalculating.value = false;
        
        if (status === "complete" && result.routes && result.routes.length > 0) {
          routes.value = result.routes.map((route, index) => {
            return {
              name: `方案${index + 1}`,
              distance: parseFloat(route.distance),
              time: parseFloat(route.time),
              path: route.path,
              steps: route.steps || [],
              isOptimal: index === optimalRouteIndex.value
            };
          });
          showPath.value = true;
          selectedRouteIndex.value = optimalRouteIndex.value;
          showToast(`已找到 ${routes.value.length} 条路径`, "success");
        } else {
          const errorMsg = result?.info || "未知错误";
          showToast("无法找到路径: " + errorMsg, "warning");
        }
      }
    );
  } catch (e) {
    clearTimeout(timeout);
    isCalculating.value = false;
    console.error("路径计算失败:", e);
    showToast("路径计算失败", "error");
  }
}

function selectRoute(index) {
  selectedRouteIndex.value = index;
  if (drivingInstance && routes.value[index]) {
    drivingInstance.clear();
    drivingInstance.search(
      new window.AMap.LngLat(startPoint.value.lng, startPoint.value.lat),
      new window.AMap.LngLat(endPoint.value.lng, endPoint.value.lat),
      function(status, result) {
        if (status === "complete" && result.routes && result.routes.length > index) {
          drivingInstance.setRoute(result.routes[index]);
        }
      }
    );
  }
}

function handleStartNodeChange(nodeId) {
  if (!nodeId) return;
  const node = nodes.value.find(n => n.node_id == nodeId);
  if (node) {
    startPoint.value = {
      lng: parseFloat(node.lng),
      lat: parseFloat(node.lat),
      name: node.name
    };
    showPath.value = false;
    routes.value = [];
  }
}

function handleEndNodeChange(nodeId) {
  if (!nodeId) return;
  const node = nodes.value.find(n => n.node_id == nodeId);
  if (node) {
    endPoint.value = {
      lng: parseFloat(node.lng),
      lat: parseFloat(node.lat),
      name: node.name
    };
    showPath.value = false;
    routes.value = [];
  }
}

function setCurrentLocation(type) {
  if (!navigator.geolocation) {
    showToast("您的浏览器不支持地理定位", "warning");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const point = {
        lng: position.coords.longitude,
        lat: position.coords.latitude,
        name: "当前位置"
      };
      if (type === "start") {
        startPoint.value = point;
        selectedStartNodeId.value = null;
      } else {
        endPoint.value = point;
        selectedEndNodeId.value = null;
      }
      showPath.value = false;
      routes.value = [];
      showToast("已获取当前位置", "success");
    },
    (error) => {
      showToast("获取位置失败: " + error.message, "warning");
    }
  );
}

function swapPoints() {
  const tempStart = { ...startPoint.value };
  const tempStartId = selectedStartNodeId.value;
  
  startPoint.value = { ...endPoint.value };
  selectedStartNodeId.value = selectedEndNodeId.value;
  
  endPoint.value = tempStart;
  selectedEndNodeId.value = tempStartId;
  
  showPath.value = false;
  routes.value = [];
}

function fullReset() {
  selectedStartNodeId.value = null;
  selectedEndNodeId.value = null;
  startPoint.value = { lng: null, lat: null, name: "" };
  endPoint.value = { lng: null, lat: null, name: "" };
  routes.value = [];
  showPath.value = false;
  selectedRouteIndex.value = 0;
  if (drivingInstance) {
    drivingInstance.clear();
    drivingInstance = null;
  }
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadNodes();
  } else {
    fullReset();
  }
});

watch(() => props.currentCampus, (newCampus) => {
  if (props.visible && newCampus) {
    loadNodes();
  }
}, { deep: true });

onMounted(() => {
  if (props.visible) {
    loadNodes();
  }
});

onUnmounted(() => {
  fullReset();
});
</script>

<template>
  <aside class="nav-panel" v-if="visible">
    <div class="nav-header">
      <div class="header-top">
        <div class="mode-switch">
          <button class="mode-btn" @click="showModeMenu = !showModeMenu">
            服务 ▼
          </button>
          <div v-if="showModeMenu" class="mode-menu">
            <button @click="emit('close')">失物招领</button>
            <button @click="emit('modeSwitch', 'repair')">报修申请</button>
            <button @click="showModeMenu = false">校园路径</button>
          </div>
        </div>
      </div>
      <div class="header-bottom">
        <h3>校园导航</h3>
      </div>
    </div>

    <div class="nav-content">
      <template v-if="nodes.length === 0">
        <div class="no-nodes">
          <div class="no-nodes-icon">🗺️</div>
          <div class="no-nodes-text">暂无可规划路径</div>
        </div>
      </template>
      
      <template v-else>
        <div class="section">
          <label>起点</label>
          <div class="point-selector">
            <select v-model="selectedStartNodeId" @change="handleStartNodeChange(selectedStartNodeId)">
              <option :value="null">选择起点...</option>
              <option v-for="node in nodes" :key="'start-' + node.node_id" :value="node.node_id">
                {{ node.name }}
              </option>
            </select>
            <button class="location-btn" @click="setCurrentLocation('start')" title="使用当前位置">
              📍
            </button>
          </div>
          <div v-if="startPoint.lng" class="point-info">
            {{ startPoint.name || '自定义位置' }} ({{ startPoint.lng.toFixed(6) }}, {{ startPoint.lat.toFixed(6) }})
          </div>
        </div>

        <div class="swap-btn" @click="swapPoints" title="交换起点和终点">
          ↕
        </div>

        <div class="section">
          <label>终点</label>
          <div class="point-selector">
            <select v-model="selectedEndNodeId" @change="handleEndNodeChange(selectedEndNodeId)">
              <option :value="null">选择终点...</option>
              <option v-for="node in nodes" :key="'end-' + node.node_id" :value="node.node_id">
                {{ node.name }}
              </option>
            </select>
            <button class="location-btn" @click="setCurrentLocation('end')" title="使用当前位置">
              📍
            </button>
          </div>
          <div v-if="endPoint.lng" class="point-info">
            {{ endPoint.name || '自定义位置' }} ({{ endPoint.lng.toFixed(6) }}, {{ endPoint.lat.toFixed(6) }})
          </div>
        </div>

        <button class="calc-btn" @click="calculatePath" :disabled="isCalculating">
          {{ isCalculating ? "计算中..." : "🧭 路径规划" }}
        </button>

        <div v-if="showPath && routes.length > 0" class="routes-result">
          <div class="routes-header">找到 {{ routes.length }} 条路径</div>
          <div class="routes-list">
            <div v-for="(route, index) in routes" :key="index" class="route-item" 
                 :class="{ active: selectedRouteIndex === index, optimal: route.isOptimal }"
                 @click="selectRoute(index)">
              <div class="route-header">
                <span class="route-name">{{ route.name }}</span>
                <span v-if="route.isOptimal" class="optimal-badge">最优</span>
              </div>
              <div class="route-info">
                <span class="distance">📏 {{ (route.distance / 1000).toFixed(2) }} 公里</span>
                <span class="time">⏱️ {{ Math.round(route.time / 60) }} 分钟</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </aside>
</template>

<style scoped>
.nav-panel {
  width: var(--list-width);
  background: linear-gradient(135deg, #fffef5 0%, #fff9c4 100%);
  border-radius: 8px;
  overflow: auto;
  transition: width 0.25s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.nav-header {
  position: sticky;
  top: 0;
  background: #fef3c7;
  color: #92400e;
  padding: 12px 16px;
  font-weight: 700;
  border-bottom: 1px solid #fde68a;
}

.header-top {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 8px;
}

.header-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.mode-switch {
  position: relative;
  display: inline-block;
}

.mode-btn {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.mode-btn:hover {
  background: #45a049;
}

.mode-menu {
  position: absolute;
  left: 0;
  top: 100%;
  margin-top: 4px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  z-index: 100;
  min-width: 140px;
}

.mode-menu button {
  display: block;
  width: 100%;
  padding: 12px 28px;
  text-align: left;
  border: none;
  background: none;
  color: #333;
  cursor: pointer;
  font-size: 15px;
  transition: background 0.2s;
}

.mode-menu button:hover {
  background: #f5f5f5;
}

.nav-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.no-nodes {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.no-nodes-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.no-nodes-text {
  color: #9ca3af;
  font-size: 16px;
  font-weight: 500;
}

.section {
  margin-bottom: 16px;
  background: #fff;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.section label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.point-selector {
  display: flex;
  gap: 8px;
}

.point-selector select {
  flex: 1;
  padding: 10px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.point-selector select:hover {
  border-color: #f59e0b;
}

.point-selector select:focus {
  outline: none;
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
}

.location-btn {
  padding: 10px 14px;
  background: #10b981;
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.location-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
}

.point-info {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 12px;
  color: #6b7280;
}

.swap-btn {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px;
  margin: 8px 0;
  color: #f59e0b;
  font-size: 24px;
  cursor: pointer;
  transition: all 0.2s;
}

.swap-btn:hover {
  transform: scale(1.2);
}

.calc-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}

.calc-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
}

.calc-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.routes-result {
  margin-top: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  overflow: hidden;
}

.routes-header {
  padding: 12px 14px;
  background: #fef3c7;
  color: #92400e;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid #fde68a;
}

.routes-list {
  padding: 8px;
}

.route-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  border: 2px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.route-item:hover {
  border-color: #f59e0b;
  background: #fffbeb;
}

.route-item.active {
  border-color: #10b981;
  background: #ecfdf5;
}

.route-item.optimal {
  border-left: 4px solid #f59e0b;
}

.route-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.route-name {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.optimal-badge {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.route-info {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
}

.distance, .time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-content::-webkit-scrollbar {
  width: 8px;
}

.nav-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.nav-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #888 0%, #666 100%);
  border-radius: 4px;
  transition: background 0.3s;
}

.nav-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #666 0%, #444 100%);
}
</style>
