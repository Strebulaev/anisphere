<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>Редактировать профиль</h3>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
        >
          <span v-if="tab.icon">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>

      <div class="modal-body">
        <form v-if="!isLoading" @submit.prevent="saveSettings">
          <!-- Basic Info Tab -->
          <div v-show="activeTab === 'basic'" class="tab-content">
            <!-- Avatar Upload -->
            <div class="form-group avatar-group">
              <label class="form-label">Фото профиля</label>
              <div class="avatar-upload">
                <div class="current-avatar">
                  <img v-if="formData.avatar" :src="formData.avatar" :alt="formData.displayName || 'Avatar'" class="avatar-preview">
                  <div v-else class="avatar-placeholder">
                    {{ getInitials(formData.displayName || formData.nickname || 'U') }}
                  </div>
                </div>
                <div class="upload-controls">
                  <input
                    type="file"
                    ref="fileInput"
                    @change="handleFileSelect"
                    accept="image/*"
                    style="display: none"
                  >
                  <button type="button" @click="fileInput?.click()" class="btn-upload">
                    Выбрать фото
                  </button>
                  <button v-if="formData.avatar" type="button" @click="deleteAvatar" class="btn-delete-avatar">
                    Удалить
                  </button>
                  <p class="upload-hint">JPG, PNG или GIF. Макс. 5MB</p>
                </div>
              </div>
            </div>

            <!-- Display Name -->
            <div class="form-group">
              <label for="displayName" class="form-label">Отображаемое имя</label>
              <input
                id="displayName"
                v-model="formData.displayName"
                type="text"
                class="form-input"
                placeholder="Ваше имя"
                maxlength="50"
              >
              <p class="field-hint">Это имя будет видно другим пользователям</p>
            </div>

            <!-- Nickname -->
            <div class="form-group">
              <label for="nickname" class="form-label">Никнейм <span class="required">*</span></label>
              <input
                id="nickname"
                v-model="formData.nickname"
                type="text"
                class="form-input"
                placeholder="уникальный_ник"
                maxlength="30"
                @blur="checkNickname"
              >
              <p class="field-hint">Уникальное имя для добавления в чаты. Только буквы, цифры и подчеркивания</p>
              <p v-if="errors.nickname" class="error-message">{{ errors.nickname }}</p>
              <p v-if="nicknameAvailable === true" class="success-message">✓ Nickname доступен</p>
            </div>

            <!-- Bio -->
            <div class="form-group">
              <label for="bio" class="form-label">О себе</label>
              <textarea
                id="bio"
                v-model="formData.bio"
                class="form-textarea"
                placeholder="Расскажите о себе..."
                maxlength="500"
                rows="3"
              ></textarea>
              <p class="field-hint">{{ formData.bio.length }}/500 символов</p>
            </div>

            <!-- Links -->
            <div class="form-group">
              <label class="form-label">Социальные ссылки</label>
              <div class="links-group">
                <div class="link-input">
                  <span class="link-prefix">https://</span>
                  <input
                    v-model="formData.website"
                    type="text"
                    class="form-input link-field"
                    placeholder="ваш-сайт.com"
                  >
                </div>
                <div class="link-input">
                  <span class="link-prefix">VK: </span>
                  <input
                    v-model="formData.vkProfile"
                    type="text"
                    class="form-input link-field"
                    placeholder="vk.com/username"
                  >
                </div>
                <div class="link-input">
                  <span class="link-prefix">Telegram: </span>
                  <input
                    v-model="formData.telegram"
                    type="text"
                    class="form-input link-field"
                    placeholder="@username"
                  >
                </div>
              </div>
            </div>

            <!-- Anime Interests -->
            <div class="form-group">
              <label class="form-label">Любимые жанры аниме</label>
              <div class="genres-grid">
                <label v-for="genre in animeGenres" :key="genre" class="genre-checkbox">
                  <input
                    type="checkbox"
                    :checked="formData.favoriteGenres.includes(genre)"
                    @change="toggleGenre(genre)"
                  >
                  {{ genre }}
                </label>
              </div>
            </div>
          </div>

          <!-- Appearance Tab -->
          <div v-show="activeTab === 'appearance'" class="tab-content">
            <h4 class="section-title">Внешний вид</h4>

            <!-- Theme -->
            <div class="form-group">
              <label class="form-label">Тема оформления</label>
              <div class="theme-options">
                <button
                  v-for="theme in themeOptions"
                  :key="theme.value"
                  type="button"
                  @click="(formData.theme as any) = theme.value"
                  :class="['theme-btn', { active: formData.theme === theme.value }]"
                >
                  <span class="theme-icon">{{ theme.icon }}</span>
                  {{ theme.label }}
                </button>
              </div>
            </div>

            <!-- Accent Color -->
            <div class="form-group">
              <label class="form-label">Акцентный цвет</label>
              <div class="color-picker">
                <button
                  v-for="color in accentColors"
                  :key="color"
                  type="button"
                  @click="formData.accentColor = color"
                  :class="['color-btn', { active: formData.accentColor === color }]"
                  :style="{ backgroundColor: color }"
                ></button>
              </div>
            </div>

            <h4 class="section-title">Язык и регион</h4>

            <!-- Language -->
            <div class="form-group">
              <label class="form-label">Язык</label>
              <select v-model="formData.language" class="form-select">
                <option value="ru">Русский</option>
                <option value="en">English</option>
                <option value="uk">Українська</option>
                <option value="be">Беларуская</option>
                <option value="kk">Қазақ тілі</option>
              </select>
            </div>

            <!-- Timezone -->
            <div class="form-group">
              <label class="form-label">Часовой пояс</label>
              <select v-model="formData.timezone" class="form-select">
                <option v-for="tz in timezones" :key="tz" :value="tz">{{ tz }}</option>
              </select>
            </div>

            <!-- Date Format -->
            <div class="form-group">
              <label class="form-label">Формат даты</label>
              <select v-model="formData.dateFormat" class="form-select">
                <option value="DD.MM.YYYY">ДД.ММ.ГГГГ</option>
                <option value="MM/DD/YYYY">ММ/ДД/ГГГГ</option>
                <option value="YYYY-MM-DD">ГГГГ-ММ-ДД</option>
              </select>
            </div>

            <!-- Time Format -->
            <div class="form-group">
              <label class="form-label">Формат времени</label>
              <div class="radio-group">
                <label class="radio-label">
                  <input type="radio" v-model="formData.timeFormat" value="24h">
                  24 часа
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="formData.timeFormat" value="12h">
                  12 часов (AM/PM)
                </label>
              </div>
            </div>
          </div>

          <!-- Notifications Tab -->
          <div v-show="activeTab === 'notifications'" class="tab-content">
            <h4 class="section-title">Общие уведомления</h4>

            <div class="toggle-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.notificationsEnabled">
                <span class="toggle-slider"></span>
                <span>Включить уведомления</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.soundEnabled">
                <span class="toggle-slider"></span>
                <span>Звук уведомления</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.vibrationEnabled">
                <span class="toggle-slider"></span>
                <span>Вибрация</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.previewEnabled">
                <span class="toggle-slider"></span>
                <span>Предпросмотр содержимого</span>
              </label>
            </div>

            <h4 class="section-title">Типы уведомлений</h4>

            <div class="toggle-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.messageNotifications">
                <span class="toggle-slider"></span>
                <span>Уведомления о сообщениях</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.groupNotifications">
                <span class="toggle-slider"></span>
                <span>Уведомления о группах</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.callNotifications">
                <span class="toggle-slider"></span>
                <span>Уведомления о звонках</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.mentionNotifications">
                <span class="toggle-slider"></span>
                <span>Уведомления об упоминаниях</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.reactionNotifications">
                <span class="toggle-slider"></span>
                <span>Уведомления о реакциях</span>
              </label>
            </div>

            <h4 class="section-title">Push-уведомления</h4>

            <div class="toggle-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.pushEnabled">
                <span class="toggle-slider"></span>
                <span>Включены push-уведомления</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.pushSoundEnabled" :disabled="!formData.pushEnabled">
                <span class="toggle-slider"></span>
                <span>Звук push-уведомлений</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.pushVibrationEnabled" :disabled="!formData.pushEnabled">
                <span class="toggle-slider"></span>
                <span>Вибрация push-уведомлений</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.pushPreviewEnabled" :disabled="!formData.pushEnabled">
                <span class="toggle-slider"></span>
                <span>Предпросмотр push-уведомлений</span>
              </label>
            </div>

            <h4 class="section-title">Email уведомления</h4>

            <div class="form-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.emailEnabled">
                <span class="toggle-slider"></span>
                <span>Включены email уведомления</span>
              </label>
            </div>

            <div class="form-group">
              <label class="form-label">Частота отправки</label>
              <select v-model="formData.emailFrequency" class="form-select" :disabled="!formData.emailEnabled">
                <option value="immediately">Немедленно</option>
                <option value="hourly">Каждый час</option>
                <option value="daily">Ежедневно</option>
                <option value="weekly">Еженедельно</option>
              </select>
            </div>

            <h4 class="section-title">Режим "Не беспокоить"</h4>

            <div class="toggle-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.doNotDisturbEnabled">
                <span class="toggle-slider"></span>
                <span>Включить режим</span>
              </label>
            </div>

            <div v-if="formData.doNotDisturbEnabled" class="time-range">
              <div class="form-group">
                <label class="form-label">Начало</label>
                <input type="time" v-model="formData.doNotDisturbStart" class="form-input">
              </div>
              <div class="form-group">
                <label class="form-label">Конец</label>
                <input type="time" v-model="formData.doNotDisturbEnd" class="form-input">
              </div>
            </div>

            <div v-if="formData.doNotDisturbEnabled" class="toggle-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.overrideChatSettings">
                <span class="toggle-slider"></span>
                <span>Переопределять настройки чатов</span>
              </label>
            </div>
          </div>

          <!-- Privacy Tab -->
          <div v-show="activeTab === 'privacy'" class="tab-content">
            <h4 class="section-title">Конфиденциальность</h4>

            <div class="toggle-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.showOnlineStatus">
                <span class="toggle-slider"></span>
                <span>Показывать статус онлайн</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.showLastSeen">
                <span class="toggle-slider"></span>
                <span>Показывать когда был в последний раз</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.showTypingStatus">
                <span class="toggle-slider"></span>
                <span>Показывать статус "печатает"</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.allowCalls">
                <span class="toggle-slider"></span>
                <span>Разрешить звонки</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.allowGroupInvites">
                <span class="toggle-slider"></span>
                <span>Разрешить приглашения в группы</span>
              </label>
            </div>

            <h4 class="section-title">Кто может видеть</h4>

            <div class="form-group">
              <label class="form-label">Кто может видеть телефон</label>
              <select v-model="formData.whoCanSeePhone" class="form-select">
                <option value="everyone">Все</option>
                <option value="contacts">Только контакты</option>
                <option value="nobody">Никто</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Кто может видеть email</label>
              <select v-model="formData.whoCanSeeEmail" class="form-select">
                <option value="everyone">Все</option>
                <option value="contacts">Только контакты</option>
                <option value="nobody">Никто</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Кто может видеть фото профиля</label>
              <select v-model="formData.whoCanSeeProfilePhoto" class="form-select">
                <option value="everyone">Все</option>
                <option value="contacts">Только контакты</option>
                <option value="nobody">Никто</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Кто может звонить</label>
              <select v-model="formData.whoCanCall" class="form-select">
                <option value="everyone">Все</option>
                <option value="contacts">Только контакты</option>
                <option value="nobody">Никто</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">Кто может добавлять в группы</label>
              <select v-model="formData.whoCanAddToGroups" class="form-select">
                <option value="everyone">Все</option>
                <option value="contacts">Только контакты</option>
                <option value="nobody">Никто</option>
              </select>
            </div>

            <div class="toggle-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.allowMessageForwarding">
                <span class="toggle-slider"></span>
                <span>Разрешить пересылку сообщений</span>
              </label>
            </div>

            <h4 class="section-title">Контакты</h4>

            <div class="toggle-group">
              <label class="toggle-label">
                <input type="checkbox" v-model="formData.syncContacts">
                <span class="toggle-slider"></span>
                <span>Синхронизировать контакты</span>
              </label>

              <label class="toggle-label">
                <input type="checkbox" v-model="formData.suggestFrequentContacts">
                <span class="toggle-slider"></span>
                <span>Предлагать частые контакты</span>
              </label>
            </div>
          </div>

          <!-- Security Tab -->
          <div v-show="activeTab === 'security'" class="tab-content">
            <h4 class="section-title">Двухфакторная аутентификация</h4>

            <div class="two-factor-status">
              <div :class="['status-badge', formData.twoFactorEnabled ? 'enabled' : 'disabled']">
                {{ formData.twoFactorEnabled ? '✓ Включена' : '✗ Отключена' }}
              </div>
            </div>

            <!-- 2FA Setup Flow -->
            <div v-if="!formData.twoFactorEnabled" class="form-group">
              <p class="field-hint">
                Двухфакторная аутентификация повышает безопасность вашего аккаунта.
                Для входа потребуется код из приложения аутентификатора.
              </p>
              <p class="field-hint" v-if="!authStore.user?.email_verified">
                <SakuraIcon name="warning" />️ Для включения 2FA необходимо подтвердить email
              </p>

              <div v-if="twoFactorSetup.step === 0">
                <button type="button" @click="startTwoFactorSetup" class="btn-primary" :disabled="!authStore.user?.email_verified">
                  Включить 2FA
                </button>
              </div>

              <div v-if="twoFactorSetup.step === 1" class="two-factor-setup">
                <h5>Шаг 1: Установите приложение</h5>
                <p class="field-hint">Установите приложение Google Authenticator, Authy или Microsoft Authenticator</p>

                <h5>Шаг 2: Отсканируйте QR-код</h5>
                <div class="qr-container">
                  <img v-if="twoFactorSetup.qrCode" :src="twoFactorSetup.qrCode" alt="QR Code" class="qr-code">
                  <p>Или введите код вручную:</p>
                  <code class="secret-code">{{ twoFactorSetup.secret }}</code>
                </div>

                <h5>Шаг 3: Введите код из приложения</h5>
                <div class="code-input">
                  <input
                    v-model="twoFactorSetup.verificationCode"
                    type="text"
                    maxlength="6"
                    placeholder="000000"
                    class="form-input code-field"
                    @input="formatTwoFactorCode"
                  >
                  <button type="button" @click="verifyTwoFactorCode" :disabled="twoFactorSetup.verificationCode.length !== 6" class="btn-primary">
                    Подтвердить
                  </button>
                </div>
                <button type="button" @click="cancelTwoFactorSetup" class="btn-secondary">Отмена</button>
              </div>
            </div>

            <!-- 2FA Enabled Settings -->
            <div v-else class="two-factor-settings">
              <div class="form-group">
                <label class="toggle-label">
                  <input type="checkbox" v-model="formData.requireOnNewDevice">
                  <span class="toggle-slider"></span>
                  <span>Требовать код на новых устройствах</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-label">Запоминать устройство на (дней)</label>
                <input
                  type="number"
                  v-model="formData.rememberDeviceDays"
                  class="form-input"
                  min="1"
                  max="365"
                >
              </div>

              <!-- Backup Codes Section -->
              <div class="backup-codes-section">
                <h5>Резервные коды ({{ twoFactorSetup.backupCodesCount }})</h5>
                <p class="field-hint">Сохраните эти коды в безопасном месте для доступа к аккаунту</p>

                <div v-if="twoFactorSetup.showBackupCodes" class="backup-codes-list">
                  <div v-for="(code, index) in twoFactorSetup.backupCodes" :key="index" class="backup-code-item">
                    {{ index + 1 }}. {{ code }}
                  </div>
                </div>

                <div class="backup-actions">
                  <button type="button" @click="toggleBackupCodes" class="btn-secondary">
                    {{ twoFactorSetup.showBackupCodes ? 'Скрыть' : 'Показать' }}
                  </button>
                  <button type="button" @click="copyBackupCodes" class="btn-secondary" :disabled="twoFactorSetup.backupCodes.length === 0"><SakuraIcon name="clipboard" /> Копировать</button>
                  <button type="button" @click="showRegenerateModal = true" class="btn-secondary"><SakuraIcon name="refresh" /> Новые коды</button>
                </div>
              </div>

              <!-- Security Log -->
              <div class="security-log-section">
                <h5>Лог безопасности</h5>
                <button type="button" @click="showSecurityLog" class="btn-secondary">
                  {{ twoFactorSetup.securityLog.length > 0 ? 'Скрыть историю' : 'Показать историю' }}
                </button>

                <div v-if="twoFactorSetup.securityLog.length > 0" class="security-log-list">
                  <div v-for="(log, index) in twoFactorSetup.securityLog" :key="index" class="log-item">
                    <div class="log-header">
                      <span class="log-action">{{ formatLogAction(log.action) }}</span>
                      <span class="log-date">{{ formatDate(log.created_at) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <button type="button" @click="showDisableModal = true" class="btn-danger">
                Отключить 2FA
              </button>
            </div>
          </div>

          <!-- Password Change Tab -->
          <div v-show="activeTab === 'password'" class="tab-content">
            <div class="password-section">
              <h4 class="section-title">Смена пароля</h4>

              <p class="password-warning">
                <SakuraIcon name="warning" />️ После смены пароля все другие сессии будут завершены. Вам нужно будет снова войти на всех устройствах.
              </p>

              <div class="form-group">
                <label for="oldPassword" class="form-label">Текущий пароль</label>
                <div class="password-input-wrapper">
                  <input
                    id="oldPassword"
                    v-model="passwordForm.oldPassword"
                    type="password"
                    class="form-input"
                    placeholder="Введите текущий пароль"
                    @input="delete passwordErrors.oldPassword"
                  >
                </div>
                <p v-if="passwordErrors.oldPassword" class="error-message">{{ passwordErrors.oldPassword }}</p>
              </div>

              <div class="form-group">
                <label for="newPassword" class="form-label">Новый пароль</label>
                <div class="password-input-wrapper">
                  <input
                    id="newPassword"
                    v-model="passwordForm.newPassword"
                    type="password"
                    class="form-input"
                    placeholder="Введите новый пароль"
                    @input="checkPasswordStrength(passwordForm.newPassword)"
                  >
                </div>
                <p v-if="passwordErrors.newPassword" class="error-message">{{ passwordErrors.newPassword }}</p>

                <!-- Password Strength Indicator -->
                <div v-if="passwordForm.newPassword" class="password-strength">
                  <div class="strength-bar">
                    <div
                      class="strength-fill"
                      :style="{ width: `${(passwordStrength / 5) * 100}%`, backgroundColor: getStrengthColor(passwordStrength) }"
                    ></div>
                  </div>
                  <p class="strength-text">
                    Сложность: <span :style="{ color: getStrengthColor(passwordStrength) }">{{ getStrengthLabel(passwordStrength) }}</span>
                  </p>
                </div>

                <!-- Password Requirements -->
                <div class="password-requirements">
                  <p class="requirements-title">Требования к паролю:</p>
                  <ul>
                    <li :class="{ met: passwordRequirements.minLength }">
                      {{ passwordRequirements.minLength ? '✓' : '○' }} Минимум 8 символов
                    </li>
                    <li :class="{ met: passwordRequirements.hasLetter }">
                      {{ passwordRequirements.hasLetter ? '✓' : '○' }} Минимум 1 буква
                    </li>
                    <li :class="{ met: passwordRequirements.hasDigit }">
                      {{ passwordRequirements.hasDigit ? '✓' : '○' }} Минимум 1 цифра
                    </li>
                    <li :class="{ met: passwordForm.newPassword.length >= 12 }">
                      {{ passwordForm.newPassword.length >= 12 ? '✓' : '○' }} 12+ символов (рекомендуется)
                    </li>
                  </ul>
                </div>
              </div>

              <div class="form-group">
                <label for="confirmPassword" class="form-label">Подтвердите новый пароль</label>
                <div class="password-input-wrapper">
                  <input
                    id="confirmPassword"
                    v-model="passwordForm.confirmPassword"
                    type="password"
                    class="form-input"
                    placeholder="Повторите новый пароль"
                    @input="delete passwordErrors.confirmPassword"
                  >
                </div>
                <p v-if="passwordErrors.confirmPassword" class="error-message">{{ passwordErrors.confirmPassword }}</p>
                <p v-else-if="passwordForm.confirmPassword && passwordForm.newPassword === passwordForm.confirmPassword" class="success-message">✓ Пароли совпадают</p>
              </div>

              <div class="password-actions">
                <button
                  type="button"
                  @click="changePassword"
                  class="btn-danger"
                  :disabled="isChangingPassword || !passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword"
                >
                  <span v-if="isChangingPassword">Смена пароля...</span>
                  <span v-else>Сменить пароль</span>
                </button>
              </div>

              <div class="password-tips">
                <h5><SakuraIcon name="lightbulb" /> Советы по созданию надежного пароля:</h5>
                <ul>
                  <li>Используйте комбинацию букв, цифр и специальных символов</li>
                  <li>Не используйте личную информацию (имя, дата рождения)</li>
                  <li>Не используйте тот же пароль на других сайтах</li>
                  <li>Используйте менеджер паролей для хранения</li>
                </ul>
              </div>
            </div>
          </div>
        </form>

        <div v-else class="loading-container">
          <div class="spinner"></div>
          <p>Загрузка настроек...</p>
        </div>
      </div>

      <!-- Disable 2FA Modal -->
      <div v-if="showDisableModal" class="modal-overlay" @click="showDisableModal = false">
        <div class="small-modal" @click.stop>
          <h4>Отключить 2FA?</h4>
          <p class="field-hint">Вы уверены, что хотите отключить двухфакторную аутентификацию? Это сделает ваш аккаунт менее защищенным.</p>

          <div class="form-group">
            <label class="form-label">Введите пароль для подтверждения:</label>
            <input v-model="disablePassword" type="password" class="form-input" placeholder="Пароль">
            <p v-if="disableError" class="error-message">{{ disableError }}</p>
          </div>

          <div class="modal-actions">
            <button @click="showDisableModal = false" class="btn-secondary">Отмена</button>
            <button @click="disableTwoFactor" :disabled="!disablePassword" class="btn-danger">Отключить</button>
          </div>
        </div>
      </div>

      <!-- Regenerate Backup Codes Modal -->
      <div v-if="showRegenerateModal" class="modal-overlay" @click="showRegenerateModal = false">
        <div class="small-modal" @click.stop>
          <h4>Сгенерировать новые коды?</h4>
          <p class="field-hint">Все старые резервные коды перестанут работать. Убедитесь, что у вас есть доступ к приложению аутентификатора.</p>

          <div class="form-group">
            <label class="form-label">Введите пароль для подтверждения:</label>
            <input v-model="regeneratePassword" type="password" class="form-input" placeholder="Пароль">
            <p v-if="regenerateError" class="error-message">{{ regenerateError }}</p>
          </div>

          <div class="modal-actions">
            <button @click="showRegenerateModal = false" class="btn-secondary">Отмена</button>
            <button @click="regenerateBackupCodes" :disabled="!regeneratePassword" class="btn-primary">Сгенерировать</button>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary">Отмена</button>
        <button @click="saveSettings" class="btn-primary" :disabled="isSaving || isLoading">
          <span v-if="isSaving">Сохранение...</span>
          <span v-else>Сохранить</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'
import { useAuthStore } from '@/stores/auth'

interface Props {
  isVisible: boolean
  onClose: () => void
  onSave?: () => void
}

const props = defineProps<Props>()
const authStore = useAuthStore()

const fileInput = ref<HTMLInputElement>()
const isLoading = ref(false)
const isSaving = ref(false)
const nicknameAvailable = ref<boolean | null>(null)
const errors = ref<Record<string, string>>({})
const activeTab = ref('basic')

const tabs = [
  { id: 'basic', label: 'Основное', icon: '🧑' },
  { id: 'appearance', label: 'Внешний вид', icon: '🎨' },
  { id: 'notifications', label: 'Уведомления', icon: '🔔' },
  { id: 'privacy', label: 'Приватность', icon: '🔐' },
  { id: 'security', label: 'Безопасность', icon: '🛡️' },
  { id: 'password', label: 'Сменить пароль', icon: '🔑' },
]

// Password change form
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const passwordErrors = ref<Record<string, string>>({})
const isChangingPassword = ref(false)
const passwordStrength = ref(0)
const passwordRequirements = reactive({
  minLength: false,
  hasLetter: false,
  hasDigit: false,
})

// Two Factor Auth
const twoFactorSetup = reactive({
  step: 0, // 0: not started, 1: setup in progress
  qrCode: '',
  secret: '',
  verificationCode: '',
  backupCodes: [] as string[],
  backupCodesCount: 0,
  showBackupCodes: false,
  securityLog: [] as any[],
})

const showDisableModal = ref(false)
const showRegenerateModal = ref(false)
const disablePassword = ref('')
const regeneratePassword = ref('')
const disableError = ref('')
const regenerateError = ref('')

const formData = reactive({
  // User data
  displayName: '',
  nickname: '',
  bio: '',
  avatar: '',
  favoriteGenres: [] as string[],
  website: '',
  vkProfile: '',
  telegram: '',

  // Profile settings
  theme: 'dark' as 'light' | 'dark' | 'system' | 'blue' | 'green',
  accentColor: '#3a86ff',
  language: 'ru' as 'ru' | 'en' | 'uk' | 'be' | 'kk',
  timezone: 'Europe/Moscow',
  dateFormat: 'DD.MM.YYYY' as 'DD.MM.YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD',
  timeFormat: '24h' as '24h' | '12h',

  // Notification settings
  notificationsEnabled: true,
  soundEnabled: true,
  vibrationEnabled: true,
  previewEnabled: true,
  messageNotifications: true,
  groupNotifications: true,
  callNotifications: true,
  mentionNotifications: true,
  reactionNotifications: true,
  pushEnabled: true,
  pushSoundEnabled: true,
  pushVibrationEnabled: true,
  pushPreviewEnabled: true,
  emailEnabled: true,
  emailFrequency: 'immediately' as 'immediately' | 'hourly' | 'daily' | 'weekly',
  doNotDisturbEnabled: false,
  doNotDisturbStart: '22:00',
  doNotDisturbEnd: '08:00',
  overrideChatSettings: false,

  // Privacy settings
  showOnlineStatus: true,
  showLastSeen: true,
  showTypingStatus: true,
  allowCalls: true,
  allowGroupInvites: true,
  whoCanSeePhone: 'contacts' as 'everyone' | 'contacts' | 'nobody',
  whoCanSeeEmail: 'contacts' as 'everyone' | 'contacts' | 'nobody',
  whoCanSeeProfilePhoto: 'everyone' as 'everyone' | 'contacts' | 'nobody',
  whoCanCall: 'everyone' as 'everyone' | 'contacts' | 'nobody',
  whoCanAddToGroups: 'everyone' as 'everyone' | 'contacts' | 'nobody',
  allowMessageForwarding: false,
  syncContacts: false,
  suggestFrequentContacts: false,

  // 2FA settings
  twoFactorEnabled: false,
  requireOnNewDevice: true,
  rememberDeviceDays: 30,
})

const animeGenres = [
  'Экшен',
  'Приключения',
  'Комедия',
  'Драма',
  'Фэнтези',
  'Романтика',
  'Sci-Fi',
  'Ужасы',
  'Детектив',
  'Повседневность'
]

const themeOptions = [
  { value: 'light', label: 'Светлая', icon: '☀' },
  { value: 'dark', label: 'Тёмная', icon: '🌙' },
  { value: 'system', label: 'Как в системе', icon: '💻' },
  { value: 'blue', label: 'Синяя', icon: '❍' },
  { value: 'green', label: 'Зелёная', icon: '❍' },
]

const accentColors = [
  '#3a86ff', // Blue
  '#ff006e', // Pink
  '#8338ec', // Purple
  '#ffbe0b', // Yellow
  '#fb5607', // Orange
  '#06d6a0', // Green
]

const timezones = [
  'Europe/Moscow',
  'Europe/Kiev',
  'Europe/Minsk',
  'Asia/Almaty',
  'UTC',
]

// Load settings when modal opens
watch(() => props.isVisible, (visible) => {
  if (visible) {
    loadSettings()
  }
})

async function loadSettings() {
  isLoading.value = true
  try {
    const data = await settingsApi.getAllSettings()

    // User data
    formData.displayName = data.user.display_name || ''
    formData.nickname = data.user.nickname || ''
    formData.bio = data.user.bio || ''
    formData.avatar = data.user.avatar || ''
    formData.favoriteGenres = data.user.favorite_genres || []
    formData.website = data.user.website || ''
    formData.vkProfile = data.user.vk_profile || ''
    formData.telegram = data.user.telegram || ''

    // Profile settings
    if (data.profile_settings) {
      Object.assign(formData, {
        theme: data.profile_settings.theme || 'dark',
        accentColor: data.profile_settings.accent_color || '#3a86ff',
        language: data.profile_settings.language || 'ru',
        timezone: data.profile_settings.timezone || 'Europe/Moscow',
        dateFormat: data.profile_settings.date_format || 'DD.MM.YYYY',
        timeFormat: data.profile_settings.time_format || '24h',
      })
    }

    // Notification settings
    if (data.notification_settings) {
      Object.assign(formData, {
        notificationsEnabled: data.notification_settings.enabled ?? true,
        soundEnabled: data.notification_settings.sound_enabled ?? true,
        vibrationEnabled: data.notification_settings.vibration_enabled ?? true,
        previewEnabled: data.notification_settings.preview_enabled ?? true,
        messageNotifications: data.notification_settings.message_notifications ?? true,
        groupNotifications: data.notification_settings.group_notifications ?? true,
        callNotifications: data.notification_settings.call_notifications ?? true,
        mentionNotifications: data.notification_settings.mention_notifications ?? true,
        reactionNotifications: data.notification_settings.reaction_notifications ?? true,
        pushEnabled: data.notification_settings.push_enabled ?? true,
        pushSoundEnabled: data.notification_settings.push_sound_enabled ?? true,
        pushVibrationEnabled: data.notification_settings.push_vibration_enabled ?? true,
        pushPreviewEnabled: data.notification_settings.push_preview_enabled ?? true,
        emailEnabled: data.notification_settings.email_enabled ?? true,
        emailFrequency: data.notification_settings.email_frequency || 'immediately',
        doNotDisturbEnabled: data.notification_settings.do_not_disturb_enabled ?? false,
        doNotDisturbStart: data.notification_settings.do_not_disturb_start || '22:00',
        doNotDisturbEnd: data.notification_settings.do_not_disturb_end || '08:00',
        overrideChatSettings: data.notification_settings.override_chat_settings ?? false,
      })
    }

    // Privacy settings
    if (data.privacy_settings) {
      Object.assign(formData, {
        showOnlineStatus: data.privacy_settings.show_online_status ?? true,
        showLastSeen: data.privacy_settings.show_last_seen ?? true,
        showTypingStatus: data.privacy_settings.show_typing_status ?? true,
        allowCalls: data.privacy_settings.allow_calls ?? true,
        allowGroupInvites: data.privacy_settings.allow_group_invites ?? true,
        whoCanSeePhone: data.privacy_settings.who_can_see_phone || 'contacts',
        whoCanSeeEmail: data.privacy_settings.who_can_see_email || 'contacts',
        whoCanSeeProfilePhoto: data.privacy_settings.who_can_see_profile_photo || 'everyone',
        whoCanCall: data.privacy_settings.who_can_call || 'everyone',
        whoCanAddToGroups: data.privacy_settings.who_can_add_to_groups || 'everyone',
        allowMessageForwarding: data.privacy_settings.allow_message_forwarding ?? false,
        syncContacts: data.privacy_settings.sync_contacts ?? false,
        suggestFrequentContacts: data.privacy_settings.suggest_frequent_contacts ?? false,
      })
    }

    // 2FA settings
    if (data.two_factor_settings) {
      Object.assign(formData, {
        twoFactorEnabled: data.two_factor_settings.is_enabled ?? false,
        requireOnNewDevice: data.two_factor_settings.require_on_new_device ?? true,
        rememberDeviceDays: data.two_factor_settings.remember_device_days || 30,
      })

      // Load backup codes count if 2FA is enabled
      if (data.two_factor_settings.is_enabled) {
        twoFactorSetup.backupCodesCount = data.two_factor_settings.backup_codes_count || 0
      }
    }
  } catch (error) {
    console.error('Error loading settings:', error)
  } finally {
    isLoading.value = false
  }
}

function getInitials(name: string) {
  return name.charAt(0).toUpperCase()
}

async function handleFileSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    if (file.size > 5 * 1024 * 1024) {
      alert('Файл слишком большой. Максимальный размер: 5MB')
      return
    }

    if (!file.type.startsWith('image/')) {
      alert('Пожалуйста, выберите изображение')
      return
    }

    try {
      const result = await settingsApi.uploadAvatar(file)
      formData.avatar = result.avatar_url || ''
    } catch (error) {
      console.error('Error uploading avatar:', error)
      alert('Ошибка при загрузке аватара')
    }
  }
}

