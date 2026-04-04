<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="chat-settings-modal">

        <!-- SIDEBAR -->
        <div class="settings-sidebar">
          <div class="sidebar-header">
            <div class="chat-info-row">
              <img v-if="chatAvatar" :src="chatAvatar" class="chat-avatar-mini" />
              <div v-else class="chat-avatar-mini avatar-placeholder">{{ (chatName || '?')[0] }}</div>
              <div class="chat-meta">
                <div class="chat-name-mini">{{ chatName }}</div>
                <div class="chat-type-pill">{{ chatType === 'group' ? 'Группа' : 'Личный' }}</div>
              </div>
            </div>
            <button @click="$emit('close')" class="close-btn">✕</button>
          </div>

          <nav class="sidebar-nav">
            <button
              v-for="section in availableSections"
              :key="section.id"
              @click="activeSection = section.id"
              class="nav-item"
              :class="{ active: activeSection === section.id }"
            >
              <span class="nav-icon">{{ section.icon }}</span>
              <span class="nav-label">{{ section.name }}</span>
            </button>
          </nav>
        </div>

        <!-- MAIN CONTENT -->
        <div class="settings-content">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>Загрузка настроек...</p>
          </div>

          <template v-else>

            <!-- ============ ОБОИ ============ -->
            <section v-if="activeSection === 'wallpaper'" class="settings-section">
              <div class="section-header">
                <h2>🖼️ Обои чата</h2>
                <button v-if="hasCustomWallpaper" @click="resetWallpaper" class="btn-ghost-sm">Сбросить</button>
              </div>

              <!-- Живой предпросмотр обоев -->
              <div class="wallpaper-preview" :style="wallpaperPreviewStyle">
                <div class="wp-msg wp-msg--other">
                  <div class="wp-bubble" :style="otherBubbleStyle">Привет! 👋</div>
                </div>
                <div class="wp-msg wp-msg--mine">
                  <div class="wp-bubble" :style="mineBubbleStyle">Привет! Смотрю аниме</div>
                </div>
              </div>

              <!-- Тип обоев -->
              <div class="field-group">
                <label class="field-label">Тип</label>
                <div class="type-tabs">
                  <button v-for="wt in wallpaperTypeOptions" :key="wt.value"
                    @click="wallpaperForm.wallpaper_type = wt.value"
                    class="type-tab" :class="{ active: wallpaperForm.wallpaper_type === wt.value }">
                    {{ wt.label }}
                  </button>
                </div>
              </div>

              <!-- Сплошной цвет -->
              <template v-if="wallpaperForm.wallpaper_type === 'solid'">
                <div class="field-group">
                  <label class="field-label">Цвет фона</label>
                  <div class="color-row">
                    <input type="color" v-model="wallpaperForm.wallpaper_color" class="color-picker-wide" />
                    <input type="text" v-model="wallpaperForm.wallpaper_color" class="color-hex-input" placeholder="#1a1a2e" />
                  </div>
                  <div class="color-swatches">
                    <button v-for="c in solidColorPresets" :key="c"
                      @click="wallpaperForm.wallpaper_color = c"
                      class="swatch" :style="{ background: c }"
                      :class="{ 'swatch--active': wallpaperForm.wallpaper_color === c }">
                    </button>
                  </div>
                </div>
              </template>

              <!-- Градиент -->
              <template v-if="wallpaperForm.wallpaper_type === 'gradient'">
                <div class="two-col">
                  <div class="field-group">
                    <label class="field-label">Цвет 1</label>
                    <div class="color-row">
                      <input type="color" v-model="wallpaperForm.wallpaper_color" class="color-picker-wide" />
                      <input type="text" v-model="wallpaperForm.wallpaper_color" class="color-hex-input" />
                    </div>
                  </div>
                  <div class="field-group">
                    <label class="field-label">Цвет 2</label>
                    <div class="color-row">
                      <input type="color" v-model="wallpaperForm.wallpaper_color2" class="color-picker-wide" />
                      <input type="text" v-model="wallpaperForm.wallpaper_color2" class="color-hex-input" />
                    </div>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Угол: {{ wallpaperForm.gradient_angle }}°</label>
                  <input type="range" v-model.number="wallpaperForm.gradient_angle" min="0" max="360" class="range-slider" />
                  <div class="angle-presets">
                    <button v-for="a in [0,45,90,135,180,225,270,315]" :key="a"
                      @click="wallpaperForm.gradient_angle = a"
                      class="angle-btn" :class="{ active: wallpaperForm.gradient_angle === a }">
                      {{ a }}°
                    </button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Готовые градиенты</label>
                  <div class="gradient-presets">
                    <button v-for="gp in gradientPresets" :key="gp.id"
                      @click="applyGradientPreset(gp)"
                      class="gradient-swatch"
                      :style="{ background: `linear-gradient(135deg, ${gp.color1}, ${gp.color2})` }">
                    </button>
                  </div>
                </div>
              </template>

              <!-- Паттерн -->
              <template v-if="wallpaperForm.wallpaper_type === 'pattern'">
                <div class="field-group">
                  <label class="field-label">Фон</label>
                  <div class="color-row">
                    <input type="color" v-model="wallpaperForm.wallpaper_color" class="color-picker-wide" />
                    <input type="text" v-model="wallpaperForm.wallpaper_color" class="color-hex-input" />
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Паттерн</label>
                  <div class="pattern-grid">
                    <button v-for="pt in patternTypes" :key="pt.value"
                      @click="wallpaperForm.pattern_type = pt.value"
                      class="pattern-btn" :class="{ active: wallpaperForm.pattern_type === pt.value }">
                      {{ pt.label }}
                    </button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Цвет паттерна</label>
                  <div class="color-row">
                    <input type="color" v-model="wallpaperForm.pattern_color" class="color-picker-wide" />
                    <input type="text" v-model="wallpaperForm.pattern_color" class="color-hex-input" />
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Прозрачность: {{ wallpaperForm.pattern_opacity }}%</label>
                  <input type="range" v-model.number="wallpaperForm.pattern_opacity" min="5" max="60" class="range-slider" />
                </div>
              </template>

              <!-- Изображение -->
              <template v-if="wallpaperForm.wallpaper_type === 'image'">
                <div class="field-group">
                  <label class="field-label">Изображение (до 5MB)</label>
                  <div class="upload-zone"
                    @click="triggerFileInput"
                    @dragover.prevent
                    @dragenter.prevent
                    @drop.prevent="handleWallpaperDrop">
                    <input ref="wallpaperFileRef" type="file" accept="image/*" @change="handleWallpaperFile" style="display:none" />
                    <div v-if="wallpaperImagePreview" class="upload-preview">
                      <img :src="wallpaperImagePreview" class="upload-preview-img" />
                      <button @click.stop="clearWallpaperImage" class="clear-btn">✕</button>
                    </div>
                    <div v-else class="upload-placeholder">
                      <div class="upload-icon-big">🖼️</div>
                      <p>Нажмите или перетащите файл</p>
                      <p class="upload-hint">JPG, PNG, WEBP — максимум 5MB</p>
                    </div>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Размытие: {{ wallpaperForm.wallpaper_blur }}px</label>
                  <input type="range" v-model.number="wallpaperForm.wallpaper_blur" min="0" max="20" class="range-slider" />
                </div>
                <div class="field-group">
                  <label class="field-label">Яркость: {{ wallpaperForm.wallpaper_intensity }}%</label>
                  <input type="range" v-model.number="wallpaperForm.wallpaper_intensity" min="20" max="100" class="range-slider" />
                </div>
              </template>

              <!-- Готовые пресеты -->
              <div class="field-group">
                <label class="field-label">Готовые обои</label>
                <div class="wallpaper-presets-grid">
                  <button v-for="preset in wallpaperPresets" :key="preset.id"
                    @click="applyWallpaperPreset(preset)"
                    class="wp-preset" :style="getPresetStyle(preset)"
                    :title="preset.name">
                    <span class="wp-preset-name">{{ preset.name }}</span>
                  </button>
                </div>
              </div>

              <div class="section-actions">
                <button @click="saveWallpaper" class="btn-primary" :disabled="saving">
                  <span v-if="saving" class="btn-spinner"></span>
                  {{ saving ? 'Сохранение...' : '💾 Сохранить обои' }}
                </button>
              </div>
            </section>

            <!-- ============ ТЕМА ============ -->
            <section v-if="activeSection === 'theme'" class="settings-section">
              <div class="section-header">
                <h2>🎨 Тема и стиль</h2>
                <button @click="resetTheme" class="btn-ghost-sm">Сбросить</button>
              </div>

              <!-- Предпросмотр -->
              <div class="theme-preview-wrap">
                <div class="theme-preview-chat" :style="{ background: themeForm.background_color }">
                  <div class="tp-header" :style="{ background: themeForm.header_color }">
                    <span>{{ chatName }}</span>
                  </div>
                  <div class="tp-messages">
                    <div class="tp-row tp-row--other">
                      <div class="tp-bubble" :style="otherBubblePreviewStyle">Привет!</div>
                    </div>
                    <div class="tp-row tp-row--mine">
                      <div class="tp-bubble" :style="mineBubblePreviewStyle">Как дела? 😊</div>
                    </div>
                    <div class="tp-row tp-row--other">
                      <div class="tp-bubble" :style="otherBubblePreviewStyle">Всё хорошо!</div>
                    </div>
                    <div class="tp-row tp-row--mine">
                      <div class="tp-bubble" :style="mineBubblePreviewStyle">Смотрю аниме</div>
                    </div>
                  </div>
                  <div class="tp-input" :style="{ background: themeForm.input_color }">
                    <span :style="{ color: themeForm.input_text_color, opacity: 0.5 }">Написать...</span>
                  </div>
                </div>
              </div>

              <!-- Готовые темы -->
              <div class="field-group">
                <label class="field-label">Готовые темы</label>
                <div class="theme-presets-grid">
                  <button v-for="preset in themePresets" :key="preset.id"
                    @click="applyThemePreset(preset)"
                    class="theme-preset-btn"
                    :class="{ active: currentPresetId === preset.id }">
                    <div class="tpb-preview">
                      <div class="tpb-mine" :style="{ background: preset.message_color_mine }"></div>
                      <div class="tpb-other" :style="{ background: preset.message_color_other }"></div>
                      <div class="tpb-bg" :style="{ background: preset.background_color || '#0f0f1a' }"></div>
                    </div>
                    <span class="tpb-name">{{ preset.name }}</span>
                  </button>
                </div>
              </div>

              <!-- ЦВЕТА СООБЩЕНИЙ -->
              <div class="settings-group-card">
                <div class="sgc-title">💬 Цвета сообщений</div>
                <div class="two-col">
                  <div class="field-group">
                    <label class="field-label">Мои (фон)</label>
                    <div class="color-row">
                      <input type="color" v-model="themeForm.message_color_mine" class="color-picker-wide" />
                      <input type="text" v-model="themeForm.message_color_mine" class="color-hex-input" />
                    </div>
                  </div>
                  <div class="field-group">
                    <label class="field-label">Чужие (фон)</label>
                    <div class="color-row">
                      <input type="color" v-model="themeForm.message_color_other" class="color-picker-wide" />
                      <input type="text" v-model="themeForm.message_color_other" class="color-hex-input" />
                    </div>
                  </div>
                </div>
                <div class="two-col">
                  <div class="field-group">
                    <label class="field-label">Мои (текст)</label>
                    <div class="color-row">
                      <input type="color" v-model="themeForm.message_text_color_mine" class="color-picker-wide" />
                      <input type="text" v-model="themeForm.message_text_color_mine" class="color-hex-input" />
                    </div>
                  </div>
                  <div class="field-group">
                    <label class="field-label">Чужие (текст)</label>
                    <div class="color-row">
                      <input type="color" v-model="themeForm.message_text_color_other" class="color-picker-wide" />
                      <input type="text" v-model="themeForm.message_text_color_other" class="color-hex-input" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- СТИЛЬ ПУЗЫРЕЙ -->
              <div class="settings-group-card">
                <div class="sgc-title">💭 Пузыри сообщений</div>
                <div class="field-group">
                  <label class="field-label">Стиль</label>
                  <div class="bubble-style-picker">
                    <button v-for="bs in bubbleStyles" :key="bs.value"
                      @click="themeForm.bubble_style = bs.value; themeForm.bubble_border_radius = bs.defaultRadius"
                      class="bsp-item" :class="{ active: themeForm.bubble_style === bs.value }">
                      <div class="bsp-demo" :style="{ borderRadius: bs.defaultRadius + 'px' }"></div>
                      <span>{{ bs.label }}</span>
                    </button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Скругление: {{ themeForm.bubble_border_radius }}px</label>
                  <input type="range" v-model.number="themeForm.bubble_border_radius" min="0" max="32" class="range-slider" />
                </div>
                <div class="toggle-row">
                  <div class="tr-info">
                    <span class="tr-label">Тень пузырей</span>
                  </div>
                  <label class="switch">
                    <input type="checkbox" v-model="themeForm.bubble_shadow" />
                    <span class="switch-slider"></span>
                  </label>
                </div>
              </div>

              <!-- ШРИФТЫ -->
              <div class="settings-group-card">
                <div class="sgc-title">🔤 Шрифт</div>
                <div class="field-group">
                  <label class="field-label">Гарнитура</label>
                  <div class="font-family-list">
                    <button v-for="ff in fontFamilies" :key="ff.value"
                      @click="themeForm.font_family = ff.value"
                      class="ff-btn" :class="{ active: themeForm.font_family === ff.value }"
                      :style="{ fontFamily: ff.css }">
                      {{ ff.label }}
                    </button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Размер</label>
                  <div class="font-size-picker">
                    <button v-for="fs in fontSizes" :key="fs.value"
                      @click="themeForm.font_size = fs.value; themeForm.font_size_px = fs.px"
                      class="fs-btn" :class="{ active: themeForm.font_size === fs.value }"
                      :style="{ fontSize: fs.px + 'px' }">
                      {{ fs.label }}
                    </button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Точный размер: {{ themeForm.font_size_px }}px</label>
                  <input type="range" v-model.number="themeForm.font_size_px" min="10" max="22" class="range-slider" />
                </div>
                <div class="field-group">
                  <label class="field-label">Толщина: {{ themeForm.font_weight }}</label>
                  <input type="range" v-model.number="themeForm.font_weight" min="300" max="700" step="100" class="range-slider" />
                </div>
                <div class="field-group">
                  <label class="field-label">Межстрочный: {{ themeForm.line_height }}</label>
                  <input type="range" v-model.number="themeForm.line_height" min="1.2" max="2.2" step="0.1" class="range-slider" />
                </div>
              </div>

              <!-- ЦВЕТА ИНТЕРФЕЙСА -->
              <div class="settings-group-card">
                <div class="sgc-title">🎨 Цвета интерфейса</div>
                <div class="interface-colors-grid">
                  <div v-for="ci in interfaceColors" :key="ci.key" class="ic-field">
                    <label class="field-label">{{ ci.label }}</label>
                    <div class="color-row">
                      <input type="color" v-model="themeForm[ci.key as keyof typeof themeForm]" class="color-picker-wide" />
                      <input type="text" v-model="themeForm[ci.key as keyof typeof themeForm]" class="color-hex-input" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- ФОРМАТ ВРЕМЕНИ -->
              <div class="settings-group-card">
                <div class="sgc-title">🕐 Время</div>
                <div class="field-group">
                  <label class="field-label">Формат</label>
                  <div class="type-tabs">
                    <button @click="themeForm.time_format = '24h'" class="type-tab" :class="{ active: themeForm.time_format === '24h' }">24ч</button>
                    <button @click="themeForm.time_format = '12h'" class="type-tab" :class="{ active: themeForm.time_format === '12h' }">12ч (AM/PM)</button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Цвет подписи времени</label>
                  <input type="text" v-model="themeForm.time_color" class="text-field" placeholder="rgba(255,255,255,0.5)" />
                </div>
              </div>

              <!-- АНИМАЦИИ -->
              <div class="settings-group-card">
                <div class="sgc-title">✨ Анимации</div>
                <div class="field-group">
                  <label class="field-label">Появление сообщений</label>
                  <div class="type-tabs">
                    <button v-for="a in messageAnimations" :key="a.value"
                      @click="themeForm.message_animation = a.value"
                      class="type-tab" :class="{ active: themeForm.message_animation === a.value }">
                      {{ a.label }}
                    </button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Реакции</label>
                  <div class="type-tabs">
                    <button v-for="a in reactionAnimations" :key="a.value"
                      @click="themeForm.reaction_animation = a.value"
                      class="type-tab" :class="{ active: themeForm.reaction_animation === a.value }">
                      {{ a.label }}
                    </button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Индикатор "печатает"</label>
                  <div class="type-tabs">
                    <button v-for="a in typingAnimations" :key="a.value"
                      @click="themeForm.typing_animation = a.value"
                      class="type-tab" :class="{ active: themeForm.typing_animation === a.value }">
                      {{ a.label }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- ЭМОДЗИ -->
              <div class="settings-group-card">
                <div class="sgc-title">😊 Эмодзи</div>
                <div class="field-group">
                  <label class="field-label">Набор</label>
                  <div class="type-tabs">
                    <button v-for="es in emojiSets" :key="es.value"
                      @click="themeForm.emoji_set = es.value"
                      class="type-tab" :class="{ active: themeForm.emoji_set === es.value }">
                      {{ es.label }}
                    </button>
                  </div>
                </div>
                <div class="field-group">
                  <label class="field-label">Размер</label>
                  <div class="type-tabs">
                    <button v-for="es in emojiSizes" :key="es.value"
                      @click="themeForm.emoji_size = es.value"
                      class="type-tab" :class="{ active: themeForm.emoji_size === es.value }">
                      {{ es.label }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- ДОПОЛНИТЕЛЬНО -->
              <div class="settings-group-card">
                <div class="sgc-title">⚙️ Дополнительно</div>
                <div class="toggle-list">
                  <div v-for="tog in themeToggles" :key="tog.key" class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">{{ tog.label }}</span>
                      <span v-if="tog.desc" class="tr-desc">{{ tog.desc }}</span>
                    </div>
                    <label class="switch">
                      <input type="checkbox" v-model="themeForm[tog.key as keyof typeof themeForm]" />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>
              </div>

              <!-- КАСТОМНЫЙ CSS -->
              <div class="settings-group-card">
                <div class="sgc-title">💻 Кастомный CSS</div>
                <textarea
                  v-model="themeForm.custom_css"
                  class="css-textarea"
                  placeholder="/* Ваш CSS для тонкой настройки */"
                  rows="5"
                ></textarea>
              </div>

              <div class="section-actions">
                <button @click="saveTheme" class="btn-primary" :disabled="saving">
                  <span v-if="saving" class="btn-spinner"></span>
                  {{ saving ? 'Сохранение...' : '💾 Сохранить тему' }}
                </button>
              </div>
            </section>

            <!-- ============ УВЕДОМЛЕНИЯ ============ -->
            <section v-if="activeSection === 'notifications'" class="settings-section">
              <div class="section-header"><h2>🔔 Уведомления</h2></div>

              <div class="settings-group-card">
                <div class="toggle-list">
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">Уведомления</span>
                      <span class="tr-desc">Получать уведомления из этого чата</span>
                    </div>
                    <label class="switch">
                      <input type="checkbox" v-model="notifForm.notifications_enabled" />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                  <template v-if="notifForm.notifications_enabled">
                    <div v-if="chatType === 'group'" class="toggle-row">
                      <div class="tr-info">
                        <span class="tr-label">Только упоминания</span>
                        <span class="tr-desc">Уведомлять только при @упоминании</span>
                      </div>
                      <label class="switch">
                        <input type="checkbox" v-model="notifForm.mentions_only" />
                        <span class="switch-slider"></span>
                      </label>
                    </div>
                    <div class="toggle-row">
                      <div class="tr-info"><span class="tr-label">Звук</span></div>
                      <label class="switch">
                        <input type="checkbox" v-model="notifForm.sound_enabled" />
                        <span class="switch-slider"></span>
                      </label>
                    </div>
                    <div class="toggle-row">
                      <div class="tr-info"><span class="tr-label">Превью сообщения</span></div>
                      <label class="switch">
                        <input type="checkbox" v-model="notifForm.show_preview" />
                        <span class="switch-slider"></span>
                      </label>
                    </div>
                  </template>
                </div>
              </div>

              <div class="settings-group-card">
                <div class="sgc-title">🔇 Заглушить</div>
                <div class="mute-grid">
                  <button v-for="opt in muteOptions" :key="opt.value"
                    @click="muteChat(opt.value)"
                    class="mute-btn" :class="{ active: currentMuteDuration === opt.value }">
                    {{ opt.label }}
                  </button>
                </div>
                <div v-if="notifForm.muted_until || notifForm.notifications_enabled === false" class="mute-status">
                  <span>🔇 {{ notifForm.muted_until ? `Заглушено до ${formatMuteDate(notifForm.muted_until)}` : 'Навсегда заглушено' }}</span>
                  <button @click="unmuteChat" class="btn-link">Включить звук</button>
                </div>
              </div>

              <div class="section-actions">
                <button @click="saveNotifSettings" class="btn-primary" :disabled="saving">
                  {{ saving ? 'Сохранение...' : '💾 Сохранить' }}
                </button>
              </div>
            </section>

            <!-- ============ ОРГАНИЗАЦИЯ ============ -->
            <section v-if="activeSection === 'organize'" class="settings-section">
              <div class="section-header"><h2>📂 Организация</h2></div>

              <div class="settings-group-card">
                <div class="toggle-list">
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">📌 Закрепить чат</span>
                      <span class="tr-desc">Показывать вверху списка</span>
                    </div>
                    <label class="switch">
                      <input type="checkbox" v-model="organizeForm.is_pinned" @change="saveOrganizeSettings" />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">📦 Архивировать</span>
                      <span class="tr-desc">Скрыть из основного списка</span>
                    </div>
                    <label class="switch">
                      <input type="checkbox" v-model="organizeForm.is_archived" @change="saveOrganizeSettings" />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                  <div v-if="chatType === 'private'" class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">🙈 Скрыть чат</span>
                      <span class="tr-desc">Не показывать в списке</span>
                    </div>
                    <label class="switch">
                      <input type="checkbox" v-model="organizeForm.is_hidden" @change="saveOrganizeSettings" />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>
              </div>

              <div class="settings-group-card">
                <div class="sgc-title">📁 Папка</div>
                <select v-model="organizeForm.folder_id" class="select-field" @change="saveOrganizeSettings">
                  <option :value="null">Без папки</option>
                  <option v-for="folder in chatFolders" :key="folder.id" :value="folder.id">
                    {{ folder.icon || '📁' }} {{ folder.name }}
                  </option>
                </select>
              </div>

              <div v-if="chatType === 'private'" class="settings-group-card">
                <div class="sgc-title">✏️ Кастомное название</div>
                <div class="field-group">
                  <input v-model="organizeForm.custom_name" class="text-field"
                    placeholder="Персональное название..." maxlength="255" />
                  <p class="field-hint">Видно только вам</p>
                </div>
                <button @click="saveOrganizeSettings" class="btn-secondary">Сохранить</button>
              </div>

              <div v-if="chatType === 'private'" class="settings-group-card">
                <div class="sgc-title">🗑️ Автоудаление</div>
                <div class="toggle-row">
                  <div class="tr-info">
                    <span class="tr-label">Автоудаление сообщений</span>
                    <span class="tr-desc">Удалять старые сообщения автоматически</span>
                  </div>
                  <label class="switch">
                    <input type="checkbox" v-model="organizeForm.auto_delete_enabled" @change="saveOrganizeSettings" />
                    <span class="switch-slider"></span>
                  </label>
                </div>
                <div v-if="organizeForm.auto_delete_enabled" class="field-group mt-3">
                  <label class="field-label">Через {{ organizeForm.auto_delete_after }} дней</label>
                  <input type="range" v-model.number="organizeForm.auto_delete_after"
                    min="1" max="365" class="range-slider" @change="saveOrganizeSettings" />
                </div>
              </div>
            </section>

            <!-- ============ ПРИВАТНОСТЬ ============ -->
            <section v-if="activeSection === 'privacy' && chatType === 'private'" class="settings-section">
              <div class="section-header"><h2>🔒 Приватность</h2></div>

              <div class="settings-group-card">
                <div class="danger-row">
                  <div class="dr-info">
                    <span class="dr-title">{{ privacyForm.is_blocked ? '✅ Разблокировать' : '🚫 Заблокировать пользователя' }}</span>
                    <span class="dr-desc">{{ privacyForm.is_blocked ? 'Снять блокировку' : 'Пользователь не сможет писать вам' }}</span>
                  </div>
                  <button v-if="!privacyForm.is_blocked" @click="blockUser" class="danger-btn">Заблокировать</button>
                  <button v-else @click="unblockUser" class="btn-secondary">Разблокировать</button>
                </div>
              </div>

              <div class="settings-group-card danger-card">
                <div class="sgc-title" style="color:#ef4444">⚠️ Опасная зона</div>
                <div class="danger-list">
                  <div class="danger-row">
                    <div class="dr-info">
                      <span class="dr-title">Очистить историю</span>
                      <span class="dr-desc">Удалить все сообщения только для вас</span>
                    </div>
                    <button @click="clearHistory" class="danger-btn">Очистить</button>
                  </div>
                  <div class="danger-row">
                    <div class="dr-info">
                      <span class="dr-title">Удалить чат</span>
                      <span class="dr-desc">Безвозвратное удаление переписки</span>
                    </div>
                    <button @click="deleteChat" class="danger-btn danger-btn--critical">Удалить</button>
                  </div>
                </div>
              </div>
            </section>

            <!-- ============ МОДЕРАЦИЯ ============ -->
            <section v-if="activeSection === 'moderation' && chatType === 'group'" class="settings-section">
              <div class="section-header"><h2>🛡️ Модерация</h2></div>

              <div class="settings-group-card">
                <div class="sgc-title">⏱️ Медленный режим</div>
                <div class="toggle-row">
                  <div class="tr-info">
                    <span class="tr-label">Медленный режим</span>
                    <span class="tr-desc">Ограничение частоты сообщений</span>
                  </div>
                  <label class="switch">
                    <input type="checkbox" v-model="groupSettings.slow_mode_enabled" @change="saveGroupSettings" />
                    <span class="switch-slider"></span>
                  </label>
                </div>
                <div v-if="groupSettings.slow_mode_enabled" class="field-group mt-3">
                  <label class="field-label">Задержка: {{ groupSettings.slow_mode_delay }}с</label>
                  <input type="range" v-model.number="groupSettings.slow_mode_delay"
                    min="5" max="3600" class="range-slider" @change="saveGroupSettings" />
                  <div class="slow-presets">
                    <button v-for="d in [5,10,30,60,300,3600]" :key="d"
                      @click="groupSettings.slow_mode_delay = d; saveGroupSettings()"
                      class="slow-preset-btn"
                      :class="{ active: groupSettings.slow_mode_delay === d }">
                      {{ formatDelay(d) }}
                    </button>
                  </div>
                </div>
              </div>

              <div class="settings-group-card">
                <div class="sgc-title">✉️ Разрешённый контент</div>
                <div class="toggle-list">
                  <div v-for="perm in contentPermissions" :key="perm.key" class="toggle-row">
                    <div class="tr-info"><span class="tr-label">{{ perm.label }}</span></div>
                    <label class="switch">
                      <input type="checkbox" v-model="groupSettings[perm.key as keyof typeof groupSettings]" @change="saveGroupSettings" />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>
              </div>

              <div class="settings-group-card">
                <div class="sgc-title">🔐 Приватность группы</div>
                <div class="toggle-list">
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">Скрыть список участников</span>
                    </div>
                    <label class="switch">
                      <input type="checkbox" v-model="groupSettings.has_hidden_members" @change="saveGroupSettings" />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">Запретить сохранение медиа</span>
                    </div>
                    <label class="switch">
                      <input type="checkbox" v-model="groupSettings.restrict_saving_content" @change="saveGroupSettings" />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>
              </div>
            </section>

          </template>
        </div>

      </div>
    </div>

    <!-- Toast уведомление -->
    <Transition name="toast-anim">
      <div v-if="toast.show" class="global-toast" :class="`toast-${toast.type}`">
        {{ toast.message }}
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'

interface ThemeForm {
  theme: string
  message_color_mine: string
  message_color_other: string
  message_text_color_mine: string
  message_text_color_other: string
  bubble_style: string
  bubble_border_radius: number
  bubble_shadow: boolean
  font_family: string
  font_size: string
  font_size_px: number
  font_weight: number
  line_height: number
  time_format: string
  time_color: string
  background_color: string
  header_color: string
  input_color: string
  input_text_color: string
  accent_color: string
  link_color: string
  message_animation: string
  reaction_animation: string
  typing_animation: string
  emoji_set: string
  emoji_size: string
  show_avatars: boolean
  show_usernames: boolean
  compact_mode: boolean
  show_read_status: boolean
  show_typing_indicator: boolean
  message_grouping: boolean
  custom_css: string
  [key: string]: any
}

interface GroupSettingsForm {
  slow_mode_enabled: boolean
  slow_mode_delay: number
  has_hidden_members: boolean
  restrict_saving_content: boolean
  can_send_media: boolean
  can_send_stickers: boolean
  can_send_polls: boolean
  can_invite_users: boolean
  can_pin_messages: boolean
  [key: string]: any
}

const props = defineProps<{
  chatId: number
  chatType: 'group' | 'private'
  chatName?: string
  chatAvatar?: string
  isAdmin?: boolean
  isOwner?: boolean
}>()

const emit = defineEmits<{
  close: []
  'settings-saved': [payload: any]
}>()

// ── State ──
const loading = ref(true)
const saving = ref(false)
const activeSection = ref('wallpaper')
const toast = ref({ show: false, message: '', type: 'success' })
const hasCustomWallpaper = ref(false)
const currentPresetId = ref<string | null>(null)
const currentMuteDuration = ref<number | null>(null)

// ── File upload ──
const wallpaperFileRef = ref<HTMLInputElement | null>(null)
const wallpaperImagePreview = ref<string | null>(null)
const wallpaperImageFile = ref<File | null>(null)

// ── Data ──
const wallpaperPresets = ref<any[]>([])
const themePresets = ref<any[]>([])
const chatFolders = ref<any[]>([])

// ── Forms ──
const wallpaperForm = ref({
  wallpaper_type: 'solid',
  wallpaper_color: '#0f0f1a',
  wallpaper_color2: '#1a1a2e',
  wallpaper_intensity: 100,
  wallpaper_blur: 0,
  wallpaper_motion: 'none',
  gradient_angle: 135,
  pattern_type: 'dots',
  pattern_color: '#3b82f6',
  pattern_opacity: 15,
})

const themeForm = ref<ThemeForm>({
  theme: 'default',
  message_color_mine: '#3b82f6',
  message_color_other: '#1e1e32',
  message_text_color_mine: '#ffffff',
  message_text_color_other: '#e2e8f0',
  bubble_style: 'modern',
  bubble_border_radius: 18,
  bubble_shadow: false,
  font_family: 'system',
  font_size: 'medium',
  font_size_px: 14,
  font_weight: 400,
  line_height: 1.5,
  time_format: '24h',
  time_color: 'rgba(255,255,255,0.5)',
  background_color: '#0f0f1a',
  header_color: '#1a1a2e',
  input_color: '#1e1e32',
  input_text_color: '#e2e8f0',
  accent_color: '#3b82f6',
  link_color: '#60a5fa',
  message_animation: 'slide',
  reaction_animation: 'bounce',
  typing_animation: 'dots',
  emoji_set: 'default',
  emoji_size: 'medium',
  show_avatars: true,
  show_usernames: true,
  compact_mode: false,
  show_read_status: true,
  show_typing_indicator: true,
  message_grouping: true,
  custom_css: '',
})

const notifForm = ref({
  notifications_enabled: true,
  mentions_only: false,
  sound_enabled: true,
  show_preview: true,
  muted_until: null as string | null,
})

const organizeForm = ref({
  is_pinned: false,
  is_archived: false,
  is_hidden: false,
  custom_name: '',
  folder_id: null as number | null,
  auto_delete_enabled: false,
  auto_delete_after: 30,
})

const privacyForm = ref({ is_blocked: false })

const groupSettings = ref<GroupSettingsForm>({
  slow_mode_enabled: false,
  slow_mode_delay: 30,
  has_hidden_members: false,
  restrict_saving_content: false,
  can_send_media: true,
  can_send_stickers: true,
  can_send_polls: true,
  can_invite_users: true,
  can_pin_messages: true,
})

// ── Computed ──
const availableSections = computed(() => {
  // Закомментировано: Тема, Уведомления, Организация, Модерация
  const s = [
    { id: 'wallpaper', name: 'Обои', icon: '🖼️' },
    // { id: 'theme', name: 'Тема', icon: '🎨' },
    // { id: 'notifications', name: 'Уведомления', icon: '🔔' },
    // { id: 'organize', name: 'Организация', icon: '📂' },
  ]
  if (props.chatType === 'private') s.push({ id: 'privacy', name: 'Приватность', icon: '🔒' })
  // if (props.chatType === 'group' && (props.isAdmin || props.isOwner))
  //   s.push({ id: 'moderation', name: 'Модерация', icon: '🛡️' })
  return s
})

const apiBase = computed(() => `/social/chat-settings/${props.chatType}/${props.chatId}`)

const bubbleRadiusVal = computed(() => {
  const map: Record<string, number> = { modern: 18, classic: 4, rounded: 24, flat: 8, minimal: 2 }
  return map[themeForm.value.bubble_style] ?? themeForm.value.bubble_border_radius
})

const fontFamilyCSS = computed(() => {
  const map: Record<string, string> = {
    system: 'system-ui,-apple-system,sans-serif',
    inter: 'Inter,sans-serif',
    roboto: 'Roboto,sans-serif',
    nunito: 'Nunito,sans-serif',
    montserrat: 'Montserrat,sans-serif',
    opensans: '"Open Sans",sans-serif',
  }
  return map[themeForm.value.font_family] || 'system-ui'
})

const wallpaperPreviewStyle = computed(() => {
  const f = wallpaperForm.value
  if (f.wallpaper_type === 'solid') return { background: f.wallpaper_color, minHeight: '120px', borderRadius: '10px' }
  if (f.wallpaper_type === 'gradient') {
    const c2 = f.wallpaper_color2 || f.wallpaper_color
    return { background: `linear-gradient(${f.gradient_angle}deg, ${f.wallpaper_color}, ${c2})`, minHeight: '120px', borderRadius: '10px' }
  }
  if (f.wallpaper_type === 'image' && wallpaperImagePreview.value) {
    return {
      backgroundImage: `url(${wallpaperImagePreview.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      minHeight: '120px',
      borderRadius: '10px',
      filter: `blur(${f.wallpaper_blur * 0.3}px) brightness(${f.wallpaper_intensity / 100})`,
    }
  }
  return { background: '#0f0f1a', minHeight: '120px', borderRadius: '10px' }
})

const mineBubbleStyle = computed(() => ({
  background: themeForm.value.message_color_mine,
  color: themeForm.value.message_text_color_mine,
  borderRadius: bubbleRadiusVal.value + 'px',
  fontFamily: fontFamilyCSS.value,
  fontSize: themeForm.value.font_size_px + 'px',
  padding: '6px 12px',
  display: 'inline-block',
  maxWidth: '80%',
}))

const otherBubbleStyle = computed(() => ({
  background: themeForm.value.message_color_other,
  color: themeForm.value.message_text_color_other,
  borderRadius: bubbleRadiusVal.value + 'px',
  fontFamily: fontFamilyCSS.value,
  fontSize: themeForm.value.font_size_px + 'px',
  padding: '6px 12px',
  display: 'inline-block',
  maxWidth: '80%',
}))

const mineBubblePreviewStyle = computed(() => ({
  ...mineBubbleStyle.value,
  boxShadow: themeForm.value.bubble_shadow ? '0 2px 8px rgba(0,0,0,0.3)' : 'none',
}))

const otherBubblePreviewStyle = computed(() => ({
  ...otherBubbleStyle.value,
  boxShadow: themeForm.value.bubble_shadow ? '0 2px 8px rgba(0,0,0,0.3)' : 'none',
}))

// ── Static data ──
const wallpaperTypeOptions = [
  { value: 'solid', label: '🎨 Цвет' },
  // Закомментировано: Градиент и Паттерн
  // { value: 'gradient', label: '🌈 Градиент' },
  // { value: 'pattern', label: '🔷 Паттерн' },
  { value: 'image', label: '🖼️ Картинка' },
]

const solidColorPresets = [
  '#0f0f1a','#1a1a2e','#1c1c1c','#0f172a','#1e1b4b',
  '#14532d','#7f1d1d','#1e3a5f','#2d1b69','#000000',
]

const gradientPresets = [
  { id:'g1', color1:'#1a1a2e', color2:'#16213e' },
  { id:'g2', color1:'#831843', color2:'#9a3412' },
  { id:'g3', color1:'#14532d', color2:'#134e4a' },
  { id:'g4', color1:'#4c1d95', color2:'#831843' },
  { id:'g5', color1:'#0c4a6e', color2:'#1e1b4b' },
  { id:'g6', color1:'#1e1b4b', color2:'#312e81' },
  { id:'g7', color1:'#1a1a2e', color2:'#4c1d95' },
  { id:'g8', color1:'#0a0a1a', color2:'#1a1a3e' },
]

const patternTypes = [
  { value:'dots', label:'Точки' },
  { value:'grid', label:'Сетка' },
  { value:'waves', label:'Волны' },
  { value:'hexagon', label:'Соты' },
  { value:'triangles', label:'Треугольники' },
]

const bubbleStyles = [
  { value:'modern', label:'Модерн', defaultRadius: 18 },
  { value:'classic', label:'Классика', defaultRadius: 4 },
  { value:'rounded', label:'Округлый', defaultRadius: 24 },
  { value:'flat', label:'Плоский', defaultRadius: 8 },
  { value:'minimal', label:'Минимал', defaultRadius: 2 },
]

const fontFamilies = [
  { value:'system', label:'Системный', css:'system-ui' },
  { value:'inter', label:'Inter', css:'Inter' },
  { value:'roboto', label:'Roboto', css:'Roboto' },
  { value:'nunito', label:'Nunito', css:'Nunito' },
  { value:'montserrat', label:'Montserrat', css:'Montserrat' },
]

const fontSizes = [
  { value:'small', label:'Маленький', px: 12 },
  { value:'medium', label:'Средний', px: 14 },
  { value:'large', label:'Большой', px: 16 },
  { value:'xlarge', label:'Очень большой', px: 18 },
]

const interfaceColors = [
  { key:'background_color', label:'Фон чата' },
  { key:'header_color', label:'Шапка' },
  { key:'input_color', label:'Поле ввода' },
  { key:'input_text_color', label:'Текст ввода' },
  { key:'accent_color', label:'Акцент' },
  { key:'link_color', label:'Ссылки' },
]

const messageAnimations = [
  { value:'slide', label:'Скольжение' },
  { value:'fade', label:'Затухание' },
  { value:'pop', label:'Появление' },
  { value:'none', label:'Нет' },
]

const reactionAnimations = [
  { value:'bounce', label:'Прыжок' },
  { value:'scale', label:'Масштаб' },
  { value:'none', label:'Нет' },
]

const typingAnimations = [
  { value:'dots', label:'Точки' },
  { value:'wave', label:'Волна' },
  { value:'pulse', label:'Пульс' },
]

const emojiSets = [
  { value:'default', label:'Системные' },
  { value:'twitter', label:'Twitter' },
  { value:'google', label:'Google' },
  { value:'anime', label:'Аниме' },
]

const emojiSizes = [
  { value:'small', label:'Маленький' },
  { value:'medium', label:'Средний' },
  { value:'large', label:'Большой' },
]

const themeToggles = [
  { key:'show_avatars', label:'Аватарки', desc:'' },
  { key:'show_usernames', label:'Имена участников', desc:'' },
  { key:'compact_mode', label:'Компактный режим', desc:'Уменьшает отступы' },
  { key:'show_read_status', label:'Статус прочтения', desc:'' },
  { key:'show_typing_indicator', label:'Индикатор печати', desc:'' },
  { key:'message_grouping', label:'Группировка сообщений', desc:'Объединять подряд идущие' },
]

const muteOptions = [
  { label:'15 мин', value: 15 },
  { label:'1 час', value: 60 },
  { label:'8 часов', value: 480 },
  { label:'2 дня', value: 2880 },
  { label:'1 неделя', value: 10080 },
  { label:'Навсегда', value: 0 },
]

const contentPermissions = [
  { key:'can_send_media', label:'Медиафайлы' },
  { key:'can_send_stickers', label:'Стикеры и GIF' },
  { key:'can_send_polls', label:'Опросы' },
  { key:'can_invite_users', label:'Приглашения' },
  { key:'can_pin_messages', label:'Закрепление сообщений' },
]

// ── Methods ──
async function loadSettings() {
  loading.value = true
  try {
    const [allRes, presetsRes, themePresetsRes, foldersRes] = await Promise.allSettled([
      apiClient.get(`${apiBase.value}/all/`),
      apiClient.get('/social/chat-settings/wallpapers/presets/'),
      apiClient.get('/social/chat-settings/themes/presets/'),
      apiClient.get('/social/chat-folders/'),
    ])

    if (allRes.status === 'fulfilled') {
      const d = allRes.value.data
      if (d.wallpaper) {
        hasCustomWallpaper.value = true
        Object.assign(wallpaperForm.value, d.wallpaper)
      }
      if (d.theme) Object.assign(themeForm.value, d.theme)
    }
    if (presetsRes.status === 'fulfilled') wallpaperPresets.value = presetsRes.value.data.presets || []
    if (themePresetsRes.status === 'fulfilled') themePresets.value = themePresetsRes.value.data.presets || []
    if (foldersRes.status === 'fulfilled') {
      chatFolders.value = foldersRes.value.data.results || foldersRes.value.data || []
    }

    await loadNotifSettings()
  } finally {
    loading.value = false
  }
}

async function loadNotifSettings() {
  try {
    const url = props.chatType === 'private'
      ? `/social/private-chats/${props.chatId}/settings/`
      : `/social/group-chats/${props.chatId}/notification-settings/`
    const { data } = await apiClient.get(url)
    Object.assign(notifForm.value, {
      notifications_enabled: data.notifications_enabled ?? true,
      mentions_only: data.mentions_only ?? false,
      sound_enabled: data.sound_enabled ?? true,
      show_preview: data.show_preview ?? true,
      muted_until: data.muted_until || null,
    })
    Object.assign(organizeForm.value, {
      is_pinned: data.is_pinned ?? false,
      is_archived: data.is_archived ?? false,
      is_hidden: data.is_hidden ?? false,
      custom_name: data.custom_name || '',
      folder_id: data.folder_id || null,
      auto_delete_enabled: data.auto_delete_enabled ?? false,
      auto_delete_after: data.auto_delete_after || 30,
    })
    privacyForm.value.is_blocked = data.is_blocked ?? false
  } catch { /* ignore */ }
}

async function saveWallpaper() {
  saving.value = true
  try {
    if (wallpaperForm.value.wallpaper_type === 'image' && wallpaperImageFile.value) {
      const fd = new FormData()
      fd.append('wallpaper_image', wallpaperImageFile.value)
      fd.append('wallpaper_blur', String(wallpaperForm.value.wallpaper_blur))
      fd.append('wallpaper_intensity', String(wallpaperForm.value.wallpaper_intensity))
      fd.append('wallpaper_type', 'image')
      await apiClient.post(`${apiBase.value}/wallpaper/set/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    } else {
      await apiClient.post(`${apiBase.value}/wallpaper/set/`, wallpaperForm.value)
    }
    hasCustomWallpaper.value = true
    showToast('✅ Обои сохранены')
    emit('settings-saved', { type: 'wallpaper', wallpaper: wallpaperForm.value })
  } catch (err: any) {
    showToast(err.response?.data?.error || 'Ошибка сохранения', 'error')
  } finally {
    saving.value = false
  }
}

async function resetWallpaper() {
  try {
    await apiClient.delete(`${apiBase.value}/wallpaper/reset/`)
    hasCustomWallpaper.value = false
    wallpaperImagePreview.value = null
    Object.assign(wallpaperForm.value, { wallpaper_type:'solid', wallpaper_color:'#0f0f1a', wallpaper_color2:'#1a1a2e' })
    showToast('Обои сброшены')
    emit('settings-saved', { type: 'wallpaper', reset: true })
  } catch { showToast('Ошибка', 'error') }
}

async function applyWallpaperPreset(preset: any) {
  Object.assign(wallpaperForm.value, preset)
  await saveWallpaper()
}

function applyGradientPreset(gp: any) {
  wallpaperForm.value.wallpaper_type = 'gradient'
  wallpaperForm.value.wallpaper_color = gp.color1
  wallpaperForm.value.wallpaper_color2 = gp.color2
}

async function saveTheme() {
  saving.value = true
  try {
    await apiClient.post(`${apiBase.value}/theme/set/`, themeForm.value)
    showToast('✅ Тема сохранена')
    emit('settings-saved', { type: 'theme', theme: { ...themeForm.value } })
    applyThemeToDom()
  } catch (err: any) {
    showToast(err.response?.data?.error || 'Ошибка', 'error')
  } finally {
    saving.value = false
  }
}

async function resetTheme() {
  try {
    await apiClient.delete(`${apiBase.value}/theme/reset/`)
    Object.assign(themeForm.value, {
      theme:'default', message_color_mine:'#3b82f6', message_color_other:'#1e1e32',
      message_text_color_mine:'#ffffff', message_text_color_other:'#e2e8f0',
      bubble_style:'modern', bubble_border_radius:18, bubble_shadow:false,
      font_family:'system', font_size:'medium', font_size_px:14,
      font_weight:400, line_height:1.5, time_format:'24h',
      background_color:'#0f0f1a', header_color:'#1a1a2e',
      input_color:'#1e1e32', accent_color:'#3b82f6',
    })
    currentPresetId.value = null
    showToast('Тема сброшена')
    emit('settings-saved', { type:'theme', reset:true })
  } catch { showToast('Ошибка', 'error') }
}

function applyThemePreset(preset: any) {
  currentPresetId.value = preset.id
  const fields = Object.keys(themeForm.value)
  fields.forEach(f => { if (f in preset) themeForm.value[f] = preset[f] })
  saveTheme()
}

function applyThemeToDom() {
  // Применяем CSS переменные в DOM для мгновенного отображения
  const root = document.documentElement
  const t = themeForm.value
  // Используем глобальные переменные для ChatDetailView
  root.style.setProperty('--chat-msg-mine-bg', t.message_color_mine)
  root.style.setProperty('--chat-msg-other-bg', t.message_color_other)
  root.style.setProperty('--chat-msg-mine-text', t.message_text_color_mine)
  root.style.setProperty('--chat-msg-other-text', t.message_text_color_other)
  root.style.setProperty('--chat-bg', t.background_color)
  root.style.setProperty('--chat-header-bg', t.header_color)
  root.style.setProperty('--chat-input-bg', t.input_color)
  root.style.setProperty('--chat-accent', t.accent_color)
  root.style.setProperty('--chat-font-size', t.font_size_px + 'px')
  root.style.setProperty('--chat-font-family', fontFamilyCSS.value)
  root.style.setProperty('--chat-font-weight', String(t.font_weight))
  root.style.setProperty('--chat-bubble-radius', bubbleRadiusVal.value + 'px')
  root.style.setProperty('--chat-bubble-shadow', t.bubble_shadow ? '0 2px 8px rgba(0,0,0,0.3)' : 'none')
}

async function saveNotifSettings() {
  saving.value = true
  try {
    const url = props.chatType === 'private'
      ? `/social/private-chats/${props.chatId}/user-settings/`
      : `/social/group-chats/${props.chatId}/member-settings/`
    await apiClient.put(url, notifForm.value)
    showToast('✅ Уведомления сохранены')
  } catch { showToast('Ошибка', 'error') }
  finally { saving.value = false }
}

async function muteChat(minutes: number) {
  try {
    const url = props.chatType === 'private'
      ? `/social/private-chats/${props.chatId}/mute/`
      : `/social/group-chats/${props.chatId}/mute/`
    await apiClient.post(url, { duration: minutes || null })
    currentMuteDuration.value = minutes
    if (minutes === 0) {
      notifForm.value.notifications_enabled = false
      notifForm.value.muted_until = null
    } else {
      notifForm.value.muted_until = new Date(Date.now() + minutes * 60000).toISOString()
    }
    showToast('🔇 Чат заглушен')
  } catch { showToast('Ошибка', 'error') }
}

async function unmuteChat() {
  try {
    if (props.chatType === 'private') {
      await apiClient.post(`/social/private-chats/${props.chatId}/unmute/`)
    } else {
      // Используем новый дедикированный эндпойнт
      await apiClient.post(`/social/group-chats/${props.chatId}/unmute/`)
    }
    notifForm.value.muted_until = null
    notifForm.value.notifications_enabled = true
    currentMuteDuration.value = null
    showToast('🔔 Уведомления включены')
  } catch { showToast('Ошибка', 'error') }
}

async function saveOrganizeSettings() {
  try {
    if (props.chatType === 'private') {
      // Для личных чатов — все настройки через один эндпойнт
      await apiClient.put(`/social/private-chats/${props.chatId}/settings/`, organizeForm.value)
    } else {
      // Для групп — архивацию и закрепление через специальные эндпойнты
      const tasks: Promise<any>[] = []

      // Архивация
      if ('is_archived' in organizeForm.value) {
        tasks.push(
          apiClient.post(`/social/group-chats/${props.chatId}/archive/`, {
            is_archived: organizeForm.value.is_archived
          })
        )
      }

      // Закрепление и остальные через member-settings
      const memberSettings: Record<string, any> = {}
      if ('is_pinned' in organizeForm.value) memberSettings.is_pinned = organizeForm.value.is_pinned
      if ('tags' in organizeForm.value) memberSettings.tags = organizeForm.value.tags
      if (Object.keys(memberSettings).length > 0) {
        tasks.push(
          apiClient.put(`/social/group-chats/${props.chatId}/member-settings/`, memberSettings)
        )
      }

      await Promise.all(tasks)
    }

    showToast('✅ Сохранено')
    emit('settings-saved', { type: 'organize', ...organizeForm.value })
  } catch { showToast('Ошибка', 'error') }
}

async function blockUser() {
  if (!confirm('Заблокировать пользователя?')) return
  try {
    await apiClient.post(`/social/private-chats/${props.chatId}/block/`)
    privacyForm.value.is_blocked = true
    showToast('🚫 Пользователь заблокирован')
  } catch { showToast('Ошибка', 'error') }
}

async function unblockUser() {
  try {
    await apiClient.post(`/social/private-chats/${props.chatId}/unblock/`)
    privacyForm.value.is_blocked = false
    showToast('✅ Пользователь разблокирован')
  } catch { showToast('Ошибка', 'error') }
}

async function clearHistory() {
  if (!confirm('Очистить историю? Это действие необратимо.')) return
  try {
    await apiClient.post(`/social/chats/${props.chatId}/clear-history/?type=${props.chatType}`)
    showToast('🗑️ История очищена')
  } catch { showToast('Ошибка', 'error') }
}

async function deleteChat() {
  if (!confirm('Удалить чат? Это действие необратимо!')) return
  showToast('Чат удалён')
  emit('close')
}

async function saveGroupSettings() {
  try {
    await apiClient.put(`/social/group-chats/${props.chatId}/settings/`, groupSettings.value)
    showToast('✅ Настройки сохранены')
  } catch { showToast('Ошибка', 'error') }
}

// ── File helpers ──
function triggerFileInput() {
  wallpaperFileRef.value?.click()
}

function handleWallpaperFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { showToast('Файл слишком большой (максимум 5MB)', 'error'); return }
  wallpaperImageFile.value = file
  wallpaperImagePreview.value = URL.createObjectURL(file)
}

function handleWallpaperDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (!file?.type.startsWith('image/')) return
  wallpaperImageFile.value = file
  wallpaperImagePreview.value = URL.createObjectURL(file)
}

function clearWallpaperImage() {
  wallpaperImageFile.value = null
  wallpaperImagePreview.value = null
  if (wallpaperFileRef.value) wallpaperFileRef.value.value = ''
}

// ── Style helpers ──
function getPresetStyle(preset: any): Record<string, string> {
  if (preset.wallpaper_type === 'gradient') {
    const c2 = preset.wallpaper_color2 || preset.wallpaper_color
    return { background: `linear-gradient(135deg, ${preset.wallpaper_color}, ${c2})` }
  }
  return { background: preset.wallpaper_color || '#1a1a2e' }
}

// ── Formatters ──
function formatMuteDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

function formatDelay(seconds: number): string {
  if (seconds < 60) return `${seconds}с`
  if (seconds < 3600) return `${seconds / 60}м`
  return `${seconds / 3600}ч`
}

// ── Toast ──
let toastTimer: ReturnType<typeof setTimeout> | null = null
function showToast(message: string, type: 'success' | 'error' = 'success') {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { show: true, message, type }
  toastTimer = setTimeout(() => { toast.value.show = false }, 3000)
}

onMounted(loadSettings)
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(5,4,8,0.88);
  backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}

