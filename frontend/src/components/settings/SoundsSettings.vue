<template>
  <div class="settings-section">
    <h2>Р—РІСѓРєРё Рё РІРёР±СЂР°С†РёСЏ</h2>

    <div class="settings-group">
      <h3>рџЋµ РџСЂРѕС„РёР»СЊ Р·РІСѓРєРѕРІ</h3>
      <div class="profile-selector">
        <select v-model="soundProfile" class="profile-select">
          <option value="classic">рџ”” РљР»Р°СЃСЃРёС‡РµСЃРєРёР№</option>
          <option value="quiet">рџ¤« РўРёС…РёР№ (С‚РѕР»СЊРєРѕ РІР°Р¶РЅС‹Рµ)</option>
          <option value="silent">рџ”‡ Р‘РµР· Р·РІСѓРєР°</option>
          <option value="anime">РђРЅРёРјРµ-РєРѕР»Р»РµРєС†РёСЏ</option>
        </select>
        <button @click="previewProfile" class="preview-btn">
          в–¶пёЏ РџСЂРѕС‚РµСЃС‚РёСЂРѕРІР°С‚СЊ
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџЋљпёЏ РРЅРґРёРІРёРґСѓР°Р»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё</h3>
      
      <div class="sound-settings-list">
        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">рџ’¬</span>
            <span class="sound-name">РЎРѕРѕР±С‰РµРЅРёРµ</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.message.sound" class="sound-select">
              <option value="default">РЎС‚Р°РЅРґР°СЂС‚</option>
              <option value="gentle">РњСЏРіРєРёР№</option>
              <option value="anime">РђРЅРёРјРµ</option>
              <option value="none">РќРµС‚</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.message.vibration" />
              <span class="toggle-icon">рџ“і</span>
            </label>
            <input
              v-model="sounds.message.volume"
              type="range"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.message.volume }}%</span>
          </div>
        </div>

        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">@</span>
            <span class="sound-name">РЈРїРѕРјРёРЅР°РЅРёРµ</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.mention.sound" class="sound-select">
              <option value="default">РЎС‚Р°РЅРґР°СЂС‚</option>
              <option value="special">РЎРїРµС†РёР°Р»СЊРЅС‹Р№</option>
              <option value="none">РќРµС‚</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.mention.vibration" />
              <span class="toggle-icon">рџ“і</span>
            </label>
            <input
              v-model="sounds.mention.volume"
              type="range"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.mention.volume }}%</span>
          </div>
        </div>

        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">вќ¤пёЏ</span>
            <span class="sound-name">Р›Р°Р№Рє</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.like.sound" class="sound-select">
              <option value="default">РЎС‚Р°РЅРґР°СЂС‚</option>
              <option value="short">РљРѕСЂРѕС‚РєРёР№</option>
              <option value="none">РќРµС‚</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.like.vibration" />
              <span class="toggle-icon">рџ“і</span>
            </label>
            <input
              v-model="sounds.like.volume"
              type="range"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.like.volume }}%</span>
          </div>
        </div>

        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">рџ‘Ґ</span>
            <span class="sound-name">РќРѕРІС‹Р№ РїРѕРґРїРёСЃС‡РёРє</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.follower.sound" class="sound-select">
              <option value="default">РЎС‚Р°РЅРґР°СЂС‚</option>
              <option value="none">РќРµС‚</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.follower.vibration" />
              <span class="toggle-icon">рџ“і</span>
            </label>
            <input
              v-model="sounds.follower.volume"
              type="range"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.follower.volume }}%</span>
          </div>
        </div>

        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">рџЏ†</span>
            <span class="sound-name">РќР°С‡Р°Р»Рѕ РєРѕРЅРєСѓСЂСЃР°</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.contest_start.sound" class="sound-select">
              <option value="default">РЎС‚Р°РЅРґР°СЂС‚</option>
              <option value="none">РќРµС‚</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.contest_start.vibration" />
              <span class="toggle-icon">рџ“і</span>
            </label>
            <input
              v-model="sounds.contest_start.volume"
              type="range"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.contest_start.volume }}%</span>
          </div>
        </div>

        <div class="sound-item important">
          <div class="sound-info">
            <span class="sound-icon">рџЋ‰</span>
            <span class="sound-name">РџРѕР±РµРґР° РІ РєРѕРЅРєСѓСЂСЃРµ!</span>
            <span class="always-on">Р’РЎР•Р“Р”Рђ Р’РљР›</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.contest_win.sound" class="sound-select">
              <option value="fanfare">Р¤Р°РЅС„Р°СЂС‹</option>
              <option value="anime">РђРЅРёРјРµ</option>
              <option value="none">РќРµС‚</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.contest_win.vibration" disabled />
              <span class="toggle-icon">рџ“і</span>
            </label>
            <input
              v-model="sounds.contest_win.volume"
              type="range"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.contest_win.volume }}%</span>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџЊ™ Р РµР¶РёРјС‹</h3>
      
      <div class="mode-settings">
        <label class="mode-option">
          <input type="checkbox" v-model="headphoneSound" />
          <span>рџЋ§ Р—РІСѓРє РІ РЅР°СѓС€РЅРёРєР°С…</span>
        </label>
        <label class="mode-option">
          <input type="checkbox" v-model="silentVibration" />
          <span>рџ“і Р’РёР±СЂР°С†РёСЏ РІ Р±РµР·Р·РІСѓС‡РЅРѕРј СЂРµР¶РёРјРµ</span>
        </label>
        <label class="mode-option">
          <input type="checkbox" v-model="doNotDisturb" />
          <span>рџЊ™ РќРµ Р±РµСЃРїРѕРєРѕРёС‚СЊ ({{ dndStart }} - {{ dndEnd }})</span>
        </label>
      </div>

      <div v-if="doNotDisturb" class="dnd-time-settings">
        <div class="time-inputs">
          <div class="time-input">
            <label>РЎ:</label>
            <input v-model="dndStart" type="time" class="time-picker" />
          </div>
          <div class="time-input">
            <label>Р”Рѕ:</label>
            <input v-model="dndEnd" type="time" class="time-picker" />
          </div>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ”Љ Р“Р»РѕР±Р°Р»СЊРЅР°СЏ РіСЂРѕРјРєРѕСЃС‚СЊ</h3>
      <div class="global-volume">
        <span>рџ”‡</span>
        <input
          v-model="globalVolume"
          type="range"
          min="0"
          max="100"
          class="global-slider"
        />
        <span>рџ”Љ</span>
        <span class="global-value">{{ globalVolume }}%</span>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџ§Є РўРµСЃС‚РѕРІС‹Р№ РїР»РµРµСЂ</h3>
      <p class="info-text">РџСЂРѕРёРіСЂС‹РІР°РµС‚СЃСЏ РґРµРјРѕ-РїРѕСЃР»РµРґРѕРІР°С‚РµР»СЊРЅРѕСЃС‚СЊ Р·РІСѓРєРѕРІ</p>
      
      <button @click="playDemoSequence" :disabled="isPlayingDemo" class="demo-btn">
        {{ isPlayingDemo ? 'в–¶пёЏ Р’РѕСЃРїСЂРѕРёР·РІРµРґРµРЅРёРµ...' : 'в–¶пёЏ РџСЂРѕС‚РµСЃС‚РёСЂРѕРІР°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё' }}
      </button>

      <div v-if="demoProgress" class="demo-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: demoProgress + '%' }"></div>
        </div>
        <div class="demo-status">{{ demoStatus }}</div>
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
import apiClient from '@/api/client'

