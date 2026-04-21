const avatarBtn = document.getElementById("avatarBtn");
const app = document.getElementById("app");
const listPanel = document.getElementById("listPanel");
const itemList = document.getElementById("itemList");
const mapPanel = document.getElementById("mapPanel");

const leftArrow = document.getElementById("leftArrow");
const rightArrow = document.getElementById("rightArrow");
const statusEl = document.getElementById("status");
const searchInput = document.getElementById("searchInput");

const publishMask = document.getElementById("publishMask");
const pubTitle = document.getElementById("pubTitle");
const pubDetail = document.getElementById("pubDetail");
const pubPhone = document.getElementById("pubPhone");
const pubCancel = document.getElementById("pubCancel");
const pubSubmit = document.getElementById("pubSubmit");

const detailMask = document.getElementById("detailMask");
const detailTitle = document.getElementById("detailTitle");
const detailBody = document.getElementById("detailBody");
const detailClose = document.getElementById("detailClose");

let is3D = true;
let mode = "normal";
let markers = [
    { id: "M001", lng: 103.988, lat: 30.582, title: "黑色水杯", detail: "图书馆拾取", phone: "13800001234", time: "2026-04-15 09:00" },
    { id: "M002", lng: 103.990, lat: 30.581, title: "校园卡", detail: "食堂门口", phone: "13900005678", time: "2026-04-15 11:20" },
    { id: "M003", lng: 103.986, lat: 30.583, title: "蓝牙耳机", detail: "教学楼A座", phone: "13600007890", time: "2026-04-15 13:08" }
];
let pendingWorldPoint = null;
let mapOffset = { x: -300, y: -180 };
let highlightId = "";
let map;
let markerObjs = [];

function initMap(config) {
    const campusBounds = [
        [config.sw_lng, config.sw_lat],
        [config.ne_lng, config.ne_lat]
    ];

    map = new AMap.Map("mapContainer", {
        zoom: config.zoom || 18,
        center: [config.center_lng, config.center_lat],
        viewMode: '3D',
        pitch: 45,
        rotation: 0
    });

    const campusPath = [
        [config.sw_lng, config.sw_lat],
        [config.ne_lng, config.sw_lat],
        [config.ne_lng, config.ne_lat],
        [config.sw_lng, config.ne_lat]
    ];

    const bounds = new AMap.Bounds(
        [config.sw_lng, config.sw_lat],
        [config.ne_lng, config.ne_lat]
    );

    map.setBounds(bounds);
    map.setZooms([16, 20]);

    map.on("click", function (e) {
        const { lng, lat } = e.lnglat;
        openPublishModal(lng, lat);
    });
}

function loadDefaultMap() {
    fetch("http://127.0.0.1:5000/map/default")
        .then(res => res.json())
        .then(config => {
            if (!config || config.error) {
                setStatus("地图加载失败");
                return;
            }
            initMap(config);
            renderAll();
        })
        .catch(() => {
            setStatus("无法连接后端");
        });
}

const toggleBtn = document.getElementById("toggle3D");

toggleBtn.addEventListener("click", () => {
    is3D = !is3D;

    if (is3D) {
        map.setPitch(45);
        map.setRotation(0);
        toggleBtn.innerText = "切换2D";
        setStatus("已切换3D视图");
    } else {
        map.setPitch(0);
        map.setRotation(0);
        toggleBtn.innerText = "切换3D";
        setStatus("已切换2D视图");
    }
});

function updateLeftArrowPosition() {
    const appRect = app.getBoundingClientRect();
    const listRect = listPanel.getBoundingClientRect();
    const relativeLeft = listRect.right - appRect.left - 14;
    leftArrow.style.left = `${Math.max(6, relativeLeft)}px`;
}

function setStatus(msg) { statusEl.textContent = msg; }

function centerToPoint(lng, lat) {
    map.setCenter([lng, lat]);
}

function switchMode(nextMode) {
    mode = nextMode;
    app.classList.remove("fullmap", "split");
    if (nextMode === "full") app.classList.add("fullmap");
    if (nextMode === "split") app.classList.add("split");

    if (nextMode === "full") {
        leftArrow.classList.add("hidden");
        rightArrow.classList.remove("hidden");
    } else {
        leftArrow.classList.remove("hidden");
        rightArrow.classList.add("hidden");
    }
    updateLeftArrowPosition();
    setTimeout(() => {
        map && map.resize();
    }, 300);

    map.setLayers([
        new AMap.TileLayer.Satellite(),
        new AMap.TileLayer.RoadNet()
    ]);

    map.setZooms([17, 22]);
}

function openPublishModal(lng, lat) {
    pendingWorldPoint = { lng, lat };
    pubTitle.value = "";
    pubDetail.value = "";
    pubPhone.value = "";
    publishMask.style.display = "flex";
}

