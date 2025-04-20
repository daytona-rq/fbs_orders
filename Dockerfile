# Этап сборки (builder)
FROM python:3.11.9-slim-bookworm@sha256:c677c6b2c280d6a6a0d7d6e9f3b3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3 as builder

# 1. Установка только необходимых зависимостей для сборки
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Создание изолированного виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Установка зависимостей с обновлением pip
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Финальный образ (runtime)
FROM python:3.11.9-slim-bookworm@sha256:c677c6b2c280d6a6a0d7d6e9f3b3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3

# 4. Обновление системных пакетов
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 5. Копирование только виртуального окружения
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 6. Настройка рабочей директории
WORKDIR /app

# 7. Копирование только необходимых файлов
COPY --chown=appuser:appuser src/ ./src
COPY --chown=appuser:appuser configs/ ./configs

# 8. Настройки безопасности
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 9. Создание непривилегированного пользователя
RUN groupadd -r appuser && \
    useradd --no-log-init -r -g appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# 10. Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]