# ── Stage 1 : Build les frontends (Node.js) ──────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Build frontend-mobile
COPY frontend-mobile/package.json frontend-mobile/package-lock.json* frontend-mobile/
RUN cd frontend-mobile && npm install
COPY frontend-mobile/ frontend-mobile/
RUN cd frontend-mobile && npm run build

# Build frontend-admin
COPY frontend-admin/package.json frontend-admin/package-lock.json* frontend-admin/
RUN cd frontend-admin && npm install
COPY frontend-admin/ frontend-admin/
RUN cd frontend-admin && npm run build

# ── Stage 2 : Backend Python + frontends intégrés ────────────
FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances Python
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copier le backend
COPY backend/ backend/

# Copier les frontends buildés depuis le stage 1
# Le backend cherche les dist/ via BASE_DIR.parent (= /app)
COPY --from=frontend-builder /app/frontend-mobile/dist frontend-mobile/dist/
COPY --from=frontend-builder /app/frontend-admin/dist frontend-admin/dist/

# Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1
ENV DEPLOY_MODE=demo
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