function closePublishModal() {
    publishMask.style.display = "none";
}

function openDetail(marker) {
    detailTitle.textContent = marker.title;
    detailBody.innerHTML = `
        <div><strong>ID：</strong>${marker.id}</div>
        <div><strong>描述：</strong>${marker.detail}</div>
        <div><strong>联系方式：</strong>${marker.phone || "-"}</div>
        <div><strong>发布时间：</strong>${marker.time}</div>
    `;
    detailMask.style.display = "flex";
}

function closeDetail() {
    detailMask.style.display = "none";
}

function renderMarkers() {
    markerObjs.forEach(m => m.setMap(null));
    markerObjs = [];

    markers.forEach((m) => {
        if (
            m.lng === undefined || m.lat === undefined ||
            isNaN(m.lng) || isNaN(m.lat)
        ) {
            console.warn("无效坐标:", m);
            return;
        }

        const isHighlight = highlightId && highlightId === m.id;
        const marker = new AMap.Marker({
            position: [Number(m.lng), Number(m.lat)],
            map: map,
            title: m.title,
            offset: new AMap.Pixel(-17, -48),
            content: `
                <div class="marker-wrap ${isHighlight ? "highlight" : ""}">
                    <div class="marker-wave"></div>
                    <div class="marker-core"></div>
                    <div class="marker-label">${m.title}</div>
                </div>
            `
        });

        marker.on("click", () => {
            highlightId = m.id;
            openDetail(m);
        });

        markerObjs.push(marker);
    });
}

function renderList() {
    itemList.innerHTML = "";
    markers.forEach((m) => {
        const li = document.createElement("li");
        li.className = "item-card";
        li.innerHTML = `
            <div class="item-card-title">${m.title}</div>
            <div>ID: ${m.id}</div>
            <div class="item-card-detail">
                <div>描述：${m.detail}</div>
                <div>联系方式：${m.phone || "-"}</div>
                <div>发布时间：${m.time}</div>
            </div>
        `;
        li.addEventListener("click", () => {
            highlightId = m.id;
            centerToPoint(m.lng, m.lat);
            renderMarkers();
            setStatus(`已定位到：${m.title}`);
        });
        li.addEventListener("dblclick", (e) => {
            e.stopPropagation();
            li.classList.toggle("expanded");
        });
        itemList.appendChild(li);
    });
}

function renderAll() {
    renderMarkers();
    renderList();
    updateLeftArrowPosition();
}

avatarBtn.addEventListener("click", () => {
    window.location.href = "./个人中心.html";
});

leftArrow.addEventListener("click", () => {
    switchMode("full");
    setStatus("已切换全图模式");
});
rightArrow.addEventListener("click", () => {
    switchMode("normal");
    setStatus("已返回分栏模式");
});

listPanel.addEventListener("dblclick", (e) => {
    if (mode === "full") return;
    if (e.target.closest(".item-card")) return;
    switchMode(mode === "split" ? "normal" : "split");
    setStatus(mode === "split" ? "列表已展开（50/50）" : "已恢复普通分栏");
});


pubCancel.addEventListener("click", closePublishModal);
publishMask.addEventListener("click", (e) => { if (e.target === publishMask) closePublishModal(); });

pubSubmit.addEventListener("click", () => {
    if (!pendingWorldPoint) return;
    const title = pubTitle.value.trim();
    const detail = pubDetail.value.trim();
    if (!title || !detail) {
        setStatus("标题和描述不能为空");
        return;
    }
    const id = "M" + String(Date.now()).slice(-5);
    markers.push({
        id,
        lng: pendingWorldPoint.lng,
        lat: pendingWorldPoint.lat,
        title,
        detail,
        phone: pubPhone.value.trim(),
        time: new Date().toLocaleString("zh-CN", { hour12: false })
    });
    highlightId = id;
    renderAll();
    closePublishModal();
    setStatus("发布成功，已生成新标记并写入列表");
});

detailClose.addEventListener("click", closeDetail);
detailMask.addEventListener("click", (e) => { if (e.target === detailMask) closeDetail(); });

searchInput.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    const key = searchInput.value.trim().toLowerCase();
    if (!key) return;
    const hit = markers.find((m) => `${m.title} ${m.detail}`.toLowerCase().includes(key));
    if (!hit) {
        setStatus("未找到匹配标记");
        return;
    }
    highlightId = hit.id;
    centerToPoint(hit.lng, hit.lat);
    renderMarkers();
    setStatus(`已定位并高亮：${hit.title}`);
});

window.addEventListener("resize", () => {
    updateLeftArrowPosition();
});

new ResizeObserver(() => {
    updateLeftArrowPosition();
}).observe(listPanel);

loadDefaultMap();
switchMode("normal");
