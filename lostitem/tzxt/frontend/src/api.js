import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export const notificationAPI = {
  getNotifications(userId, unreadOnly = false) {
    return api.get('/notifications/', {
      params: { user_id: userId, unread_only: unreadOnly }
    })
  },

  markAsRead(notificationId) {
    return api.put(`/notifications/${notificationId}/read`)
  },

  markAllAsRead(userId) {
    return api.put('/notifications/read-all', {}, {
      params: { user_id: userId }
    })
  }
}

export const lostItemAPI = {
  create(data) {
    return api.post('/lost-items/', data)
  },

  getAll(status, category) {
    return api.get('/lost-items/', {
      params: { status, category }
    })
  },

  getOne(itemId) {
    return api.get(`/lost-items/${itemId}`)
  },

  update(itemId, data) {
    return api.put(`/lost-items/${itemId}`, data)
  },

  delete(itemId) {
    return api.delete(`/lost-items/${itemId}`)
  }
}

export const claimAPI = {
  create(data) {
    return api.post('/claims/', data)
  },

  approve(claimId) {
    return api.put(`/claims/${claimId}/approve`)
  },

  reject(claimId) {
    return api.put(`/claims/${claimId}/reject`)
  },

  getByLostItem(lostItemId) {
    return api.get(`/claims/lost-item/${lostItemId}`)
  },

  getByUser(userId) {
    return api.get(`/claims/user/${userId}`)
  }
}

export default api