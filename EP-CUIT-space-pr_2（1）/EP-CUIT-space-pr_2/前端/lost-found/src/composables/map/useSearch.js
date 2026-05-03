import { ref } from 'vue'

export function useSearch(markers, getMap, renderMarkers, highlightId) {
    const searchInput = ref('')
    const status = ref('')

    const search = () => {
        const key = searchInput.value.toLowerCase()

        const hit = markers.value.find(m =>
            (m.title + m.detail).toLowerCase().includes(key)
        )

        if (!hit) {
            status.value = "未找到"
            return
        }

        highlightId.value = hit.id

        const map = getMap()
        map.setCenter([hit.lng, hit.lat])

        renderMarkers()
    }

    return {
        searchInput,
        search,
        status
    }
}