.chat-settings-modal {
  display: flex;
  width: min(900px, 95vw);
  height: min(700px, 90vh);
  background: var(--surface-2);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-modal);
  border: 1px solid var(--border-default);
}

/* ── Sidebar ── */
.settings-sidebar {
  width: 220px;
  min-width: 220px;
  background: var(--surface-1);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-subtle);
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.chat-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.chat-avatar-mini {
  width: 36px; height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid var(--accent-subtle);
}

.avatar-placeholder {
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px; color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.chat-meta { min-width: 0; }
.chat-name-mini { font-size: 13px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chat-type-pill { font-size: 10px; color: var(--text-tertiary); background: var(--surface-4); padding: 1px 6px; border-radius: var(--radius-full); margin-top: 2px; display: inline-block; }

.close-btn {
  background: none; border: none; color: var(--text-secondary); cursor: pointer;
  font-size: 16px; padding: 4px; border-radius: var(--radius-md);
  transition: all 0.2s var(--ease-petal);
  flex-shrink: 0;
}
.close-btn:hover { color: var(--accent); background: var(--surface-4); }

.sidebar-nav { padding: 8px; overflow-y: auto; flex: 1; }

.nav-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 10px 12px;
  background: none; border: none; cursor: pointer;
  color: var(--text-secondary); border-radius: var(--radius-lg);
  transition: all 0.15s var(--ease-petal); text-align: left;
  font-size: 13px;
}
.nav-item:hover { background: var(--surface-4); color: var(--text-primary); }
.nav-item.active { background: var(--accent-subtle); color: var(--accent); font-weight: 500; }
.nav-icon { font-size: 16px; flex-shrink: 0; }
.nav-label { flex: 1; }

/* ── Content ── */
.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  min-width: 0;
}

.loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; gap: 12px; color: var(--text-tertiary);
}

.spinner {
  width: 32px; height: 32px;
  border: 3px solid var(--surface-4);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.settings-section { padding: 24px; }

.section-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px;
}
.section-header h2 { font-size: 18px; font-weight: 600; color: var(--text-primary); margin: 0; }

/* ── Cards ── */
.settings-group-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 16px;
  margin-bottom: 16px;
}
.sgc-title {
  font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--text-tertiary); margin-bottom: 12px;
}

/* ── Fields ── */
.field-group { margin-bottom: 14px; }
.field-label { display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }
.field-hint { font-size: 11px; color: var(--text-tertiary); margin-top: 4px; }
.mt-3 { margin-top: 12px; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.color-row { display: flex; align-items: center; gap: 8px; }
.color-picker-wide {
  width: 40px; height: 32px;
  padding: 2px; border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); background: var(--surface-4); cursor: pointer;
}
.color-hex-input {
  flex: 1; background: var(--surface-4); border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); padding: 6px 10px; color: var(--text-primary);
  font-size: 13px; font-family: monospace;
}
.color-hex-input:focus { outline: none; border-color: var(--accent); }

.color-swatches { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.swatch {
  width: 28px; height: 28px; border-radius: var(--radius-md);
  border: 2px solid transparent; cursor: pointer;
  transition: transform 0.15s var(--ease-petal), border-color 0.15s var(--ease-petal);
}
.swatch:hover { transform: scale(1.1); }
.swatch--active { border-color: var(--accent); transform: scale(1.1); }

.range-slider {
  width: 100%; accent-color: var(--accent);
  cursor: pointer; height: 4px;
}

/* ── Type tabs ── */
.type-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.type-tab {
  padding: 6px 14px; background: var(--surface-4);
  border: 1px solid var(--border-default); border-radius: var(--radius-lg);
  color: var(--text-secondary); font-size: 12px; cursor: pointer;
  transition: all 0.15s var(--ease-petal);
}
.type-tab:hover { border-color: var(--accent); color: var(--text-primary); }
.type-tab.active { background: var(--accent-subtle); border-color: var(--accent); color: var(--accent); }

/* ── Wallpaper preview ── */
.wallpaper-preview {
  position: relative;
  min-height: 110px; border-radius: var(--radius-lg);
  padding: 12px; margin-bottom: 16px;
  display: flex; flex-direction: column; gap: 6px;
  overflow: hidden;
  transition: all 0.3s var(--ease-petal);
}
.wp-msg { display: flex; }
.wp-msg--mine { justify-content: flex-end; }
.wp-msg--other { justify-content: flex-start; }
.wp-bubble { padding: 6px 12px; font-size: 13px; line-height: 1.4; }

/* ── Gradient presets ── */
.angle-presets { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.angle-btn {
  padding: 4px 8px; background: var(--surface-4);
  border: 1px solid var(--border-default); border-radius: var(--radius-md);
  color: var(--text-secondary); font-size: 11px; cursor: pointer;
}
.angle-btn.active { border-color: var(--accent); color: var(--accent); }

.gradient-presets { display: flex; flex-wrap: wrap; gap: 8px; }
.gradient-swatch {
  width: 48px; height: 32px; border-radius: var(--radius-lg);
  border: 2px solid transparent; cursor: pointer;
  transition: transform 0.15s var(--ease-petal), border-color 0.15s var(--ease-petal);
}
.gradient-swatch:hover { transform: scale(1.1); border-color: rgba(255,255,255,0.3); }

/* ── Pattern ── */
.pattern-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.pattern-btn {
  padding: 6px 12px; background: var(--surface-4);
  border: 1px solid var(--border-default); border-radius: var(--radius-lg);
  color: var(--text-secondary); font-size: 12px; cursor: pointer;
}
.pattern-btn.active { border-color: var(--accent); color: var(--accent); background: var(--accent-subtle); }

/* ── Upload ── */
.upload-zone {
  border: 2px dashed var(--border-default); border-radius: var(--radius-lg);
  cursor: pointer; transition: border-color 0.2s var(--ease-petal);
  overflow: hidden; min-height: 100px;
}
.upload-zone:hover { border-color: var(--accent); }
.upload-placeholder {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 24px; gap: 6px; color: var(--text-tertiary);
}
.upload-icon-big { font-size: 32px; }
.upload-hint { font-size: 11px; }
.upload-preview { position: relative; }
.upload-preview-img { width: 100%; max-height: 180px; object-fit: cover; display: block; }
.clear-btn {
  position: absolute; top: 6px; right: 6px;
  background: rgba(0,0,0,0.7); border: none; color: white;
  border-radius: 50%; width: 24px; height: 24px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; font-size: 12px;
}

/* ── Wallpaper presets ── */
.wallpaper-presets-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.wp-preset {
  aspect-ratio: 16/9; border-radius: var(--radius-lg); border: 2px solid transparent;
  cursor: pointer; position: relative; overflow: hidden;
  transition: border-color 0.2s var(--ease-petal), transform 0.15s var(--ease-petal);
}
.wp-preset:hover { border-color: rgba(255,255,255,0.3); transform: scale(1.02); }
.wp-preset-name {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: rgba(0,0,0,0.6); color: white; font-size: 9px;
  padding: 2px 4px; text-align: center;
}

/* ── Theme preview ── */
.theme-preview-wrap { margin-bottom: 16px; }
.theme-preview-chat {
  border-radius: var(--radius-lg); overflow: hidden;
  border: 1px solid var(--border-subtle);
  transition: background 0.3s var(--ease-petal);
}
.tp-header {
  padding: 10px 14px; font-size: 13px; font-weight: 600;
  color: var(--text-primary); transition: background 0.3s var(--ease-petal);
}
.tp-messages { padding: 10px; display: flex; flex-direction: column; gap: 6px; }
.tp-row { display: flex; }
.tp-row--mine { justify-content: flex-end; }
.tp-row--other { justify-content: flex-start; }
.tp-bubble { padding: 6px 12px; font-size: 13px; line-height: 1.4; max-width: 70%; }
.tp-input {
  padding: 10px 14px; font-size: 13px;
  border-top: 1px solid var(--border-subtle);
  transition: background 0.3s var(--ease-petal);
}

/* ── Theme presets ── */
.theme-presets-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.theme-preset-btn {
  background: var(--surface-4); border: 2px solid var(--border-default);
  border-radius: var(--radius-lg); padding: 10px 8px;
  cursor: pointer; transition: all 0.2s var(--ease-petal);
  display: flex; flex-direction: column; align-items: center; gap: 6px;
}
.theme-preset-btn:hover { border-color: var(--accent); }
.theme-preset-btn.active { border-color: var(--accent); }
.tpb-preview { width: 100%; height: 32px; border-radius: var(--radius-md); overflow: hidden; display: flex; gap: 2px; }
.tpb-mine, .tpb-other { flex: 1; height: 100%; }
.tpb-bg { width: 20px; flex-shrink: 0; }
.tpb-name { font-size: 10px; color: var(--text-secondary); text-align: center; }

/* ── Bubble style ── */
.bubble-style-picker { display: flex; gap: 8px; flex-wrap: wrap; }
.bsp-item {
  background: var(--surface-4); border: 1px solid var(--border-default); border-radius: var(--radius-lg);
  padding: 10px; cursor: pointer; display: flex; flex-direction: column;
  align-items: center; gap: 6px; min-width: 70px; transition: all 0.15s var(--ease-petal);
}
.bsp-item:hover { border-color: var(--accent); }
.bsp-item.active { border-color: var(--accent); background: var(--accent-subtle); }
.bsp-demo { width: 48px; height: 20px; background: var(--accent); }
.bsp-item span { font-size: 10px; color: var(--text-secondary); }

/* ── Font family ── */
.font-family-list { display: flex; gap: 6px; flex-wrap: wrap; }
.ff-btn {
  padding: 6px 12px; background: var(--surface-4); border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); color: var(--text-secondary); cursor: pointer; font-size: 13px;
  transition: all 0.15s var(--ease-petal);
}
.ff-btn:hover { border-color: var(--accent); color: var(--text-primary); }
.ff-btn.active { border-color: var(--accent); color: var(--accent); background: var(--accent-subtle); }

/* ── Font size ── */
.font-size-picker { display: flex; gap: 6px; }
.fs-btn {
  padding: 6px 12px; background: var(--surface-4); border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); color: var(--text-secondary); cursor: pointer; transition: all 0.15s var(--ease-petal);
}
.fs-btn:hover { border-color: var(--accent); color: var(--text-primary); }
.fs-btn.active { border-color: var(--accent); color: var(--accent); background: var(--accent-subtle); }

