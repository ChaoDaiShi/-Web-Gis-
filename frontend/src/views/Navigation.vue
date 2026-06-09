<template>
  <div class="navigation-page">
    <div class="header">
      <button class="back-btn" @click="goBack">← 返回首页</button>
      <h1>🗺️ 成都信息工程大学导航</h1>
    </div>

    <div class="main-content">
      <div class="control-panel">
        <div class="section">
          <label>📍 起点</label>
          <div class="input-group">
            <select v-model="startId" @change="clearPath">
              <option :value="null">请选择起点...</option>
              <option v-for="node in nodes" :key="'s-' + node.node_id" :value="node.node_id">
                {{ node.name }}
              </option>
            </select>
            <button class="locate-btn" @click="locateCurrentPosition('start')" title="获取当前位置">
              📍
            </button>
          </div>
          <div v-if="currentLocation" class="location-status">
            <span class="status-text">{{ locationStatus }}</span>
          </div>
        </div>

        <div class="swap-btn" @click="swap">🔄</div>

        <div class="section">
          <label>🎯 终点</label>
          <select v-model="endId" @change="clearPath">
            <option :value="null">请选择终点...</option>
            <option v-for="node in nodes" :key="'e-' + node.node_id" :value="node.node_id">
              {{ node.name }}
            </option>
          </select>
        </div>

        <button class="calc-btn" @click="findPath" :disabled="isLoading">
          {{ isLoading ? '计算中...' : '🚀 开始导航' }}
        </button>

        <div v-if="pathInfo" class="result-panel">
          <div class="distance">
            📏 总距离: {{ (pathInfo.distance / 1000).toFixed(2) }} 公里 
            ({{ pathInfo.distance.toFixed(0) }} 米)
          </div>
          <div class="time">
            ⏱️ 预计时间: {{ pathInfo.time }} 分钟
          </div>
          <div class="path-steps">
            <div v-for="(step, i) in pathInfo.steps" :key="i" class="step">
              {{ step }}
            </div>
          </div>
          <div class="nav-buttons">
            <button class="nav-btn nav-btn-amap" @click="openAMapNavigation">
              🗺️ 打开高德地图导航
            </button>
            <button class="clear-btn" @click="clearPath">清除路径</button>
          </div>
        </div>
      </div>

      <div class="map-container" id="mapContainer">
        <div v-if="!mapReady" class="loading">
          <div class="spinner"></div>
          <p>加载地图中...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { loadAMap } from '../utils/amapLoader.js'

const showToast = window.showToast
const API_BASE = 'http://127.0.0.1:5000'

const nodes = ref([])
const startId = ref(null)
const endId = ref(null)
const pathInfo = ref(null)
const isLoading = ref(false)
const mapReady = ref(false)
const currentLocation = ref(null)
const locationStatus = ref('')

let map = null
let pathPolyline = null
let markers = []

async function loadNodes() {
  try {
    const res = await fetch(API_BASE + '/api/nav/nodes')
    const data = await res.json()
    if (data.success && data.data) {
      nodes.value = data.data.map(n => ({
        ...n,
        lng: parseFloat(n.lng),
        lat: parseFloat(n.lat)
      }))
    }
  } catch (e) {
    console.error('加载节点失败:', e)
  }
}

async function initMap() {
  try {
    const AMap = await loadAMap({ plugins: ['AMap.ToolBar', 'AMap.Scale', 'AMap.Geolocation'] })
    map = new AMap.Map('mapContainer', {
      center: [103.987, 30.582],
      zoom: 17,
      viewMode: '2D'
    })

    map.addControl(new AMap.ToolBar())
    map.addControl(new AMap.Scale())
    
    const geolocation = new AMap.Geolocation({
      enableHighAccuracy: true,
      timeout: 10000,
      buttonOffset: new AMap.Pixel(10, 20),
      buttonPosition: 'RT',
      showMarker: true,
      showCircle: true,
      panToLocation: true,
      zoomToAccuracy: true
    })
    
    map.addControl(geolocation)
    
    mapReady.value = true
  } catch (e) {
    console.error('地图初始化失败:', e)
    mapReady.value = false
  }
}

function getNodeName(id) {
  const node = nodes.value.find(n => n.node_id == id)
  return node ? node.name : ''
}

function getNodeCoord(id) {
  const node = nodes.value.find(n => n.node_id == id)
  return node ? [node.lng, node.lat] : null
}