interface SoundSettings {
  sound: string
  vibration: boolean
  volume: number
}

const soundProfile = ref('classic')
const globalVolume = ref(80)

const sounds = ref({
  message: { sound: 'default', vibration: true, volume: 80 },
  mention: { sound: 'default', vibration: true, volume: 100 },
  like: { sound: 'default', vibration: false, volume: 50 },
  follower: { sound: 'default', vibration: false, volume: 60 },
  contest_start: { sound: 'default', vibration: true, volume: 70 },
  contest_win: { sound: 'fanfare', vibration: true, volume: 100 }
})

const headphoneSound = ref(true)
const silentVibration = ref(true)
const doNotDisturb = ref(false)
const dndStart = ref('23:00')
const dndEnd = ref('08:00')

const originalSettings = ref({})

const isPlayingDemo = ref(false)
const demoProgress = ref(0)
const demoStatus = ref('')

const hasChanges = computed(() => {
  return JSON.stringify(sounds.value) !== JSON.stringify(originalSettings.value)
})

const fetchSoundSettings = async () => {
  try {
    const response = await apiClient.get('/users/sound-settings/')
    soundProfile.value = response.data.sound_profile || 'classic'
    globalVolume.value = response.data.global_volume || 80
    sounds.value = response.data.sounds || sounds.value
    headphoneSound.value = response.data.headphone_sound ?? true
    silentVibration.value = response.data.silent_vibration ?? true
    doNotDisturb.value = response.data.do_not_disturb || false
    dndStart.value = response.data.dnd_start || '23:00'
    dndEnd.value = response.data.dnd_end || '08:00'
    
    originalSettings.value = JSON.parse(JSON.stringify(sounds.value))
  } catch (error) {
    console.error('Error fetching sound settings:', error)
  }
}

