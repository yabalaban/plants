# Stage 1: Build frontend
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend runtime
FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 -s /bin/bash app

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --no-dev --frozen

COPY backend/app/ ./app/

COPY --from=frontend /build/build /app/frontend/build

RUN mkdir -p /data/db /data/photos /data/config && chown -R app:app /data

ENV PLANTS_DB_PATH=/data/db/plants.db
ENV PLANTS_PHOTO_DIR=/data/photos
ENV PLANTS_SETTINGS_PATH=/data/config/settings.json
ENV PLANTS_FRONTEND_DIR=/app/frontend/build
ENV CLAUDE_CLI_TIMEOUT=120
ENV UV_NO_CACHE=1

USER app
EXPOSE 8472

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -sf http://localhost:8472/api/health || exit 1

CMD ["uv", "run", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8472"]
