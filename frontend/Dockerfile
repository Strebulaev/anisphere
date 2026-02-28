# Этап 1: Сборка
FROM node:20-bullseye as builder

WORKDIR /app

# Копируем package файлы
COPY package*.json ./
COPY .npmrc ./

# Устанавливаем зависимости
RUN npm config set registry https://registry.npmmirror.com && \
    npm ci --silent --no-audit --no-fund --legacy-peer-deps

# Копируем исходники
COPY . .

# Собираем проект
RUN npm run build

# Этап 2: Продакшен
FROM nginx:alpine

# Копируем собранные файлы
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем конфиг nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Копируем скрипт для проверки здоровья
RUN echo '#!/bin/sh\necho "OK"' > /usr/share/nginx/html/health.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]