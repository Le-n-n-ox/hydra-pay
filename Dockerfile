# Hydra Pay cloud server: dashboard, M-Pesa, WhatsApp, SMS and USSD.
# Card taps arrive from bridge.py on the laptop (READER=bridge). See docs/CLOUD_DEPLOY.md.

# ---- 1. build the React frontend into /app/static ----
FROM node:22-slim AS web
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- 2. Python server ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    READER=bridge \
    DATA_DIR=/data \
    PORT=8000 \
    TZ=EAT-3
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py settings.example.json ./
COPY telco ./telco
COPY --from=web /app/static ./static
RUN mkdir -p /data
EXPOSE 8000
CMD ["python", "dashboard.py", "--no-browser"]
