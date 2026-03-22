<template>
  <div class="settings-section">
    <h2>РЁСЂРёС„С‚С‹ Рё СЂР°Р·РјРµСЂ</h2>

    <div class="settings-group">
      <h3>рџ”¤ Р Р°Р·РјРµСЂ С‚РµРєСЃС‚Р°</h3>
      
      <div class="size-control">
        <span class="size-label small">РњРµР»РєРёР№</span>
        <input
          v-model="fontSize"
          type="range"
          min="12"
          max="22"
          step="1"
          class="size-slider"
        />
        <span class="size-label large">РљСЂСѓРїРЅС‹Р№</span>
        <span class="size-value">{{ fontSize }}px</span>
      </div>

      <div class="size-preview">
        <div class="preview-text" :style="{ fontSize: fontSize + 'px' }">
          РџСЂРёРјРµСЂ С‚РµРєСЃС‚Р° РґР»СЏ РїСЂРѕРІРµСЂРєРё СЂР°Р·РјРµСЂР° С€СЂРёС„С‚Р°. anisphere вЂ” Р»СѓС‡С€РёР№ СЃРµСЂРІРёСЃ РґР»СЏ Р»СЋР±РёС‚РµР»РµР№ Р°РЅРёРјРµ!
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ“Џ РњР°СЃС€С‚Р°Р± РёРЅС‚РµСЂС„РµР№СЃР°</h3>
      
      <div class="scale-control">
        <span class="scale-label">РЈРјРµРЅСЊС€РёС‚СЊ</span>
        <input
          v-model="interfaceScale"
          type="range"
          min="80"
          max="150"
          step="5"
          class="scale-slider"
        />
        <span class="scale-label">РЈРІРµР»РёС‡РёС‚СЊ</span>
        <span class="scale-value">{{ interfaceScale }}%</span>
      </div>

      <div class="scale-presets">
        <button
          v-for="preset in scalePresets"
          :key="preset"
          :class="['scale-preset', { active: interfaceScale === preset }]"
          @click="interfaceScale = preset"
        >
          {{ preset }}%
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџЋЁ РЁСЂРёС„С‚</h3>
      
      <div class="font-selector">
        <label class="font-option" :class="{ active: selectedFont === 'system' }">
          <input type="radio" v-model="selectedFont" value="system" />
          <span class="font-preview system">РЎРёСЃС‚РµРјРЅС‹Р№</span>
        </label>

        <label class="font-option" :class="{ active: selectedFont === 'Inter' }">
          <input type="radio" v-model="selectedFont" value="Inter" />
          <span class="font-preview inter" style="font-family: 'Inter', sans-serif;">Inter</span>
        </label>

        <label class="font-option" :class="{ active: selectedFont === 'Roboto' }">
          <input type="radio" v-model="selectedFont" value="Roboto" />
          <span class="font-preview roboto" style="font-family: 'Roboto', sans-serif;">Roboto</span>
        </label>

        <label class="font-option" :class="{ active: selectedFont === 'Open Sans' }">
          <input type="radio" v-model="selectedFont" value="Open Sans" />
          <span class="font-preview opensans" style="font-family: 'Open Sans', sans-serif;">Open Sans</span>
        </label>

        <label class="font-option" :class="{ active: selectedFont === 'Montserrat' }">
          <input type="radio" v-model="selectedFont" value="Montserrat" />
          <span class="font-preview montserrat" style="font-family: 'Montserrat', sans-serif;">Montserrat</span>
        </label>

        <label class="font-option" :class="{ active: selectedFont === 'anime' }">
          <input type="radio" v-model="selectedFont" value="anime" />
        </label>
      </div>

      <div class="font-sample" :style="{ fontFamily: getFontFamily(selectedFont) }">
        <p class="sample-title">РџСЂРёРјРµСЂ С‚РµРєСЃС‚Р°</p>
        <p class="sample-text">
          anisphere вЂ” СЌС‚Рѕ РїР»Р°С‚С„РѕСЂРјР° РґР»СЏ Р»СЋР±РёС‚РµР»РµР№ Р°РЅРёРјРµ, РіРґРµ РІС‹ РјРѕР¶РµС‚Рµ СЃРјРѕС‚СЂРµС‚СЊ, РѕР±СЃСѓР¶РґР°С‚СЊ Рё РґРµР»РёС‚СЊСЃСЏ СЃРІРѕРёРјРё Р»СЋР±РёРјС‹РјРё С‚РёС‚СѓР»Р°РјРё.
        </p>
        <p class="sample-subtitle">РџРѕРґР·Р°РіРѕР»РѕРІРѕРє H2</p>
        <p class="sample-body">
          РћР±С‹С‡РЅС‹Р№ С‚РµРєСЃС‚ РїР°СЂР°РіСЂР°С„Р° РґР»СЏ РїСЂРѕРІРµСЂРєРё С‡РёС‚Р°РµРјРѕСЃС‚Рё РІС‹Р±СЂР°РЅРЅРѕРіРѕ С€СЂРёС„С‚Р°. РҐРѕСЂРѕС€Рѕ С‡РёС‚Р°РµРјС‹Р№ С€СЂРёС„С‚ РІР°Р¶РµРЅ РґР»СЏ РєРѕРјС„РѕСЂС‚РЅРѕРіРѕ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ РїСЂРёР»РѕР¶РµРЅРёСЏ.
        </p>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ“ђ РџР»РѕС‚РЅРѕСЃС‚СЊ РёРЅС‚РµСЂС„РµР№СЃР°</h3>
      
      <div class="density-options">
        <label class="density-option" :class="{ active: density === 'compact' }">
          <input type="radio" v-model="density" value="compact" />
          <div class="density-preview compact">
            <div class="preview-line"></div>
            <div class="preview-line"></div>
            <div class="preview-line"></div>
          </div>
          <div class="density-info">
            <span class="density-name">РљРѕРјРїР°РєС‚РЅС‹Р№</span>
            <span class="density-desc">Р‘РѕР»СЊС€Рµ РєРѕРЅС‚РµРЅС‚Р° РЅР° СЌРєСЂР°РЅРµ</span>
          </div>
        </label>

        <label class="density-option" :class="{ active: density === 'comfortable' }">
          <input type="radio" v-model="density" value="comfortable" />
          <div class="density-preview comfortable">
            <div class="preview-line"></div>
            <div class="preview-line"></div>
            <div class="preview-line"></div>
          </div>
          <div class="density-info">
            <span class="density-name">РЈРґРѕР±РЅС‹Р№</span>
            <span class="density-desc">РџРѕ СѓРјРѕР»С‡Р°РЅРёСЋ</span>
          </div>
        </label>

        <label class="density-option" :class="{ active: density === 'spacious' }">
          <input type="radio" v-model="density" value="spacious" />
          <div class="density-preview spacious">
            <div class="preview-line"></div>
            <div class="preview-line"></div>
            <div class="preview-line"></div>
          </div>
          <div class="density-info">
            <span class="density-name">РџСЂРѕСЃС‚РѕСЂРЅС‹Р№</span>
            <span class="density-desc">Р›РµРіС‡Рµ С‡РёС‚Р°С‚СЊ</span>
          </div>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>вљ™пёЏ РЎРїРµС†РёР°Р»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё</h3>
      
      <div class="special-settings">
        <label class="setting-option">
          <input type="checkbox" v-model="boldHeadings" />
          <span class="setting-icon">H</span>
          <span class="setting-text">
            <span class="setting-name">Р–РёСЂРЅС‹Р№ С€СЂРёС„С‚ РґР»СЏ Р·Р°РіРѕР»РѕРІРєРѕРІ</span>
            <span class="setting-desc">Р’СЃРµ Р·Р°РіРѕР»РѕРІРєРё Р±СѓРґСѓС‚ Р¶РёСЂРЅС‹РјРё</span>
          </span>
        </label>

        <label class="setting-option">
          <input type="checkbox" v-model="increaseLineHeight" />
          <span class="setting-icon">В¶</span>
          <span class="setting-text">
            <span class="setting-name">РЈРІРµР»РёС‡РёС‚СЊ РјРµР¶СЃС‚СЂРѕС‡РЅС‹Р№ РёРЅС‚РµСЂРІР°Р»</span>
            <span class="setting-desc">РЈР»СѓС‡С€Р°РµС‚ С‡РёС‚Р°РµРјРѕСЃС‚СЊ РґР»РёРЅРЅС‹С… С‚РµРєСЃС‚РѕРІ</span>
          </span>
        </label>

        <label class="setting-option">
          <input type="checkbox" v-model="monospaceCode" />
          <span class="setting-icon">&lt;/&gt;</span>
          <span class="setting-text">
            <span class="setting-name">РњРѕРЅРѕС€РёСЂРёРЅРЅС‹Р№ С€СЂРёС„С‚ РґР»СЏ РєРѕРґР°</span>
            <span class="setting-desc">РљРѕРґ Р±СѓРґРµС‚ РѕС‚РѕР±СЂР°Р¶Р°С‚СЊСЃСЏ РјРѕРЅРѕС€РёСЂРёРЅРЅС‹Рј С€СЂРёС„С‚РѕРј</span>
          </span>
        </label>

        <label class="setting-option">
          <input type="checkbox" v-model="reduceMotion" />
          <span class="setting-icon">рџљ«</span>
          <span class="setting-text">
            <span class="setting-name">РЈРјРµРЅСЊС€РёС‚СЊ Р°РЅРёРјР°С†РёСЋ</span>
            <span class="setting-desc">РћС‚РєР»СЋС‡РёС‚СЊ РїР»Р°РІРЅС‹Рµ РїРµСЂРµС…РѕРґС‹ Рё Р°РЅРёРјР°С†РёРё</span>
          </span>
        </label>

        <label class="setting-option">
          <input type="checkbox" v-model="highContrastMode" />
          <span class="setting-icon">в—ђ</span>
          <span class="setting-text">
            <span class="setting-name">Р’С‹СЃРѕРєРёР№ РєРѕРЅС‚СЂР°СЃС‚</span>
            <span class="setting-desc">РЈР»СѓС‡С€Р°РµС‚ РІРёРґРёРјРѕСЃС‚СЊ РґР»СЏ СЃР»Р°Р±РѕРІРёРґСЏС‰РёС…</span>
          </span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ‘ЃпёЏ РџСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ</h3>
      
      <div class="preview-container" :style="previewStyle">
        <div class="preview-content">
          <h2 class="preview-heading">Р—Р°РіРѕР»РѕРІРѕРє H2</h2>
          <h3 class="preview-subheading">РџРѕРґР·Р°РіРѕР»РѕРІРѕРє H3</h3>
          <p class="preview-paragraph">
            Р­С‚Рѕ РїСЂРёРјРµСЂ РѕР±С‹С‡РЅРѕРіРѕ С‚РµРєСЃС‚Р°. anisphere вЂ” РѕС‚Р»РёС‡РЅС‹Р№ СЃРµСЂРІРёСЃ РґР»СЏ РїСЂРѕСЃРјРѕС‚СЂР° Р°РЅРёРјРµ РѕРЅР»Р°Р№РЅ.
            Р—РґРµСЃСЊ РІС‹ РјРѕР¶РµС‚Рµ РЅР°Р№С‚Рё РјРЅРѕР¶РµСЃС‚РІРѕ РёРЅС‚РµСЂРµСЃРЅС‹С… С‚Р°Р№С‚Р»РѕРІ Рё РѕР±СЃСѓРґРёС‚СЊ РёС… СЃ СЃРѕРѕР±С‰РµСЃС‚РІРѕРј.
          </p>
          <div class="preview-buttons">
            <button class="preview-btn primary">РћСЃРЅРѕРІРЅР°СЏ РєРЅРѕРїРєР°</button>
            <button class="preview-btn secondary">Р’С‚РѕСЂРёС‡РЅР°СЏ РєРЅРѕРїРєР°</button>
          </div>
          <div class="preview-list">
            <h4>РЎРїРёСЃРѕРє:</h4>
            <ul>
              <li>РџРµСЂРІС‹Р№ РїСѓРЅРєС‚ СЃРїРёСЃРєР°</li>
              <li>Р’С‚РѕСЂРѕР№ РїСѓРЅРєС‚ СЃРїРёСЃРєР°</li>
              <li>РўСЂРµС‚РёР№ РїСѓРЅРєС‚ СЃРїРёСЃРєР°</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="saveSettings" :disabled="!hasChanges" class="save-btn">
        рџ’ѕ РЎРѕС…СЂР°РЅРёС‚СЊ РЅР°СЃС‚СЂРѕР№РєРё
      </button>
      <button @click="resetToDefaults" class="reset-btn">
        в†» РЎР±СЂРѕСЃРёС‚СЊ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'
