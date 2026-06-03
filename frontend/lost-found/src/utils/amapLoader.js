import AMapLoader from '@amap/amap-jsapi-loader';

const AMAP_KEY = '49382949a3128467653e88aab0daa5c7';
const AMAP_SECURITY = '13aaa6de30599d02d3b3f1c562e9bd5e';
const LOAD_TIMEOUT = 25000;

let loadPromise = null;

export function loadAMap(options = {}) {
  if (window.AMap) {
    return Promise.resolve(window.AMap);
  }
  if (loadPromise) {
    return loadPromise;
  }

  window._AMapSecurityConfig = {
    securityJsCode: AMAP_SECURITY,
  };

  loadPromise = Promise.race([
    AMapLoader.load({
      key: AMAP_KEY,
      version: '2.0',
      plugins: options.plugins || [],
    }),
    new Promise((_, reject) => {
      setTimeout(() => reject(new Error('高德地图加载超时，请检查网络连接')), LOAD_TIMEOUT);
    }),
  ])
    .then((AMap) => {
      window.AMap = AMap;
      return AMap;
    })
    .catch((err) => {
      loadPromise = null;
      throw err;
    });

  return loadPromise;
}

export function resetAMapLoader() {
  loadPromise = null;
  delete window.AMap;
  document.querySelectorAll('script[src*="webapi.amap.com"]').forEach((el) => el.remove());
}
