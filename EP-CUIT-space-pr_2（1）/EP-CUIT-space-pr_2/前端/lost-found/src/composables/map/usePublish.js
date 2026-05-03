import { ref } from 'vue'

export function usePublish(loadMarkers) {
    const pubTitle = ref('')
    const pubDetail = ref('')
    const pubPhone = ref('')
    const pubLng = ref(null)
    const pubLat = ref(null)

    const openPublish = (lng, lat) => {
        pubLng.value = lng
        pubLat.value = lat
    }

    const submitPublish = async () => {
        if (!pubTitle.value) {
            alert("标题不能为空")
            return
        }

        try {
            const res = await fetch("http://127.0.0.1:5000/map/add", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    title: pubTitle.value,
                    description: pubDetail.value,
                    phone: pubPhone.value,
                    lng: pubLng.value,
                    lat: pubLat.value
                })
            })

            const data = await res.json()

            if (data.success) {
                alert("发布成功")
                loadMarkers()
            }

        } catch (e) {
            console.log("发布失败", e)
        }
    }

    return {
        pubTitle,
        pubDetail,
        pubPhone,
        openPublish,
        submitPublish
    }
}