/* ── Interface colors ── */
.interface-colors-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.ic-field .field-label { font-size: 11px; }

/* ── Toggle ── */
.toggle-list { display: flex; flex-direction: column; gap: 2px; }
.toggle-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0; border-bottom: 1px solid var(--border-subtle);
}
.toggle-row:last-child { border-bottom: none; padding-bottom: 0; }
.tr-info { display: flex; flex-direction: column; gap: 2px; }
.tr-label { font-size: 13px; color: var(--text-primary); }
.tr-desc { font-size: 11px; color: var(--text-tertiary); }

.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
  flex-shrink: 0;
  cursor: pointer;
}
.switch input {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  cursor: pointer;
  margin: 0;
}
.switch-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--surface-5);
  border-radius: 22px;
  transition: background 0.2s var(--ease-petal);
  pointer-events: none;
}
.switch-slider::before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s var(--ease-petal);
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
.switch input:checked + .switch-slider {
  background: var(--accent);
}
.switch input:checked + .switch-slider::before {
  transform: translateX(18px);
}
.switch:hover .switch-slider {
  background: var(--surface-4);
}
.switch input:checked:hover + .switch-slider {
  background: var(--accent-press);
}

/* ── CSS textarea ── */
.css-textarea {
  width: 100%; background: var(--surface-1); border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); padding: 10px; color: var(--text-primary);
  font-family: 'Fira Code', monospace; font-size: 12px;
  resize: vertical; min-height: 80px; box-sizing: border-box;
}
.css-textarea:focus { outline: none; border-color: var(--accent); }

