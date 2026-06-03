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

// Confirm 对话框管理器
class ConfirmManager {
  constructor() {
    this._currentConfirm = null
    this.listeners = []
  }

  get currentConfirm() {
    return this._currentConfirm
  }

  set currentConfirm(value) {
    this._currentConfirm = value
    this.notifyListeners()
  }

  addListener(callback) {
    this.listeners.push(callback)
    return () => {
      const index = this.listeners.indexOf(callback)
      if (index > -1) {
        this.listeners.splice(index, 1)
      }
    }
  }

  notifyListeners() {
    this.listeners.forEach(callback => callback(this._currentConfirm))
  }

  show(options) {
    const {
      title = '确认操作',
      message = '确定要执行此操作吗？',
      confirmText = '确定',
      cancelText = '取消',
      type = 'warning'
    } = options

    return new Promise((resolve) => {
      this.currentConfirm = {
        visible: true,
        title,
        message,
        confirmText,
        cancelText,
        type,
        onConfirm: () => {
          this.currentConfirm = null
          resolve(true)
        },
        onCancel: () => {
          this.currentConfirm = null
          resolve(false)
        }
      }
    })
  }

  close() {
    this.currentConfirm = null
  }
}

const toastManager = new ToastManager()
const confirmManager = new ConfirmManager()

export default toastManager
export { confirmManager }