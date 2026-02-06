# Usamos una imagen slim para reducir tamaño y superficie de ataque
FROM python:3.14-slim-bookworm


# Evita que Python genere archivos .pyc y fuerza salida std sin buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app_nodos

# Instalar dependencias del sistema necesarias para compilar psycopg2 y otras libs
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY pyproject.toml .
RUN pip install --upgrade pip \
    && pip install .


# Copiar el proyecto
COPY app_nodos/ /app_nodos/

# Exponer puerto (informativo)
EXPOSE 8000

COPY ./docker/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Comando por defecto (lo sobreescribiremos en compose o entrypoint)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]