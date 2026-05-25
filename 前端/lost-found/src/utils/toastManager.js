// Toast 管理器
class ToastManager {
  constructor() {
    this.toastQueue = []
    this.currentToast = null
    this.onToastUpdate = null
  }

  show(message, type = 'info') {
    this.toastQueue.push({ message, type, id: Date.now() })
    this.processQueue()
  }

  processQueue() {
    if (this.currentToast || this.toastQueue.length === 0) return
    this.currentToast = this.toastQueue.shift()
    if (this.onToastUpdate) {
      this.onToastUpdate(this.currentToast)
    }
  }

  close() {
    this.currentToast = null
    if (this.onToastUpdate) {
      this.onToastUpdate(null)
    }
    setTimeout(() => this.processQueue(), 100)
  }

  setOnToastUpdate(callback) {
    this.onToastUpdate = callback
  }
}

const toastManager = new ToastManager()

export default toastManager
