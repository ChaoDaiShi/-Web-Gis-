<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  visible: Boolean,
  title: { type: String, default: '编辑记录' },
  subtitle: { type: String, default: '' },
  fields: { type: Array, default: () => [] },
  readonly: Boolean,
  saving: Boolean
})

const emit = defineEmits(['update:visible', 'save', 'cancel'])

const form = ref({})

watch(
  () => [props.visible, props.fields],
  () => {
    if (!props.visible) return
    const next = {}
    for (const f of props.fields) {
      const v = f.value
      next[f.key] = v === null || v === undefined ? '' : String(v)
    }
    form.value = next
  },
  { deep: true, immediate: true }
)

const groupedFields = computed(() => props.fields)

function close() {
  emit('update:visible', false)
  emit('cancel')
}

function submit() {
  const payload = {}
  for (const f of props.fields) {
    if (f.readonly) continue
    let val = form.value[f.key]
    if (f.type === 'number') {
      val = val === '' ? null : Number(val)
    } else if (f.type === 'json') {
      try {
        val = val === '' ? null : JSON.parse(val)
      } catch {
        return alert('JSON 格式不正确')
      }
    } else if (val === '') {
      val = null
    }
    payload[f.key] = val
  }
  emit('save', payload)
}

function onOverlayClick(e) {
  if (e.target === e.currentTarget) close()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="record-editor-overlay" @click="onOverlayClick">
      <div class="record-editor" @click.stop>
        <header class="re-header">
          <div>
            <h3>{{ title }}</h3>
            <p v-if="subtitle" class="re-sub">{{ subtitle }}</p>
          </div>
          <button type="button" class="re-close" @click="close">&times;</button>
        </header>

        <div class="re-toolbar">
          <span class="re-hint">字段</span>
          <span class="re-hint">值</span>
        </div>

        <div class="re-body">
          <div v-for="f in groupedFields" :key="f.key" class="re-row" :class="{ readonly: f.readonly }">
            <label class="re-field">
              <span class="re-key">{{ f.key }}</span>
              <span v-if="f.type" class="re-type">{{ f.type }}</span>
            </label>
            <div class="re-value">
              <input
                v-if="!f.readonly && (f.type === 'text' || f.type === 'number')"
                v-model="form[f.key]"
                :type="f.type === 'number' ? 'number' : 'text'"
                class="re-input"
              />
              <textarea
                v-else-if="!f.readonly && (f.type === 'textarea' || f.type === 'json')"
                v-model="form[f.key]"
                class="re-textarea"
                :rows="f.type === 'json' ? 6 : 3"
              />
              <span v-else class="re-readonly">{{ form[f.key] || '—' }}</span>
            </div>
          </div>
        </div>

        <footer class="re-footer">
          <button type="button" class="btn-cancel" @click="close">取消</button>
          <button
            v-if="!readonly"
            type="button"
            class="btn-save"
            :disabled="saving"
            @click="submit"
          >
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.record-editor-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.record-editor {
  width: min(820px, 100%);
  max-height: 85vh;
  background: #ffffff;
  color: #111111;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  border: 1px solid #d9d9d9;
}
.re-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 22px 26px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
  border-radius: 12px 12px 0 0;
}
.re-header h3 { margin: 0; font-size: 22px; color: #096dd9; font-weight: 700; }
.re-sub { margin: 6px 0 0; font-size: 15px; color: #666; }
.re-close {
  background: none;
  border: none;
  color: #666;
  font-size: 32px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
}
.re-close:hover { color: #333; }
.re-toolbar {
  display: grid;
  grid-template-columns: 220px 1fr;
  padding: 14px 26px;
  font-size: 13px;
  color: #666;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}
.re-body {
  overflow-y: auto;
  flex: 1;
  padding: 0;
}
.re-row {
  display: grid;
  grid-template-columns: 220px 1fr;
  border-bottom: 1px solid #f0f0f0;
  min-height: 64px;
  align-items: stretch;
}
.re-row:hover { background: #f5f5f5; }
.re-row.readonly { opacity: 0.85; }
.re-field {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px 20px;
  background: #fafafa;
  border-right: 1px solid #e8e8e8;
  gap: 4px;
}
.re-key { font-size: 17px; color: #096dd9; font-weight: 600; }
.re-type { font-size: 13px; color: #888; font-weight: 500; }
.re-value {
  padding: 14px 20px;
  display: flex;
  align-items: center;
}
.re-input,
.re-textarea {
  width: 100%;
  background: #fff;
  border: 2px solid #d9d9d9;
  border-radius: 8px;
  color: #111;
  padding: 12px 16px;
  font-size: 17px;
  font-family: inherit;
  font-weight: 500;
  transition: border-color 0.2s;
}
.re-input:focus,
.re-textarea:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.15);
}
.re-readonly {
  font-size: 17px;
  color: #333;
  font-weight: 500;
  word-break: break-all;
}
.re-footer {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  padding: 20px 26px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
  border-radius: 0 0 12px 12px;
}
.btn-cancel {
  padding: 12px 28px;
  background: #fff;
  color: #333;
  border: 2px solid #d9d9d9;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.2s;
}
.btn-cancel:hover {
  background: #f5f5f5;
  border-color: #b3b3b3;
}
.btn-save {
  padding: 12px 28px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.2s;
}
.btn-save:hover {
  background: #40a9ff;
}
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
