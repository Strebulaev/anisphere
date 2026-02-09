FROM node:20-bullseye

WORKDIR /app

# Копируем .npmrc и package файлы
COPY .npmrc package*.json ./

# Используем зеркало npm для России/Китая и увеличиваем retry
RUN npm config set registry https://registry.npmmirror.com && \
    npm install --silent --no-audit --no-fund --legacy-peer-deps --timeout=180000 || \
    npm install --silent --no-audit --no-fund --legacy-peer-deps --timeout=180000 || \
    npm install --silent --no-audit --no-fund --legacy-peer-deps --timeout=180000

# Копируем остальные файлы
COPY . .

EXPOSE 5173

# Явно указываем host в команде
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]