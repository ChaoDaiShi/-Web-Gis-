import { ref } from 'vue'

export function useMap() {
    let map = null

    const initMap = (config, onMapClick) => {
        map = new AMap.Map("mapContainer", {
            zoom: config.zoom || 18,
            center: [config.center_lng, config.center_lat],
            viewMode: "3D",
            pitch: 45
        })

        // 限制范围
        const bounds = new AMap.Bounds(
            [config.sw_lng, config.sw_lat],
            [config.ne_lng, config.ne_lat]
        )
        map.setBounds(bounds)
        map.setZooms([16, 20])

        // 点击地图
        map.on("click", (e) => {
            if (onMapClick) {
                onMapClick(e.lnglat.lng, e.lnglat.lat)
            }
        })
    }

    const getMap = () => map

    return {
        initMap,
        getMap
    }
}