/* ── Select ── */
.select-field {
  width: 100%; background: var(--surface-4); border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); padding: 8px 12px; color: var(--text-primary);
  font-size: 13px; cursor: pointer;
}
.select-field:focus { outline: none; border-color: var(--accent); }

/* ── Text field ── */
.text-field {
  width: 100%; background: var(--surface-4); border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); padding: 8px 12px; color: var(--text-primary);
  font-size: 13px; box-sizing: border-box;
}
.text-field:focus { outline: none; border-color: var(--accent); }

/* ── Mute ── */
.mute-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.mute-btn {
  padding: 6px 14px; background: var(--surface-4); border: 1px solid var(--border-default);
  border-radius: var(--radius-lg); color: var(--text-secondary); cursor: pointer; font-size: 12px;
  transition: all 0.15s var(--ease-petal);
}
.mute-btn:hover { border-color: var(--accent); color: var(--text-primary); }
.mute-btn.active { background: var(--accent-subtle); border-color: var(--accent); color: var(--accent); }
.mute-status { margin-top: 10px; display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--text-secondary); }
.btn-link { background: none; border: none; color: var(--accent); cursor: pointer; font-size: 12px; padding: 0; }
.btn-link:hover { color: var(--accent-press); }

/* ── Slow mode presets ── */
.slow-presets { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.slow-preset-btn {
  padding: 4px 10px; background: var(--surface-4); border: 1px solid var(--border-default);
  border-radius: var(--radius-md); color: var(--text-secondary); font-size: 11px; cursor: pointer;
}
.slow-preset-btn.active { border-color: var(--accent); color: var(--accent); }

/* ── Danger ── */
.danger-card { border-color: var(--danger-subtle); }
.danger-list { display: flex; flex-direction: column; gap: 10px; }
.danger-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 0; border-bottom: 1px solid var(--border-subtle);
}
.danger-row:last-child { border-bottom: none; }
.dr-info { display: flex; flex-direction: column; gap: 2px; }
.dr-title { font-size: 13px; color: var(--text-primary); }
.dr-desc { font-size: 11px; color: var(--text-tertiary); }
.danger-btn {
  padding: 6px 14px; background: var(--danger); border: 1px solid var(--danger-press);
  color: white; border-radius: var(--radius-lg); cursor: pointer; font-size: 12px;
  transition: all 0.15s var(--ease-petal); white-space: nowrap;
}
.danger-btn:hover { background: var(--danger-press); }
.danger-btn--critical { background: var(--danger); border-color: var(--danger-press); color: white; font-weight: 600; }
.danger-btn--critical:hover { background: var(--danger-press); }