async function deleteAvatar() {
  try {
    await settingsApi.deleteAvatar()
    formData.avatar = ''
  } catch (error) {
    console.error('Error deleting avatar:', error)
    alert('Ошибка при удалении аватара')
  }
}

async function checkNickname() {
  const nickname = formData.nickname.trim()
  if (!nickname) {
    nicknameAvailable.value = null
    return
  }

  if (!/^[a-zA-Z0-9_]+$/.test(nickname)) {
    errors.value.nickname = 'Никнейм может содержать только буквы, цифры и подчеркивания'
    nicknameAvailable.value = false
    return
  }

  try {
    const response = await fetch('/api/users/nickname/check/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname }),
    })

    const data = await response.json()
    nicknameAvailable.value = data.available
    if (!data.available) {
      errors.value.nickname = data.error || 'Этот nickname уже занят'
    } else {
      delete errors.value.nickname
    }
  } catch (error) {
    console.error('Error checking nickname:', error)
  }
}

function toggleGenre(genre: string) {
  const index = formData.favoriteGenres.indexOf(genre)
  if (index === -1) {
    if (formData.favoriteGenres.length < 20) {
      formData.favoriteGenres.push(genre)
    }
  } else {
    formData.favoriteGenres.splice(index, 1)
  }
}

async function saveSettings() {
  if (isSaving.value) return

  // Validation
  errors.value = {}

  if (!formData.displayName.trim()) {
    errors.value.displayName = 'Имя обязательно'
  }

  if (!formData.nickname.trim()) {
    errors.value.nickname = 'Nickname обязателен'
  }

  if (formData.bio && formData.bio.length > 500) {
    errors.value.bio = 'Описание не должно превышать 500 символов'
  }

  if (Object.keys(errors.value).length > 0) {
    return
  }

  isSaving.value = true

  try {
    await settingsApi.updateSettings({
      user: {
        display_name: formData.displayName,
        nickname: formData.nickname,
        bio: formData.bio,
        favorite_genres: formData.favoriteGenres,
        website: formData.website,
        vk_profile: formData.vkProfile,
        telegram: formData.telegram,
      },
      profile_settings: {
        theme: formData.theme,
        accent_color: formData.accentColor,
        language: formData.language,
        timezone: formData.timezone,
        date_format: formData.dateFormat,
        time_format: formData.timeFormat,
      },
      notification_settings: {
        enabled: formData.notificationsEnabled,
        sound_enabled: formData.soundEnabled,
        vibration_enabled: formData.vibrationEnabled,
        preview_enabled: formData.previewEnabled,
        message_notifications: formData.messageNotifications,
        group_notifications: formData.groupNotifications,
        call_notifications: formData.callNotifications,
        mention_notifications: formData.mentionNotifications,
        reaction_notifications: formData.reactionNotifications,
        push_enabled: formData.pushEnabled,
        push_sound_enabled: formData.pushSoundEnabled,
        push_vibration_enabled: formData.pushVibrationEnabled,
        push_preview_enabled: formData.pushPreviewEnabled,
        email_enabled: formData.emailEnabled,
        email_frequency: formData.emailFrequency,
        do_not_disturb_enabled: formData.doNotDisturbEnabled,
        do_not_disturb_start: formData.doNotDisturbStart,
        do_not_disturb_end: formData.doNotDisturbEnd,
        override_chat_settings: formData.overrideChatSettings,
      },
      privacy_settings: {
        show_online_status: formData.showOnlineStatus,
        show_last_seen: formData.showLastSeen,
        show_typing_status: formData.showTypingStatus,
        allow_calls: formData.allowCalls,
        allow_group_invites: formData.allowGroupInvites,
        who_can_see_phone: formData.whoCanSeePhone,
        who_can_see_email: formData.whoCanSeeEmail,
        who_can_see_profile_photo: formData.whoCanSeeProfilePhoto,
        who_can_call: formData.whoCanCall,
        who_can_add_to_groups: formData.whoCanAddToGroups,
        allow_message_forwarding: formData.allowMessageForwarding,
        sync_contacts: formData.syncContacts,
        suggest_frequent_contacts: formData.suggestFrequentContacts,
      },
      two_factor_settings: {
        is_enabled: formData.twoFactorEnabled,
        require_on_new_device: formData.requireOnNewDevice,
        remember_device_days: formData.rememberDeviceDays,
      },
    })

    // Refresh user data in store
    await authStore.fetchUser()

    props.onSave?.()
    closeModal()
  } catch (error: any) {
    console.error('Error saving settings:', error)
    if (error.response?.data) {
      const apiErrors = error.response.data
      Object.keys(apiErrors).forEach((key) => {
        errors.value[key] = Array.isArray(apiErrors[key]) ? apiErrors[key][0] : apiErrors[key]
      })
    } else {
      alert('Ошибка при сохранении настроек')
    }
  } finally {
    isSaving.value = false
  }
}

