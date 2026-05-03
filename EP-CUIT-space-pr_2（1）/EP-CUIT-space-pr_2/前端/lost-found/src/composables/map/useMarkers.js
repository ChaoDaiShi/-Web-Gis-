import { ref } from 'vue'

export function useMarkers(getMap) {
    const markers = ref([])
    let markerObjs = []
    const highlightId = ref(null)

    const loadMarkers = async () => {
        try {
            const res = await fetch("http://127.0.0.1:5000/map/markers")
            const data = await res.json()

            if (!data.success) return

            markers.value = data.data.map(item => ({
                id: item.item_id,
                title: item.title,
                detail: item.description,
                lng: Number(item.lng),
                lat: Number(item.lat),
                time: item.create_time
            }))

            renderMarkers()

        } catch (e) {
            console.log("标记加载失败", e)
        }
    }

    const renderMarkers = () => {
        const map = getMap()
        if (!map) return

        markerObjs.forEach(m => m.setMap(null))
        markerObjs = []

        markers.value.forEach((m) => {
            if (!m.lng || !m.lat) return

            const marker = new AMap.Marker({
                position: [m.lng, m.lat],
                map: map,
                title: m.title
            })

            marker.on("click", () => {
                highlightId.value = m.id
                renderMarkers()
            })

            markerObjs.push(marker)
        })
    }

    return {
        markers,
        highlightId,
        loadMarkers,
        renderMarkers
    }
}