import { createApp } from 'vue';

const app = createApp({});
export const eventBus = app.config.globalProperties.$bus = {
  on(event, callback) {
    document.addEventListener(event, (e) => callback(e.detail));
  },
  emit(event, data) {
    document.dispatchEvent(new CustomEvent(event, { detail: data }));
  },
  off(event, callback) {
    document.removeEventListener(event, callback);
  }
};

export default eventBus;