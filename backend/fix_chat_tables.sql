-- ============================================
-- Исправление таблиц чатов
-- Выполнить на сервере: mysql -u root -p animecore < fix_chat_tables.sql
-- ============================================

-- ============================================
-- Таблица: social_chatwallpaper
-- Добавляем колонки для паттернов
-- ============================================

ALTER TABLE social_chatwallpaper 
    ADD COLUMN pattern_type VARCHAR(20) DEFAULT '' NOT NULL AFTER wallpaper_color2,
    ADD COLUMN pattern_color VARCHAR(7) DEFAULT '' NOT NULL AFTER pattern_type,
    ADD COLUMN pattern_opacity INT DEFAULT 20 NOT NULL AFTER pattern_color;

-- ============================================
-- Таблица: social_privatechatsettings
-- Добавляем колонки для уведомлений и вибрации
-- ============================================

ALTER TABLE social_privatechatsettings 
    ADD COLUMN notification_sound VARCHAR(50) DEFAULT 'default' NOT NULL AFTER sound_enabled,
    ADD COLUMN vibration_enabled TINYINT(1) DEFAULT 1 NOT NULL AFTER notification_sound,
    ADD COLUMN vibration_type VARCHAR(20) DEFAULT 'default' NOT NULL AFTER vibration_enabled,
    ADD COLUMN show_popup TINYINT(1) DEFAULT 1 NOT NULL AFTER show_preview;

-- ============================================
-- Отмечаем миграцию как применённую
-- ============================================

INSERT INTO django_migrations (app, name, applied) 
VALUES ('social', '0013_chat_settings_full', NOW())
ON DUPLICATE KEY UPDATE applied = NOW();
