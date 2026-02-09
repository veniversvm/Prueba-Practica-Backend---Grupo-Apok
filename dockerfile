# ===================== ETAPA DE CONSTRUCCIÓN =====================
FROM python:3.14-slim-bookworm AS builder

# Variables para optimización
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY pyproject.toml .

# Instalar dependencias en directorio aislado (SIN --user)
RUN pip install --no-warn-script-location \
    --prefix=/install \
    .

# ===================== ETAPA DE DESARROLLO =====================
FROM python:3.14-slim-bookworm AS development

WORKDIR /app_nodos

# Instalar dependencias mínimas para desarrollo
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas desde builder
COPY --from=builder /install /usr/local

# Copiar aplicación
COPY app_nodos/ /app_nodos/

# Script de entrypoint para desarrollo
COPY ./docker/django/entrypoint-dev.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app_nodos
USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]

# ===================== ETAPA DE PRODUCCIÓN =====================
FROM python:3.14-slim-bookworm AS production

WORKDIR /app_nodos

# Instalar solo lo esencial para producción
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas desde builder
COPY --from=builder /install /usr/local

# Copiar aplicación
COPY app_nodos/ /app_nodos/

# Script de entrypoint para producción (CORREGIR RUTA)
COPY ./docker/django/entrypoint-prod.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh 

# Crear directorio para logs
RUN mkdir -p /app_nodos/logs

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app_nodos
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
# NO necesitas CMD aquí, está en el entrypoint-prod.sh