const { show: showToast } = useToast()
import { ref, computed, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'
import { useTheme } from '@/composables/useTheme'

const { applyFontSettings } = useTheme()

const fontSize = ref(14)
const interfaceScale = ref(100)
const selectedFont = ref('system')
const density = ref('comfortable')

const boldHeadings = ref(true)
const increaseLineHeight = ref(false)
const monospaceCode = ref(true)
const reduceMotion = ref(false)
const highContrastMode = ref(false)

const scalePresets = [80, 90, 100, 110, 125, 150]

const originalSettings = ref({})

const getFontFamily = (font: string) => {
  switch (font) {
    case 'Inter': return "'Inter', sans-serif"
    case 'Roboto': return "'Roboto', sans-serif"
    case 'Open Sans': return "'Open Sans', sans-serif"
    case 'Montserrat': return "'Montserrat', sans-serif"
    case 'anime': return "'Noto Sans JP', sans-serif"
    default: return 'system-ui, -apple-system, sans-serif'
  }
}

const previewStyle = computed(() => {
  return {
    fontSize: fontSize.value + 'px',
    fontFamily: getFontFamily(selectedFont.value),
    lineHeight: increaseLineHeight.value ? '1.8' : '1.5',
    filter: highContrastMode.value ? 'contrast(1.2)' : 'none'
  }
})

const hasChanges = computed(() => {
  const current = {
    fontSize: fontSize.value,
    interfaceScale: interfaceScale.value,
    selectedFont: selectedFont.value,
    density: density.value,
    boldHeadings: boldHeadings.value,
    increaseLineHeight: increaseLineHeight.value,
    monospaceCode: monospaceCode.value,
    reduceMotion: reduceMotion.value,
    highContrastMode: highContrastMode.value
  }
  return JSON.stringify(current) !== JSON.stringify(originalSettings.value)
})

const fetchFontSettings = async () => {
  try {
    const data = await settingsApi.getFontSettings()
    fontSize.value = data.font_size || 14
    interfaceScale.value = data.interface_scale || 100
    selectedFont.value = data.font_family || 'system'
    density.value = data.density || 'comfortable'
    boldHeadings.value = data.bold_headings ?? true
    increaseLineHeight.value = data.increase_line_height || false
    monospaceCode.value = data.monospace_code ?? true
    reduceMotion.value = data.reduce_motion || false
    highContrastMode.value = data.high_contrast_mode || false

    originalSettings.value = {
      fontSize: fontSize.value,
      interfaceScale: interfaceScale.value,
      selectedFont: selectedFont.value,
      density: density.value,
      boldHeadings: boldHeadings.value,
      increaseLineHeight: increaseLineHeight.value,
      monospaceCode: monospaceCode.value,
      reduceMotion: reduceMotion.value,
      highContrastMode: highContrastMode.value
    }

    // РџСЂРёРјРµРЅСЏРµРј РЅР°СЃС‚СЂРѕР№РєРё Рє РґРѕРєСѓРјРµРЅС‚Сѓ
    applyFontSettings(data)
  } catch (error) {
    console.error('Error fetching font settings:', error)
  }
}

const saveSettings = async () => {
  try {
    const data = {
      font_family: selectedFont.value,
      font_size: fontSize.value,
      interface_scale: interfaceScale.value,
      line_height: increaseLineHeight.value ? 1.8 : 1.5,
      density: density.value,
      bold_headings: boldHeadings.value,
      increase_line_height: increaseLineHeight.value,
      monospace_code: monospaceCode.value,
      reduce_motion: reduceMotion.value,
      high_contrast_mode: highContrastMode.value
    }

    await settingsApi.updateFontSettings(data)
    originalSettings.value = {
      fontSize: fontSize.value,
      interfaceScale: interfaceScale.value,
      selectedFont: selectedFont.value,
      density: density.value,
      boldHeadings: boldHeadings.value,
      increaseLineHeight: increaseLineHeight.value,
      monospaceCode: monospaceCode.value,
      reduceMotion: reduceMotion.value,
      highContrastMode: highContrastMode.value
    }
    
    // РџСЂРёРјРµРЅСЏРµРј РЅР°СЃС‚СЂРѕР№РєРё Рє РґРѕРєСѓРјРµРЅС‚Сѓ
    applyFontSettings(data)

    showToast('РќР°СЃС‚СЂРѕР№РєРё СЃРѕС…СЂР°РЅРµРЅС‹!')
  } catch (error) {
    console.error('Error saving font settings:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЃРѕС…СЂР°РЅРµРЅРёРё РЅР°СЃС‚СЂРѕРµРє')
  }
}

const resetToDefaults = () => {
  fontSize.value = 14
  interfaceScale.value = 100
  selectedFont.value = 'system'
  density.value = 'comfortable'
  boldHeadings.value = true
  increaseLineHeight.value = false
  monospaceCode.value = true
  reduceMotion.value = false
  highContrastMode.value = false
}

onMounted(() => {
  fetchFontSettings()
})
</script>

<style scoped>
.settings-group {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
}

.size-control, .scale-control {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.size-label, .scale-label {
  font-size: 13px;
  color: var(--secondary-text);
  min-width: 60px;
}

.size-slider, .scale-slider {
  flex: 1;
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
}

.size-slider::-webkit-slider-thumb, .scale-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
}

.size-value, .scale-value {
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.size-preview {
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.preview-text {
  line-height: 1.6;
}

.scale-presets {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.scale-preset {
  padding: 8px 16px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.scale-preset:hover {
  border-color: var(--primary-color);
}

.scale-preset.active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.font-selector {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.font-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 15px;
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.font-option:hover {
  background: var(--card-bg);
}

.font-option.active {
  border-color: var(--primary-color);
  background: rgba(0, 132, 255, 0.1);
}

.font-option input[type="radio"] {
  display: none;
}

.font-preview {
  font-size: 16px;
  font-weight: 500;
}

.font-preview.anime {
  font-family: 'Noto Sans JP', sans-serif;
}

.font-sample {
  padding: 20px;
  background: var(--card-bg);
  border-radius: 6px;
}

.sample-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.sample-text {
  font-size: 16px;
  line-height: 1.6;
  margin: 0 0 15px 0;
  color: var(--text-color);
}

.sample-subtitle {
  font-size: 18px;
  font-weight: 500;
  margin: 0 0 10px 0;
}

.sample-body {
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  color: var(--secondary-text);
}

.density-options {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.density-option {
  flex: 1;
  min-width: 150px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 15px;
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.density-option:hover {
  background: var(--card-bg);
}

.density-option.active {
  border-color: var(--primary-color);
  background: rgba(0, 132, 255, 0.1);
}

.density-option input[type="radio"] {
  display: none;
}

.density-preview {
  height: 60px;
  background: var(--card-bg);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  padding: 0 10px;
}

.density-preview.compact .preview-line {
  height: 6px;
}

.density-preview.comfortable .preview-line {
  height: 8px;
}

.density-preview.spacious .preview-line {
  height: 10px;
}

.preview-line {
  background: var(--border-color);
  border-radius: 2px;
  width: 100%;
}

.density-info {
  text-align: center;
}

.density-name {
  display: block;
  font-weight: 500;
  margin-bottom: 4px;
}

.density-desc {
  display: block;
  font-size: 12px;
  color: var(--secondary-text);
}

.special-settings {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.setting-option {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.setting-option:hover {
  background: var(--hover-bg);
}

.setting-option input[type="checkbox"] {
  margin: 0;
}

.setting-icon {
  font-size: 24px;
  width: 40px;
  text-align: center;
  font-weight: 600;
}

.setting-text {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.setting-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.setting-desc {
  font-size: 13px;
  color: var(--secondary-text);
}

.preview-container {
  padding: 25px;
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.preview-content h2.preview-heading {
  font-size: 1.8em;
  margin: 0 0 10px 0;
  font-weight: var(--heading-font-weight, 400);
}

.preview-content h3.preview-subheading {
  font-size: 1.4em;
  margin: 0 0 15px 0;
  font-weight: var(--subheading-font-weight, 400);
}

.preview-content p.preview-paragraph {
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.preview-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.preview-btn {
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  border: none;
}

.preview-btn.primary {
  background: var(--primary-color);
  color: white;
}

.preview-btn.secondary {
  background: var(--hover-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
}

.preview-list h4 {
  margin: 0 0 10px 0;
}

.preview-list ul {
  margin: 0;
  padding-left: 20px;
}

.preview-list li {
  margin-bottom: 5px;
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.save-btn, .reset-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.save-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reset-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}
</style>
