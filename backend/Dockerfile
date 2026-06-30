FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект (все файлы из backend/)
COPY . .

# Проверяем структуру
RUN echo "=== FILES IN /APP ===" && ls -la && \
    echo "=== CONFIG DIR ===" && ls -la config/ || echo "No config dir"

EXPOSE 8000

# Используем daphne для ASGI (WebSocket + HTTP)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]