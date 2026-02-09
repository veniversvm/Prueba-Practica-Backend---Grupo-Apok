#!/bin/bash
#entrypoint-prod.sh - Versión optimizada para producción con Uvicorn y ASGI
set -e

echo "🚀 MODO PRODUCCIÓN - Uvicorn + ASGI"

# Validar variables de entorno críticas
if [ -z "$SECRET_KEY" ] && [ -z "$DB_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY o DB_KEY no está definida"
    exit 1
fi

# Esperar a PgBouncer
echo "⏳ Verificando PgBouncer..."
while ! nc -z pgbouncer 5432; do
    sleep 0.5
done
echo "✅ PgBouncer disponible"

# Aplicar migraciones
echo "🔄 Aplicando migraciones..."
python manage.py migrate --noinput

# Seeders condicionales
if [ "$RUN_SEEDERS_IN_PROD" = "true" ] || [ "$RUN_SEEDERS_IN_PROD" = "True" ]; then
    echo "🌱 Ejecutando seeders en producción (RUN_SEEDERS_IN_PROD=true)..."
    python manage.py setup_sudo
    python manage.py seed_users
    python manage.py seed_nodes
else
    echo "⏭️  Saltando seeders en producción (set RUN_SEEDERS_IN_PROD=true para ejecutarlos)"
fi

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Comprobar integridad de la base de datos
python manage.py check --deploy

echo "🔧 Configurando Uvicorn..."

# Número de workers
WORKERS=${UVICORN_WORKERS:-2}
echo "👥 Usando $WORKERS workers"

# Log level
LOG_LEVEL=${UVICORN_LOG_LEVEL:-"info"}

echo "🚀 Iniciando Uvicorn con $WORKERS workers..."
exec uvicorn app_nodos.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers $WORKERS \
    --log-level $LOG_LEVEL \
    --proxy-headers \
    --forwarded-allow-ips "*" \
    --timeout-keep-alive 30