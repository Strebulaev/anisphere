# -*- coding: utf-8 -*-

# Основные настройки
family = 'wikipedia'
mylang = 'ru'

# ТВОЙ ЛОГИН И ПАРОЛЬ
usernames['wikipedia']['ru'] = 'Kai3637'

# Пароль можно сохранить в файле (безопаснее, чем в open text)
# Создай файл password.py с содержимым:
password = '84UVpz:2pJ*qkcf'
# from password import password  # Раскомментируй, если создашь password.py

# Или можно указать пароль напрямую (но так менее безопасно)
# password = '84UVpz:2pJ*qkcf'

# Настройки аутентификации
authenticate = {}  # Должен быть словарь, а не список

# Технические настройки
console_encoding = 'utf-8'
use_api_login = True  # Используем API для логина
user_agent_description = 'AnimeStudioCollector/1.0 (https://github.com/Kai3637/collector)'

# Настройки скорости (важно для избежания блокировок)
maxthrottle = 10  # максимум запросов в минуту
minthrottle = 1   # минимум задержки между запросами
put_throttle = 1  # задержка между записями