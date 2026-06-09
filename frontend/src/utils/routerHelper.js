import router from '../router'

export function navigateTo(path) {
  try {
    if (router && typeof router.push === 'function') {
      router.push(path)
    } else {
      console.warn('Router not available, navigating via window.location')
      window.location.href = path
    }
  } catch (e) {
    console.error('Navigation failed:', e)
    window.location.href = path
  }
}

export function goBack(fallbackPath = '/home') {
  try {
    if (router && typeof router.back === 'function') {
      router.back()
    } else {
      window.location.href = fallbackPath
    }
  } catch (e) {
    console.error('Go back failed:', e)
    window.location.href = fallbackPath
  }
}

export default {
  navigateTo,
  goBack
}
