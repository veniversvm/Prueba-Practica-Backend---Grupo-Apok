#!/bin/bash
#entrypoint.sh - Versión común para desarrollo y producción
# 1. Esperar a Postgres
echo "Esperando a Postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Postgres está arriba."

# 2. Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# 3. Configurar el usuario SUDO inicial (seguridad y automatización)
echo "Configurando usuario SUDO desde .env..."
python manage.py setup_sudo

# 4. Poblar con usuarios de prueba (ADMINs y USERs)
echo "Poblando usuarios de prueba..."
python manage.py seed_users

# 5. Generar el árbol de nodos con auditoría
echo "Generando árbol de nodos con autoría..."
python manage.py seed_nodes

# 6. Iniciar el servidor
echo "Iniciando servidor Django..."
exec "$@"