async function enableTwoFactor() {
  alert('Для включения 2FA необходимо подтвердить email')
}

// Two Factor Auth functions
async function startTwoFactorSetup() {
  try {
    const data = await settingsApi.enableTwoFactor()
    twoFactorSetup.qrCode = data.qr_code
    twoFactorSetup.secret = data.secret
    twoFactorSetup.step = 1
  } catch (error: any) {
    console.error('Error starting 2FA setup:', error)
    if (error.response?.data?.error) {
      alert(error.response.data.error)
    }
  }
}

function formatTwoFactorCode() {
  twoFactorSetup.verificationCode = twoFactorSetup.verificationCode.replace(/\D/g, '').slice(0, 6)
}

async function verifyTwoFactorCode() {
  try {
    await settingsApi.verifyTwoFactor(twoFactorSetup.verificationCode)
    formData.twoFactorEnabled = true
    twoFactorSetup.step = 0
    twoFactorSetup.verificationCode = ''
    alert('2FA успешно включена!')
    await loadSettings()
  } catch (error: any) {
    console.error('Error verifying 2FA code:', error)
    if (error.response?.data?.error) {
      alert(error.response.data.error)
    }
  }
}

function cancelTwoFactorSetup() {
  twoFactorSetup.step = 0
  twoFactorSetup.qrCode = ''
  twoFactorSetup.secret = ''
  twoFactorSetup.verificationCode = ''
}