async function findPath() {
  if (!startId.value || !endId.value) {
    showToast('请选择起点和终点！', 'warning')
    return
  }

  const startCoord = getNodeCoord(startId.value)
  const endCoord = getNodeCoord(endId.value)
  if (!startCoord || !endCoord) {
    showToast('坐标数据错误！', 'error')
    return
  }

  isLoading.value = true
  pathInfo.value = null
  clearMapPath()

  try {
    const url = `${API_BASE}/api/nav/path?start_lng=${startCoord[0]}&start_lat=${startCoord[1]}&end_lng=${endCoord[0]}&end_lat=${endCoord[1]}`
    const res = await fetch(url)
    const data = await res.json()

    if (data.success && data.data) {
      const coords = data.data.coordinates.map(c => [
        parseFloat(c[0]),
        parseFloat(c[1])
      ])

      pathInfo.value = {
        distance: parseFloat(data.data.total_distance),
        time: parseInt(data.data.estimated_time) || 0,
        steps: [
          `从「${getNodeName(startId.value)}」出发`,
          ...data.data.path.map(p => `经过「${getNodeName(p.to_node)}」`),
          `到达「${getNodeName(endId.value)}」`
        ]
      }

      drawPath(coords, startCoord, endCoord)
    } else {
      showToast(data.message || '找不到路径！', 'warning')
    }
  } catch (e) {
    console.error('路径计算失败:', e)
    showToast('计算失败，请重试！', 'error')
  } finally {
    isLoading.value = false
  }
}

function drawPath(coords, start, end) {
  if (!map || !window.AMap) return

  const AMap = window.AMap

  if (pathPolyline) {
    map.remove(pathPolyline)
  }

  if (markers.length > 0) {
    map.remove(markers)
    markers = []
  }

  pathPolyline = new AMap.Polyline({
    path: coords,
    strokeColor: '#33ccff',
    strokeOpacity: 0.8,
    strokeWeight: 5,
    strokeStyle: 'solid'
  })

  map.add(pathPolyline)

  const startMarker = new AMap.Marker({
    position: start,
    content: '<div style="background:#28a745;color:white;padding:5px 10px;border-radius:3px;font-size:12px;">起点</div>',
    offset: new AMap.Pixel(-25, -30)
  })

  const endMarker = new AMap.Marker({
    position: end,
    content: '<div style="background:#dc3545;color:white;padding:5px 10px;border-radius:3px;font-size:12px;">终点</div>',
    offset: new AMap.Pixel(-25, -30)
  })

  map.add(startMarker)
  map.add(endMarker)
  markers.push(startMarker, endMarker)

  map.setFitView()
}

function clearMapPath() {
  if (map) {
    if (pathPolyline) {
      map.remove(pathPolyline)
      pathPolyline = null
    }
    if (markers.length > 0) {
      map.remove(markers)
      markers = []
    }
  }
}

function clearPath() {
  pathInfo.value = null
  clearMapPath()
}

function swap() {
  const temp = startId.value
  startId.value = endId.value
  endId.value = temp
  clearPath()
}

function goBack() {
  window.location.href = '/home'
}

function wgs84ToGcj02(lng, lat) {
  const a = 6378245.0
  const ee = 0.00669342162296594323
  const pi = 3.1415926535897932384626

  if (outOfChina(lng, lat)) {
    return [lng, lat]
  }

  let dLat = transformLat(lng - 105.0, lat - 35.0)
  let dLng = transformLng(lng - 105.0, lat - 35.0)
  const radLat = lat / 180.0 * pi
  let magic = Math.sin(radLat)
  magic = 1 - ee * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * pi)
  dLng = (dLng * 180.0) / (a / sqrtMagic * Math.cos(radLat) * pi)
  const mgLat = lat + dLat
  const mgLng = lng + dLng

  return [mgLng, mgLat]
}

