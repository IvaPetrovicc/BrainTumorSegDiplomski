<template>
  <div class="card">
    <div class="header">
      <div>
        <h2>Učitavanje MRI snimke</h2>
      </div>
    </div>

    <form class="form" @submit.prevent="sendImage">
      <div class="upload-panel">
        <div class="brain-icon">🧠</div>
        <div class="upload-row">
          <label class="file-input">
            <input type="file" accept="image/*" @change="onFileChange" :disabled="isPredicting" />
            <small class="file-name" :class="{ empty: !fileName }">{{ fileName || "placeholder" }}</small>
          </label>
          <button type="submit" class="primary-btn" :disabled="!canPredict">
            <span v-if="isPredicting" class="spinner"></span>
            {{ isPredicting ? 'Analiza...' : 'Pokreni segmentaciju' }}
          </button>
        </div>
        <span class="status-text">{{ status }}</span>
      </div>
    </form>

    <p v-if="error" class="error">
      <span class="error-icon">⚠️</span>
      {{ error }}
    </p>

    <div v-if="previewSrc">
      <div class="section-header">
        <span class="section-icon">📸</span>
        <h3 class="section-title">Pregled snimke</h3>
      </div>
      <div class="preview-grid">
        <div class="preview-card">
          <div class="preview-header">
            <h3>Originalna snimka</h3>
            <span class="chip">Učitano</span>
          </div>
          <img :src="previewSrc" alt="Pregled učitane slike" loading="lazy" />
        </div>
        <div class="preview-card" v-if="overlaySrc">
          <div class="preview-header">
            <h3>Segmentacijski prikaz</h3>
            <span class="chip success">Segmentacija</span>
          </div>
          <img :src="overlaySrc" alt="Preklapanje predikcije" loading="lazy" />
        </div>
        <div class="preview-card" v-else-if="prediction">
          <div class="preview-header">
            <h3>Bez segmentacije</h3>
            <span class="chip muted">Bez maske</span>
          </div>
          <p class="muted">Model nije vratio masku ili okvir za prikaz.</p>
        </div>
      </div>
    </div>

    <div v-if="prediction">
      <div class="section-header">
        <span class="section-icon">📋</span>
        <h3 class="section-title">Dijagnostički rezultati</h3>
      </div>
      <div class="result">
        <div class="meta">
          <div class="meta-item">
            <div class="meta-label">Datoteka</div>
            <div class="meta-value">{{ prediction.filename }}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Model</div>
            <div class="meta-value">{{ prediction.model_used }}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Tumor detektiran</div>
            <div class="meta-value">
              <span :class="prediction.has_tumor ? 'flag-critical' : 'flag-good'">
                {{ prediction.has_tumor ? '⚠️ Da' : '✓ Ne' }}
              </span>
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Pouzdanost</div>
            <div class="meta-value">{{ prediction.confidence.toFixed(3) }}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Pragovi detekcije</div>
            <div class="meta-value thresholds">
              conf {{ prediction.conf_th }}, iou {{ prediction.iou_th }}, min area {{ prediction.min_mask_area }}
            </div>
          </div>
        </div>
        <p v-if="prediction.description" class="description">{{ prediction.description }}</p>
      </div>
      <div class="report-actions">
        <button type="button" class="secondary-btn" :disabled="isReporting" @click="downloadReport">
          <span v-if="isReporting" class="spinner"></span>
          {{ isReporting ? 'Izrada izvještaja...' : 'Preuzmi medicinski izvještaj' }}
        </button>
        <span class="status-text">{{ reportStatus }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' }
})

const file = ref(null)
const previewSrc = ref('')
const isPredicting = ref(false)
const prediction = ref(null)
const error = ref('')
const status = ref('')
const isReporting = ref(false)
const reportStatus = ref('')

const fileName = computed(() => file.value?.name ?? '')
const overlaySrc = computed(() => prediction.value?.overlay_image ?? '')
const canPredict = computed(() => file.value && !isPredicting.value)

function revokePreview() {
  if (previewSrc.value && previewSrc.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewSrc.value)
  }
}

function onFileChange(e) {
  revokePreview()
  file.value = e.target.files?.[0] ?? null
  previewSrc.value = file.value ? URL.createObjectURL(file.value) : ''
  error.value = ''
  prediction.value = null
}