async function loadBackupCodes() {
  try {
    const data = await settingsApi.getBackupCodes()
    twoFactorSetup.backupCodes = data.codes || []
    twoFactorSetup.backupCodesCount = data.count || data.codes?.length || 0
  } catch (error: any) {
    console.error('Error loading backup codes:', error)
  }
}

async function toggleBackupCodes() {
  if (!twoFactorSetup.showBackupCodes && twoFactorSetup.backupCodes.length === 0) {
    await loadBackupCodes()
  }
  twoFactorSetup.showBackupCodes = !twoFactorSetup.showBackupCodes
}

async function regenerateBackupCodes() {
  try {
    const data = await settingsApi.regenerateBackupCodes(regeneratePassword.value)
    twoFactorSetup.backupCodes = data.codes || []
    twoFactorSetup.backupCodesCount = data.codes?.length || 0
    showRegenerateModal.value = false
    regeneratePassword.value = ''
    twoFactorSetup.showBackupCodes = true
    alert('Новые резервные коды сгенерированы!')
  } catch (error: any) {
    console.error('Error regenerating backup codes:', error)
    if (error.response?.data?.error) {
      regenerateError.value = error.response.data.error
    }
  }
}

function copyBackupCodes() {
  const codes = twoFactorSetup.backupCodes.join('\n')
  navigator.clipboard.writeText(codes).then(() => {
    alert('Коды скопированы в буфер обмена')
  }).catch(() => {
    alert('Ошибка копирования')
  })
}