const saveSettings = async () => {
  try {
    await apiClient.put('/users/sound-settings/', {
      sound_profile: soundProfile.value,
      global_volume: globalVolume.value,
      sounds: sounds.value,
      headphone_sound: headphoneSound.value,
      silent_vibration: silentVibration.value,
      do_not_disturb: doNotDisturb.value,
      dnd_start: dndStart.value,
      dnd_end: dndEnd.value
    })
    originalSettings.value = JSON.parse(JSON.stringify(sounds.value))
    showToast('РќР°СЃС‚СЂРѕР№РєРё СЃРѕС…СЂР°РЅРµРЅС‹!')
  } catch (error) {
    console.error('Error saving sound settings:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЃРѕС…СЂР°РЅРµРЅРёРё РЅР°СЃС‚СЂРѕРµРє')
  }
}

const resetToDefaults = () => {
  soundProfile.value = 'classic'
  globalVolume.value = 80
  sounds.value = {
    message: { sound: 'default', vibration: true, volume: 80 },
    mention: { sound: 'default', vibration: true, volume: 100 },
    like: { sound: 'default', vibration: false, volume: 50 },
    follower: { sound: 'default', vibration: false, volume: 60 },
    contest_start: { sound: 'default', vibration: true, volume: 70 },
    contest_win: { sound: 'fanfare', vibration: true, volume: 100 }
  }
  headphoneSound.value = true
  silentVibration.value = true
  doNotDisturb.value = false
}

const previewProfile = () => {
  // Play sound profile preview
  console.log('Previewing profile:', soundProfile.value)
}

const playDemoSequence = async () => {
  isPlayingDemo.value = true
  demoProgress.value = 0
  
  const demoSteps = [
    { sound: 'message', status: 'рџ’¬ РЎРѕРѕР±С‰РµРЅРёРµ' },
    { sound: 'mention', status: '@ РЈРїРѕРјРёРЅР°РЅРёРµ' },
    { sound: 'like', status: 'вќ¤пёЏ Р›Р°Р№Рє' },
    { sound: 'follower', status: 'рџ‘Ґ РќРѕРІС‹Р№ РїРѕРґРїРёСЃС‡РёРє' },
    { sound: 'contest_start', status: 'рџЏ† РќР°С‡Р°Р»Рѕ РєРѕРЅРєСѓСЂСЃР°' },
    { sound: 'contest_win', status: 'рџЋ‰ РџРѕР±РµРґР°!' }
  ]
  
  if (demoSteps) {
    for (const [index, step] of demoSteps.entries()) {
      demoStatus.value = step.status
      demoProgress.value = ((index + 1) / demoSteps.length) * 100
      
      // Play sound (in real app)
      await new Promise(resolve => setTimeout(resolve, 1500))
    }
  }
  
  isPlayingDemo.value = false
  demoStatus.value = 'вњ… Р—Р°РІРµСЂС€РµРЅРѕ'
  setTimeout(() => {
    demoProgress.value = 0
    demoStatus.value = ''
  }, 2000)
}

onMounted(() => {
  fetchSoundSettings()
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

.profile-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.profile-select {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 14px;
}

.preview-btn {
  padding: 10px 20px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.sound-settings-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sound-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.sound-item.important {
  border: 1px solid #FFD700;
  background: rgba(255, 215, 0, 0.05);
}

.sound-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sound-icon {
  font-size: 20px;
  width: 30px;
  text-align: center;
}

.sound-name {
  font-weight: 500;
  flex: 1;
}

.always-on {
  font-size: 11px;
  background: #4CAF50;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
}

.sound-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.sound-select {
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 13px;
}

.vibration-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.vibration-toggle input[type="checkbox"] {
  margin: 0;
}

.toggle-icon {
  font-size: 18px;
}

.volume-slider {
  width: 80px;
  height: 6px;
  background: var(--border-color);
  border-radius: 3px;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
}

.volume-value {
  font-size: 12px;
  color: var(--secondary-text);
  min-width: 35px;
}

.mode-settings {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}

.mode-option input[type="checkbox"] {
  margin: 0;
}

.dnd-time-settings {
  margin-top: 15px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.time-inputs {
  display: flex;
  gap: 15px;
}

.time-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.time-input label {
  font-weight: 500;
}

.time-picker {
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--card-bg);
  color: var(--text-color);
}

.global-volume {
  display: flex;
  align-items: center;
  gap: 15px;
}

.global-slider {
  flex: 1;
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
}

.global-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
}

.global-value {
  font-weight: 600;
  min-width: 45px;
  text-align: right;
}

.info-text {
  color: var(--secondary-text);
  margin-bottom: 15px;
}

.demo-btn {
  width: 100%;
  padding: 12px 20px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.demo-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.demo-progress {
  margin-top: 20px;
}

.progress-bar {
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.3s;
}

.demo-status {
  text-align: center;
  font-size: 14px;
  color: var(--secondary-text);
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