/* ── Buttons ── */
.section-actions { margin-top: 20px; }
.btn-primary {
  padding: 10px 20px; background: var(--accent); border: none;
  color: var(--text-on-accent); border-radius: var(--radius-lg); cursor: pointer; font-size: 14px;
  font-weight: 500; display: inline-flex; align-items: center; gap: 6px;
  transition: all 0.2s var(--ease-petal);
}
.btn-primary:hover { box-shadow: var(--shadow-glow-sm); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary {
  padding: 8px 16px; background: var(--surface-4); border: 1px solid var(--border-default);
  color: var(--text-primary); border-radius: var(--radius-lg); cursor: pointer; font-size: 13px;
  transition: all 0.15s var(--ease-petal);
}
.btn-secondary:hover { border-color: var(--accent); }
.btn-ghost-sm {
  padding: 6px 12px; background: none; border: 1px solid var(--border-default);
  color: var(--text-secondary); border-radius: var(--radius-lg); cursor: pointer; font-size: 12px;
  transition: all 0.15s var(--ease-petal);
}
.btn-ghost-sm:hover { border-color: var(--accent); color: var(--accent); }

.btn-spinner {
  display: inline-block; width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
  border-radius: 50%; animation: spin 0.7s linear infinite;
}

/* ── Toast ── */
.global-toast {
  position: fixed; bottom: 20px; right: 20px;
  padding: 12px 18px; border-radius: var(--radius-lg);
  font-size: 14px; font-weight: 500;
  box-shadow: var(--shadow-modal);
  z-index: 9999;
}
.toast-success { background: var(--success); color: white; border: 1px solid var(--success-press); }
.toast-error { background: var(--danger); color: white; border: 1px solid var(--danger-press); }

.toast-anim-enter-active, .toast-anim-leave-active { transition: all 0.3s var(--ease-bloom); }
.toast-anim-enter-from, .toast-anim-leave-to { opacity: 0; transform: translateY(12px); }

/* ── Scrollbar ── */
.settings-content::-webkit-scrollbar { width: 4px; }
.settings-content::-webkit-scrollbar-thumb { background: var(--surface-5); border-radius: 2px; }
.settings-content::-webkit-scrollbar-track { background: transparent; }

/* ── Responsive ── */
@media (max-width: 640px) {
  .chat-settings-modal { flex-direction: column; width: 100vw; height: 100vh; border-radius: 0; }
  .settings-sidebar { width: 100%; min-width: 0; flex-direction: row; overflow-x: auto; }
  .sidebar-header { display: none; }
  .sidebar-nav { display: flex; padding: 8px; gap: 4px; flex-direction: row; }
  .nav-item { flex-direction: column; min-width: 60px; padding: 8px 6px; font-size: 10px; }
  .nav-label { font-size: 10px; }
  .two-col { grid-template-columns: 1fr; }
  .interface-colors-grid { grid-template-columns: 1fr; }
}
</style>