async function showSecurityLog() {
  if (twoFactorSetup.securityLog.length === 0) {
    await loadSecurityLog()
  }
}

async function loadSecurityLog() {
  try {
    const data = await settingsApi.getTwoFactorSecurityLog()
    twoFactorSetup.securityLog = data.logs || []
  } catch (error: any) {
    console.error('Error loading security log:', error)
  }
}

async function disableTwoFactor() {
  const password = prompt('Введите ваш пароль для отключения 2FA:')
  if (!password) return

  try {
    await settingsApi.disableTwoFactor(password)
    formData.twoFactorEnabled = false
    showDisableModal.value = false
    disablePassword.value = ''
    alert('2FA успешно отключена')
    await loadSettings()
  } catch (error: any) {
    console.error('Error disabling 2FA:', error)
    if (error.response?.data?.error) {
      alert(error.response.data.error)
    } else {
      alert('Ошибка при отключении 2FA')
    }
  }
}

function formatLogAction(action: string) {
  const actions: Record<string, string> = {
    '2fa_setup_started': 'Начало настройки',
    '2fa_enabled': 'Включение 2FA',
    '2fa_disabled': 'Отключение 2FA',
    '2fa_backup_code_used': 'Использование резервного кода',
    '2fa_backup_codes_regenerated': 'Генерация новых кодов',
    '2fa_settings_updated': 'Обновление настроек'
  }
  return actions[action] || action
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function closeModal() {
  errors.value = {}
  nicknameAvailable.value = null
  passwordErrors.value = {}
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  props.onClose()
}

// Password strength check
function checkPasswordStrength(password: string) {
  passwordRequirements.minLength = password.length >= 8
  passwordRequirements.hasLetter = /[a-zA-Z]/.test(password)
  passwordRequirements.hasDigit = /[0-9]/.test(password)

  let strength = 0
  if (passwordRequirements.minLength) strength += 1
  if (passwordRequirements.hasLetter) strength += 1
  if (passwordRequirements.hasDigit) strength += 1
  if (password.length >= 12) strength += 1
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) strength += 1

  passwordStrength.value = strength

  return strength
}

