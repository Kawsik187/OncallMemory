# ==========================================
# Stage 1: Build Frontend (React + Vite + Tailwind)
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend package manifests first for caching
COPY frontend/package*.json ./
RUN npm ci || npm install

# Copy frontend source and build production bundle
COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Python Backend (FastAPI + Uvicorn)
# ==========================================
FROM python:3.11-slim AS runner

# Environment variables for Python runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Install curl for container health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend application source code
COPY backend/ ./backend/

# Copy built frontend assets from Stage 1 into /app/frontend/dist
# FastAPI mounts /app/frontend/dist to serve the React UI at root /
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set working directory to backend
WORKDIR /app/backend

# Expose FastAPI application port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
