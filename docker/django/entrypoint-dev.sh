#!/bin/bash
# entrypoint-dev.sh - Versión optimizada para desarrollo con Django Development Server
set -e

echo "🛠️  MODO DESARROLLO - Django Development Server"

# Esperar a PostgreSQL
echo "⏳ Esperando a PostgreSQL..."
while ! nc -z db 5432; do
    sleep 0.5
done
echo "✅ PostgreSQL listo"

# Esperar a PgBouncer
echo "⏳ Esperando a PgBouncer..."
while ! nc -z pgbouncer 5432; do
    sleep 0.5
done
echo "✅ PgBouncer listo"

# Aplicar migraciones
echo "🔄 Aplicando migraciones..."
python manage.py migrate --noinput

# Cargar datos iniciales (solo si no existen)
if [ ! -f /tmp/.initial_data_loaded ]; then
    echo "📦 Cargando datos iniciales..."
    python manage.py setup_sudo
    python manage.py seed_users
    python manage.py seed_nodes
    touch /tmp/.initial_data_loaded
fi

# Ejecutar comandos adicionales si existen
if [ -f /app_nodos/scripts/dev-init.sh ]; then
    bash /app_nodos/scripts/dev-init.sh
fi

echo "🚀 Iniciando servidor de desarrollo..."
exec "$@"