function getStrengthLabel(strength: number): string {
  if (strength <= 1) return 'Слабый'
  if (strength <= 2) return 'Средний'
  if (strength <= 3) return 'Хороший'
  if (strength <= 4) return 'Сильный'
  return 'Отличный'
}

function getStrengthColor(strength: number): string {
  if (strength <= 1) return '#ef4444'
  if (strength <= 2) return '#f59e0b'
  if (strength <= 3) return '#10b981'
  if (strength <= 4) return '#3b82f6'
  return '#8b5cf6'
}

// Change password
async function changePassword() {
  if (isChangingPassword.value) return

  // Validation
  passwordErrors.value = {}

  if (!passwordForm.oldPassword) {
    passwordErrors.value.oldPassword = 'Введите текущий пароль'
  }

  if (!passwordForm.newPassword) {
    passwordErrors.value.newPassword = 'Введите новый пароль'
  } else if (passwordForm.newPassword.length < 8) {
    passwordErrors.value.newPassword = 'Пароль должен содержать минимум 8 символов'
  } else if (!passwordRequirements.hasLetter) {
    passwordErrors.value.newPassword = 'Пароль должен содержать минимум одну букву'
  } else if (!passwordRequirements.hasDigit) {
    passwordErrors.value.newPassword = 'Пароль должен содержать минимум одну цифру'
  }

  if (!passwordForm.confirmPassword) {
    passwordErrors.value.confirmPassword = 'Подтвердите новый пароль'
  } else if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordErrors.value.confirmPassword = 'Пароли не совпадают'
  }

  if (passwordForm.oldPassword === passwordForm.newPassword) {
    passwordErrors.value.newPassword = 'Новый пароль должен отличаться от текущего'
  }

  if (Object.keys(passwordErrors.value).length > 0) {
    return
  }

  isChangingPassword.value = true

  try {
    await settingsApi.changePassword({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword,
      confirm_password: passwordForm.confirmPassword,
    })

    alert('Пароль успешно изменен! Все другие сессии были завершены.')

    // Clear form
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    passwordStrength.value = 0

    // Close modal
    closeModal()
  } catch (error: any) {
    console.error('Error changing password:', error)
    if (error.response?.data) {
      const apiErrors = error.response.data
      Object.keys(apiErrors).forEach((key) => {
        passwordErrors.value[key] = Array.isArray(apiErrors[key]) ? apiErrors[key][0] : apiErrors[key]
      })
    } else {
      alert('Ошибка при смене пароля')
    }
  } finally {
    isChangingPassword.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: var(--color-background-surface);
  border-radius: var(--radius-modal);
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-modal);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--color-divider);
  flex-shrink: 0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--radius-button);
  transition: background-color 0.15s ease;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: var(--color-background-active);
  color: var(--color-text);
}