function transformLat(lng, lat) {
  let ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * Math.sqrt(Math.abs(lng))
  ret += (20.0 * Math.sin(6.0 * lng * Math.PI) + 20.0 * Math.sin(2.0 * lng * Math.PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(lat * Math.PI) + 40.0 * Math.sin(lat / 3.0 * Math.PI)) * 2.0 / 3.0
  ret += (160.0 * Math.sin(lat / 12.0 * Math.PI) + 320 * Math.sin(lat * Math.PI / 30.0)) * 2.0 / 3.0
  return ret
}

function transformLng(lng, lat) {
  let ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * Math.sqrt(Math.abs(lng))
  ret += (20.0 * Math.sin(6.0 * lng * Math.PI) + 20.0 * Math.sin(2.0 * lng * Math.PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(lng * Math.PI) + 40.0 * Math.sin(lng / 3.0 * Math.PI)) * 2.0 / 3.0
  ret += (150.0 * Math.sin(lng / 12.0 * Math.PI) + 300.0 * Math.sin(lng / 30.0 * Math.PI)) * 2.0 / 3.0
  return ret
}

function outOfChina(lng, lat) {
  return (lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271 || false)
}

function locateCurrentPosition(target) {
  locationStatus.value = '获取位置中...'
  
  if (map && window.AMap && window.AMap.Geolocation) {
    const AMap = window.AMap
    const geolocation = new AMap.Geolocation({
      enableHighAccuracy: true,
      timeout: 15000,
      showMarker: false,
      showCircle: false,
      panToLocation: false,
      zoomToAccuracy: false
    })
    
    geolocation.getCurrentPosition(async (status, result) => {
      if (status === 'complete') {
        const lng = result.position.lng
        const lat = result.position.lat
        
        currentLocation.value = { lng, lat }
        locationStatus.value = '定位成功！'
        
        showToast('已获取当前位置', 'success')
        
        try {
          const url = `${API_BASE}/api/nav/nearest-node?lng=${lng}&lat=${lat}`
          const res = await fetch(url)
          const data = await res.json()
          
          if (data.success && data.data) {
            const nearestNode = data.data
            if (target === 'start') {
              startId.value = nearestNode.node_id
            }
            
            showToast(`最近位置: ${nearestNode.name}`, 'success')
            
            if (map && window.AMap) {
              const AMap = window.AMap
              
              const currentMarker = new AMap.Marker({
                position: [lng, lat],
                content: '<div style="background:#33ccff;color:white;padding:8px 12px;border-radius:50%;font-size:14px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.2);">📍</div>',
                offset: new AMap.Pixel(-15, -15)
              })
              
              map.add(currentMarker)
              markers.push(currentMarker)
              
              map.setCenter([lng, lat])
              map.setZoom(17)
            }
          } else {
            showToast('未找到附近的导航节点', 'warning')
          }
        } catch (e) {
          console.error('查找最近节点失败:', e)
        }
      } else {
        locationStatus.value = ''
        showToast('高德定位失败，尝试浏览器定位...', 'warning')
        locateWithBrowser(target)
      }
    })
  } else {
    locateWithBrowser(target)
  }
}

function locateWithBrowser(target) {
  locationStatus.value = '获取位置中...'
  
  if (!navigator.geolocation) {
    showToast('您的浏览器不支持地理定位', 'error')
    locationStatus.value = ''
    return
  }

  if (!window.isSecureContext && window.location.protocol !== 'http:') {
    showToast('定位功能在HTTPS环境下更稳定', 'warning')
  }

  const options = {
    enableHighAccuracy: true,
    timeout: 15000,
    maximumAge: 0
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      let lng = position.coords.longitude
      let lat = position.coords.latitude
      
      const [gcjLng, gcjLat] = wgs84ToGcj02(lng, lat)
      
      currentLocation.value = { lng: gcjLng, lat: gcjLat }
      locationStatus.value = '定位成功！'
      
      showToast('已获取当前位置', 'success')
      
      try {
        const url = `${API_BASE}/api/nav/nearest-node?lng=${gcjLng}&lat=${gcjLat}`
        const res = await fetch(url)
        const data = await res.json()
        
        if (data.success && data.data) {
          const nearestNode = data.data
          if (target === 'start') {
            startId.value = nearestNode.node_id
          }
          
          showToast(`最近位置: ${nearestNode.name}`, 'success')
          
          if (map && window.AMap) {
            const AMap = window.AMap
            
            const currentMarker = new AMap.Marker({
              position: [gcjLng, gcjLat],
              content: '<div style="background:#33ccff;color:white;padding:8px 12px;border-radius:50%;font-size:14px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.2);">📍</div>',
              offset: new AMap.Pixel(-15, -15)
            })
            
            map.add(currentMarker)
            markers.push(currentMarker)
            
            map.setCenter([gcjLng, gcjLat])
            map.setZoom(17)
          }
        } else {
          showToast('未找到附近的导航节点', 'warning')
        }
      } catch (e) {
        console.error('查找最近节点失败:', e)
      }
    },
    (error) => {
      let errorMsg = ''
      switch(error.code) {
        case error.PERMISSION_DENIED:
          errorMsg = '请允许浏览器获取您的位置权限'
          break
        case error.POSITION_UNAVAILABLE:
          errorMsg = '位置信息不可用，请检查GPS是否开启'
          break
        case error.TIMEOUT:
          errorMsg = '获取位置超时，请重试'
          break
        default:
          errorMsg = '获取位置失败: ' + error.message
      }
      showToast(errorMsg, 'error')
      locationStatus.value = ''
    },
    options
  )
}

function isMobileDevice() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

function openAMapNavigation() {
  const startCoord = getNodeCoord(startId.value)
  const endCoord = getNodeCoord(endId.value)
  
  if (!startCoord || !endCoord) {
    showToast('坐标数据错误！', 'error')
    return
  }
  
  const startName = encodeURIComponent(getNodeName(startId.value) || '起点')
  const endName = encodeURIComponent(getNodeName(endId.value) || '终点')
  
  let url
  if (isMobileDevice()) {
    url = `amapuri://route/plan/?dlat=${endCoord[1]}&dlon=${endCoord[0]}&dname=${endName}&t=0`
  } else {
    url = `https://uri.amap.com/navigation?from=${startCoord[0]},${startCoord[1]},${startName}&to=${endCoord[0]},${endCoord[1]},${endName}&mode=walk`
  }
  
  const startTime = Date.now()
  const link = document.createElement('a')
  link.href = url
  link.click()
  
  setTimeout(() => {
    if (Date.now() - startTime < 2000) {
      window.location.href = `https://uri.amap.com/navigation?from=${startCoord[0]},${startCoord[1]},${startName}&to=${endCoord[0]},${endCoord[1]},${endName}&mode=walk`
    }
  }, 1000)
}

onMounted(async () => {
  await loadNodes()
  await initMap()
})

onUnmounted(() => {
  clearMapPath()
})
</script>

<style scoped>
.navigation-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.header {
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: white;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.header h1 {
  margin: 0;
  font-size: 20px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.control-panel {
  width: 320px;
  background: white;
  padding: 20px;
  overflow-y: auto;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.section {
  margin-bottom: 15px;
}

.section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.section select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
}

.input-group {
  display: flex;
  gap: 8px;
}

.input-group select {
  flex: 1;
}

.locate-btn {
  padding: 10px 18px;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border: 2px solid white;
  border-radius: 50px;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
  font-weight: bold;
}

.locate-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 16px rgba(40, 167, 69, 0.5);
  background: linear-gradient(135deg, #20c997 0%, #28a745 100%);
}

.locate-btn:active {
  transform: translateY(0) scale(0.98);
}

.location-status {
  margin-top: 8px;
}

.status-text {
  font-size: 12px;
  color: #28a745;
  font-weight: 500;
}

.swap-btn {
  text-align: center;
  padding: 10px;
  cursor: pointer;
  font-size: 24px;
  margin: 10px 0;
  transition: transform 0.3s;
}

.swap-btn:hover {
  transform: rotate(180deg);
}

.calc-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #33ccff 0%, #0099cc 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 10px;
  transition: all 0.3s;
}

.calc-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(51, 204, 255, 0.4);
}

.calc-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.result-panel {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #33ccff;
}

.distance {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.time {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.path-steps {
  max-height: 300px;
  overflow-y: auto;
}

.step {
  padding: 8px 0;
  border-bottom: 1px dashed #eee;
  font-size: 13px;
  color: #555;
}

.step:last-child {
  border-bottom: none;
}

.clear-btn {
  width: 100%;
  padding: 10px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 15px;
  transition: all 0.3s;
}

.clear-btn:hover {
  background: #5a6268;
}

.nav-buttons {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.nav-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.nav-btn-amap {
  background: linear-gradient(135deg, #00b4d8 0%, #0096c7 100%);
  color: white;
}

.nav-btn-amap:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4);
}

.map-container {
  flex: 1;
  position: relative;
  background: #e9ecef;
}

.map-container .loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.map-container .spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #33ccff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }

  .control-panel {
    width: 100%;
    max-height: 40vh;
  }

  .map-container {
    height: 60vh;
  }
}
</style>