FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libc6-dev \
    adduser \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system celeryuser && \
    adduser --system --ingroup celeryuser celeryuser && \
    mkdir -p /var/lib/celery && \
    chown -R celeryuser:celeryuser /var/lib/celery

WORKDIR /app

RUN chown -R celeryuser:celeryuser /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER celeryuser:celeryuser