async function sendImage() {
  error.value = ''
  prediction.value = null

  if (!file.value) {
    status.value = 'Učitajte sliku za pokretanje segmentacije.'
    error.value = 'Najprije odaberite sliku.'
    return
  }

  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('model_choice', 'custom')

  isPredicting.value = true
  status.value = 'Slanje slike na backend...'
  
  try {
    const { data } = await api.post('/predict', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    
    prediction.value = {
      filename: data.filename ?? file.value.name,
      model_used: data.model_used ?? 'custom',
      conf_th: Number(data.conf_th ?? 0),
      iou_th: Number(data.iou_th ?? 0),
      min_mask_area: Number(data.min_mask_area ?? 0),
      has_tumor: Boolean(data.has_tumor),
      confidence: Number(data.confidence ?? 0),
      description: data.description ?? '',
      overlay_image: data.overlay_image ?? '',
    }
    
    status.value = 'Segmentacija završena.'
  } catch (e) {
    const detail = e.response?.data?.detail ?? e.message
    error.value = detail
    status.value = 'Segmentacija nije uspjela.'
  } finally {
    isPredicting.value = false
  }
}

function fileToDataUrl(fileObj) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = (err) => reject(err)
    reader.readAsDataURL(fileObj)
  })
}

async function downloadReport() {
  if (!prediction.value || !file.value) {
    reportStatus.value = 'Nema predikcije za izvještaj.'
    return
  }

  isReporting.value = true
  reportStatus.value = 'Generiranje PDF izvještaja...'
  
  try {
    const original = await fileToDataUrl(file.value)
    const payload = {
      filename: prediction.value.filename || file.value.name,
      model_used: prediction.value.model_used || 'custom',
      conf_th: Number(prediction.value.conf_th ?? 0),
      iou_th: Number(prediction.value.iou_th ?? 0),
      min_mask_area: Number(prediction.value.min_mask_area ?? 0),
      has_tumor: Boolean(prediction.value.has_tumor),
      confidence: Number(prediction.value.confidence ?? 0),
      description: prediction.value.description ?? '',
      image_original: original,
      image_overlay: prediction.value.overlay_image || null,
    }

    const res = await api.post('/report', payload, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `izvjestaj_${payload.filename || 'predikcija'}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    reportStatus.value = 'Izvještaj preuzet.'
  } catch (e) {
    const detail = e.response?.data?.detail ?? e.message
    reportStatus.value = `Greška: ${detail}`
  } finally {
    isReporting.value = false
  }
}
</script>

<style scoped>
.card {
  background: rgba(18, 18, 18, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(99, 102, 241, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.03);
  position: relative;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(99, 102, 241, 0.8) 30%, 
    rgba(139, 92, 246, 0.8) 70%,
    transparent 100%);
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 48px 48px 40px;
  border-bottom: 1px solid rgba(99, 102, 241, 0.15);
  flex-wrap: wrap;
}

.eyebrow {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #6366f1;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.eyebrow::before {
  content: '';
  width: 32px;
  height: 1px;
  background: linear-gradient(90deg, #6366f1, transparent);
}

h2 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
  letter-spacing: -2px;
  line-height: 1.2;
}

.subhead {
  margin: 0;
  font-size: 15px;
  color: #a1a1aa;
  font-weight: 400;
  line-height: 1.6;
}

.badge {
  padding: 10px 24px;
  border-radius: 100px;
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  border: 1px solid rgba(99, 102, 241, 0.3);
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6366f1;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.badge.active {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
  color: #a78bfa;
  box-shadow: 0 0 24px rgba(139, 92, 246, 0.3);
}

.badge.active .pulse-dot {
  background: #a78bfa;
  animation: pulse-bright 1s infinite;
}

@keyframes pulse-bright {
  0%, 100% { 
    opacity: 1; 
    box-shadow: 0 0 10px #a78bfa; 
  }
  50% { 
    opacity: 0.6; 
    box-shadow: 0 0 4px #a78bfa; 
  }
}

.form {
  padding: 48px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.upload-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.upload-row {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  flex-wrap: wrap;
  justify-content: center;
}

.file-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-input input[type="file"] {
  background: rgba(10, 10, 10, 0.8);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: #e5e5e5;
  padding: 10px 14px;
  height: 48px;
  border-radius: 10px;
  font-size: 13px;
  font-family: 'Inter', sans-serif;
  width: 320px;
}

.file-input input[type="file"]::file-selector-button {
  padding: 8px 14px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 8px;
  color: #c7d2fe;
  font-weight: 600;
  font-size: 11px;
  cursor: pointer;
  margin-right: 12px;
  font-family: 'Inter', sans-serif;
}

.file-input input[type="file"]::file-selector-button:hover {
  background: rgba(99, 102, 241, 0.25);
  border-color: #6366f1;
}

.file-input small {
  color: #6366f1;
  font-weight: 500;
  font-size: 12px;
  font-family: 'Fira Code', monospace;
  text-align: center;
}

.file-name {
  min-height: 16px;
  max-width: 320px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-name.empty {
  visibility: hidden;
}

.brain-icon {
  font-size: 72px;
  filter: drop-shadow(0 8px 24px rgba(99, 102, 241, 0.4));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

.actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.primary-btn {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
  border: 1px solid rgba(99, 102, 241, 0.5);
  height: 48px;
  padding: 0 18px;
  border-radius: 10px;
  font-weight: 700;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 0.3px;
  text-transform: uppercase;
  box-shadow: 
    0 12px 32px rgba(99, 102, 241, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.primary-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.primary-btn:hover:not(:disabled)::before {
  left: 100%;
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(0.3);
}

.primary-btn:not(:disabled):hover {
  transform: translateY(-3px);
  box-shadow: 
    0 18px 48px rgba(99, 102, 241, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.secondary-btn {
  background: rgba(99, 102, 241, 0.12);
  color: #c7d2fe;
  border: 1px solid rgba(99, 102, 241, 0.4);
  height: 48px;
  padding: 0 28px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 0.3px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.secondary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary-btn:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.2);
  border-color: #6366f1;
  transform: translateY(-2px);
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-text {
  color: #a1a1aa;
  font-size: 14px;
  font-style: italic;
  text-align: center;
}

.report-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin: 0 48px 48px;
}

.error {
  margin: 0 48px 32px;
  padding: 20px 24px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-left: 4px solid #ef4444;
  border-radius: 12px;
  color: #fca5a5;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.error-icon {
  font-size: 22px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 48px 48px 28px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(99, 102, 241, 0.2);
}

.section-icon {
  font-size: 28px;
  filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.5));
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -1px;
  margin: 0;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 24px;
  padding: 0 48px 48px;
}

.preview-card {
  background: rgba(10, 10, 10, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.4s ease;
}

.preview-card:hover {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
  transform: translateY(-6px);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.preview-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.preview-card img {
  width: 100%;
  height: auto;
  border-radius: 12px;
  display: block;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.muted {
  color: #52525b;
  text-align: center;
  padding: 60px 24px;
  font-size: 14px;
  margin: 0;
  line-height: 1.6;
}

.chip {
  padding: 7px 14px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #6366f1;
  background: rgba(99, 102, 241, 0.15);
}

.chip.success {
  border-color: rgba(34, 197, 94, 0.4);
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
}

.chip.muted {
  color: #71717a;
  border-color: rgba(113, 113, 122, 0.25);
  background: rgba(113, 113, 122, 0.15);
}

.result {
  background: rgba(10, 10, 10, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 16px;
  padding: 36px;
  margin: 0 48px 40px;
}

.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 28px;
}

.meta-item {
  padding: 18px;
  background: rgba(99, 102, 241, 0.05);
  border-left: 3px solid #6366f1;
  border-radius: 8px;
}

.meta-label {
  font-size: 11px;
  font-weight: 600;
  color: #a1a1aa;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.meta-value {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  font-family: 'Fira Code', monospace;
}

.thresholds {
  font-size: 13px !important;
}

.flag-good,
.flag-critical {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  border-radius: 8px;
  border: 1px solid;
  margin-top: 6px;
}

.flag-good {
  border-color: rgba(34, 197, 94, 0.4);
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  box-shadow: 0 0 24px rgba(34, 197, 94, 0.2);
}

.flag-critical {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
  box-shadow: 0 0 24px rgba(239, 68, 68, 0.2);
}

.description {
  margin: 0;
  padding: 24px;
  background: rgba(99, 102, 241, 0.05);
  border-left: 4px solid #6366f1;
  border-radius: 10px;
  color: #d4d4d8;
  font-size: 15px;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .header {
    padding: 32px 24px 28px;
    flex-direction: column;
    align-items: flex-start;
  }

  h2 {
    font-size: 28px;
  }

  .form {
    padding: 32px 24px;
  }

  .brain-icon {
    font-size: 72px;
  }

  .upload-row {
    flex-direction: column;
    width: 100%;
  }

  .file-input input[type="file"] {
    width: 100%;
  }

  .section-header {
    margin: 32px 24px 20px;
  }

  .preview-grid {
    grid-template-columns: 1fr;
    padding: 0 24px 32px;
  }

  .result {
    margin: 0 24px 32px;
    padding: 24px;
  }

  .report-actions {
    margin: 0 24px 32px;
  }

  .meta {
    grid-template-columns: 1fr;
  }

  .error {
    margin: 0 24px 24px;
  }

  .primary-btn, .secondary-btn {
    width: 100%;
  }
}
</style>