/* Tabs */
.tabs {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1.5rem 0;
  border-right: 1px solid var(--color-divider);
  flex-shrink: 0;
  width: 200px;
  background: var(--color-background);
}

.tab-btn {
  padding: 0.75rem 1.25rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-button);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  transition: all 0.15s ease;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-left: 3px solid transparent;
}

.tab-btn:hover {
  background: var(--color-background-active);
  color: var(--color-text);
}

.tab-btn.active {
  background: var(--color-background-active);
  color: var(--color-accent);
  border-left-color: var(--color-accent);
}

/* Modal Body */
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: row;
  min-height: 500px;
}

.tab-content {
  flex: 1;
  min-height: 400px;
  overflow-y: auto;
  padding-left: 1rem;
}

/* Form Elements */
.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.required {
  color: var(--color-accent-pink);
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: var(--radius-button);
  font-size: 0.875rem;
  background: var(--color-background);
  color: var(--color-text);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.field-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: 0.25rem;
}

.error-message {
  font-size: 0.75rem;
  color: var(--color-accent-pink);
  margin-top: 0.25rem;
}

.success-message {
  font-size: 0.75rem;
  color: var(--color-accent-teal);
  margin-top: 0.25rem;
}

/* Section Title */
.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 2rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-divider);
}

/* Toggle Switch */
.toggle-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  user-select: none;
}

.toggle-label input[type="checkbox"] {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--color-background);
  border: 1px solid var(--color-divider);
  border-radius: 12px;
  transition: all 0.15s ease;
}

.toggle-slider::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: var(--color-text-secondary);
  border-radius: 50%;
  transition: all 0.15s ease;
}

.toggle-label input:checked + .toggle-slider {
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.toggle-label input:checked + .toggle-slider::before {
  left: 22px;
  background: var(--color-text);
}

/* Avatar Upload */
.avatar-group {
  text-align: center;
}

.avatar-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.current-avatar {
  position: relative;
}

.avatar-preview,
.avatar-placeholder {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  background: var(--color-accent);
  color: var(--color-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: bold;
}

.upload-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.btn-upload,
.btn-delete-avatar {
  padding: 0.5rem 1rem;
  background: var(--color-accent);
  color: var(--color-text);
  border: none;
  border-radius: var(--radius-button);
  cursor: pointer;
  font-size: 0.875rem;
  transition: background-color 0.15s ease;
}

.btn-upload:hover,
.btn-delete-avatar:hover {
  background: var(--color-accent-hover);
}

.btn-delete-avatar {
  background: var(--color-accent-pink);
}

.upload-hint {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* Links */
.links-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.link-input {
  display: flex;
  align-items: center;
}

.link-prefix {
  padding: 0.75rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-right: none;
  border-radius: var(--radius-button) 0 0 var(--radius-button);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  white-space: nowrap;
}

.link-field {
  border-radius: 0 var(--radius-button) var(--radius-button) 0;
  border-left: none;
}

/* Genres */
.genres-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.5rem;
}

.genre-checkbox {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 0.875rem;
  padding: 0.5rem;
  border-radius: var(--radius-button);
  transition: background-color 0.15s ease;
  color: var(--color-text-secondary);
}

.genre-checkbox:hover {
  background: var(--color-background);
}

.genre-checkbox input {
  margin-right: 0.5rem;
}

/* Theme Options */
.theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
}

.theme-btn {
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 2px solid var(--color-divider);
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--color-text);
}

.theme-btn:hover {
  border-color: var(--color-accent);
}

.theme-btn.active {
  border-color: var(--color-accent);
  background: var(--color-background-active);
}

.theme-icon {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 0.25rem;
}

/* Color Picker */
.color-picker {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.color-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 3px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}

.color-btn:hover {
  transform: scale(1.1);
}

.color-btn.active {
  border-color: var(--color-text);
}

/* Radio Group */
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.radio-label input[type="radio"] {
  width: 18px;
  height: 18px;
  accent-color: var(--color-accent);
}

/* Time Range */
.time-range {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

/* Password Change */
.password-section {
  max-width: 500px;
  margin: 0 auto;
}

.password-warning {
  background: var(--color-background-active);
  border-left: 4px solid var(--color-accent-orange);
  padding: 1rem;
  border-radius: var(--radius-button);
  margin-bottom: 1.5rem;
  color: var(--color-text);
  line-height: 1.5;
}

.password-input-wrapper {
  position: relative;
}

.password-input-wrapper .form-input {
  padding-right: 3rem;
}

.password-strength {
  margin-top: 1rem;
}

.strength-bar {
  height: 6px;
  background: var(--color-background);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
}

.strength-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.password-requirements {
  background: var(--color-background);
  padding: 1rem;
  border-radius: var(--radius-button);
  margin-top: 1rem;
}

.requirements-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  margin: 0 0 0.75rem 0;
}

.password-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.password-requirements li {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  margin-bottom: 0.5rem;
  transition: color 0.2s ease;
}

.password-requirements li.met {
  color: var(--color-accent-teal);
}

.password-actions {
  margin-top: 1.5rem;
  display: flex;
  gap: 1rem;
}

.password-tips {
  margin-top: 2rem;
  padding: 1rem;
  background: var(--color-background-active);
  border-radius: var(--radius-button);
}

.password-tips h5 {
  margin: 0 0 0.75rem 0;
  color: var(--color-text);
  font-size: 0.875rem;
}

.password-tips ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.password-tips li {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
  padding-left: 1.5rem;
  position: relative;
}

.password-tips li::before {
  content: '<SakuraIcon name="lightbulb" />';
  position: absolute;
  left: 0;
}

/* Two Factor */
.two-factor-status {
  text-align: center;
  margin-bottom: 1.5rem;
}

.status-badge {
  display: inline-block;
  padding: 0.5rem 1.5rem;
  border-radius: var(--radius-button);
  font-weight: 600;
  font-size: 1rem;
}

.status-badge.enabled {
  background: var(--color-accent-teal);
  color: var(--color-text);
}

.status-badge.disabled {
  background: var(--color-background-active);
  color: var(--color-text-secondary);
}

.two-factor-setup {
  background: var(--color-background);
  padding: 1.5rem;
  border-radius: var(--radius-button);
}

.two-factor-setup h5 {
  margin: 1.5rem 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
}

.two-factor-setup h5:first-child {
  margin-top: 0;
}

.qr-container {
  text-align: center;
  margin: 1.5rem 0;
}

.qr-code {
  width: 200px;
  height: 200px;
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-button);
  display: inline-block;
}

.secret-code {
  display: block;
  background: var(--color-background-active);
  padding: 0.75rem;
  border-radius: var(--radius-button);
  font-family: monospace;
  font-size: 0.875rem;
  word-break: break-all;
  margin: 1rem 0;
}

.code-input {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin: 1.5rem 0;
}

.code-field {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-button);
  font-size: 1.25rem;
  text-align: center;
  font-family: monospace;
  max-width: 150px;
}

.two-factor-settings {
  padding: 1rem;
  background: var(--color-background);
  border-radius: var(--radius-button);
}

/* Backup Codes */
.backup-codes-section {
  margin: 1.5rem 0;
}

.backup-codes-section h5 {
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.backup-codes-list {
  background: var(--color-background-active);
  padding: 1rem;
  border-radius: var(--radius-button);
  margin: 1rem 0;
  font-family: monospace;
  font-size: 0.875rem;
}

.backup-code-item {
  margin-bottom: 0.5rem;
}

.backup-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.backup-actions .btn-secondary {
  font-size: 0.75rem;
  padding: 0.5rem 0.75rem;
}

.backup-actions .btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Security Log */
.security-log-section {
  margin: 1.5rem 0;
}

.security-log-section h5 {
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.security-log-list {
  background: var(--color-background-active);
  padding: 1rem;
  border-radius: var(--radius-button);
  margin: 1rem 0;
}

.log-item {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-divider);
}

.log-item:last-child {
  border-bottom: none;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-action {
  font-weight: 500;
  font-size: 0.875rem;
}

.log-date {
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
}

/* Small Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.small-modal {
  background: var(--color-background-surface);
  padding: 1.5rem;
  border-radius: var(--radius-modal);
  max-width: 400px;
  width: 100%;
  border: 1px solid var(--color-divider);
}

.small-modal h4 {
  margin: 0 0 1rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

/* Buttons */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid var(--color-divider);
  flex-shrink: 0;
}

.btn-secondary,
.btn-primary,
.btn-danger {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: var(--radius-button);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s ease;
}

.btn-secondary {
  background: var(--color-background);
  color: var(--color-text);
  border: 1px solid var(--color-divider);
}

.btn-secondary:hover {
  background: var(--color-background-active);
}

.btn-primary {
  background: var(--color-accent);
  color: var(--color-text);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.btn-danger {
  background: var(--color-accent-pink);
  color: var(--color-text);
}

.btn-danger:hover {
  background: var(--color-accent-pink-hover);
}

.btn-secondary:disabled,
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Loading */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--color-text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .modal-content {
    max-height: 100vh;
    height: 100vh;
    border-radius: 0;
  }

  .modal-header,
  .modal-footer {
    padding: 1rem;
  }

  .modal-body {
    padding: 1rem;
    flex-direction: column;
  }

  .tabs {
    flex-direction: row;
    padding: 0.5rem;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-divider);
    overflow-x: auto;
  }

  .tab-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.75rem;
    border-left: none;
    border-bottom: 3px solid transparent;
  }

  .tab-btn.active {
    border-left: none;
    border-bottom-color: var(--color-accent);
  }

  .tab-content {
    padding-left: 0;
  }

  .theme-options {
    grid-template-columns: 1fr 1fr;
  }

  .time-range {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
  }

  .btn-secondary,
  .btn-primary,
  .btn-danger {
    width: 100%;
  }
}
</style>
