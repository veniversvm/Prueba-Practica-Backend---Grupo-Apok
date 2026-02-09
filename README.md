
# 🌳 Sistema de Gestión de Árboles Jerárquicos - Versión Técnica Detallada

## 📋 Descripción

API REST completa para gestión de estructuras jerárquicas de árboles con autenticación JWT, roles de usuario, internacionalización multi-idioma, optimización de conexiones mediante PgBouncer y cache estratégica.

---

## 🚀 Tecnologías Utilizadas - Detallado

### **Backend & Framework**

- **Django 6.0.2** - Framework web Python con soporte asíncrono
- **Django REST Framework 3.16.1** - Construcción de APIs RESTful con serialización avanzada
- **TOML para dependencias** - Gestión moderna de paquetes con `pyproject.toml`

### **Base de Datos & Optimización**

- **PostgreSQL 18 Alpine** - Versión ligera y eficiente (postgres:18-alpine)
- **PgBouncer** - Connection pooling para alta concurrencia (imagen: edoburu/pgbouncer)
- **Django Caching** - Cache integrado para reducir conexiones a base de datos
- **Configuración PostgreSQL** - Archivo `pg_hba.conf` personalizado para red Docker

### **Autenticación & Seguridad**

- **Simple JWT 5.5.1** - Autenticación con JSON Web Tokens robusta
- **SCRAM-SHA-256** - Autenticación moderna en PgBouncer
- **Custom Authentication Backend** - Login dual (email/username)
- **Django CORS Headers** - Control de acceso entre dominios seguro

### **Internacionalización**

- **num2words 0.5.14** - Conversión de números a texto en múltiples idiomas
- **pytz 2025.2** - Manejo completo de zonas horarias
- **Custom Middleware** - Procesamiento dinámico de headers de idioma y zona horaria

### **Documentación & API**

- **DRF Spectacular 0.29.0** - Generación automática de documentación OpenAPI 3.0
- **Swagger UI** - Interface interactiva para explorar la API
- **Markdown 3.10.1** - Soporte para documentación enriquecida

### **Contenerización & Orquestación**

- **Docker Compose 2.20+** - Orquestación multi-servicio con dependencias controladas
- **Entrypoint optimizado** - Script de inicialización inteligente
- **Network Bridge** - Red aislada `backend_net` para comunicación segura

### **Testing & Calidad**

- **Django Test Framework** - Suite completa de pruebas unitarias
- **Coverage.py** - Análisis de cobertura de código exhaustivo

---

## 🏗️ Arquitectura del Sistema - Infraestructura Docker

### **Servicios Configurados**

| Servicio             | Imagen/Config      | Puerto         | Propósito              | Dependencias |
| -------------------- | ------------------ | -------------- | ----------------------- | ------------ |
| **PostgreSQL** | postgres:18-alpine | 5432 (interno) | Base de datos principal | -            |
| **PgBouncer**  | edoburu/pgbouncer  | 6432 (host)    | Pool de conexiones      | PostgreSQL   |
| **Django App** | Custom Dockerfile  | 8000           | Aplicación principal   | PgBouncer    |

### **Flujo de Conexiones Optimizado**

```
Aplicación Django → PgBouncer (Pool: 20 conexiones) → PostgreSQL
```

- **Modo transacción**: Configuración óptima para Django
- **Max conexiones**: 100 clientes, pool de 20
- **Cache Django**: Reduce necesidad de nuevas conexiones

### **Configuración PostgreSQL Personalizada**

```sql
# postgres/pg_hba.conf
host    tree_db     tree_user    172.20.0.0/16     md5
host    all         all          127.0.0.1/32      md5
host    all         all          ::1/128           md5
```

- **Red específica**: Solo permite conexiones desde la red Docker interna
- **Seguridad**: No expone PostgreSQL directamente al host

---

## 🔄 Proceso de Inicialización (Entrypoint.sh)

### **Fases de Arranque**

1. **Espera para PostgreSQL** (Health Check)

   ```bash
   while ! nc -z db 5432; do sleep 0.1; done
   ```
2. **Migraciones de Base de Datos**

   ```bash
   python manage.py migrate --noinput
   ```
3. **Configuración de Usuario SUDO**

   ```bash
   python manage.py setup_sudo  # Creado desde variables .env
   ```
4. **Población de Datos de Prueba**

   ```bash
   python manage.py seed_users   # Usuarios ADMIN y USER
   python manage.py seed_nodes   # Árbol jerárquico con auditoría
   ```
5. **Inicio del Servidor Django**

   ```bash
   exec "$@"  # Ejecuta el comando principal (runserver/gunicorn)
   ```

---

## ⚡ Optimizaciones de Performance Específicas

### **Connection Pooling con PgBouncer**

```yaml
# Configuración en docker-compose.yml
pgbouncer:
  environment:
    - POOL_MODE=transaction  # CRÍTICO para Django
    - MAX_CLIENT_CONN=100
    - DEFAULT_POOL_SIZE=20
    - AUTH_TYPE=scram-sha-256
```

- **Evita sobrecarga**: Reutiliza conexiones PostgreSQL
- **Alta concurrencia**: Soporta 100+ usuarios simultáneos
- **Autenticación segura**: SCRAM-SHA-256 moderno

### **Estrategia de Cache Django**

- **Cache de 180 segundos** en endpoints de listado
- **Reducción de queries** con `select_related` y `prefetch_related`
- **Validación temprana** para evitar procesamiento innecesario

### **Configuración de Red Aislada**

```yaml
networks:
  backend_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16  # Subnet específica
```

- **Seguridad**: Contenedores aislados del host
- **Rendimiento**: Comunicación interna optimizada

---

## 📦 Gestión de Dependencias Moderna

### **Archivo `pyproject.toml`**

```toml
[project]
name = "tree"
version = "1.0.0"
description = "Django project running fully on Docker"
requires-python = ">=3.12"

dependencies = [
    "Django==6.0.2",
    "django-filter==25.2",
    "djangorestframework==3.16.1",
    "Markdown==3.10.1",
    "psycopg2-binary==2.9.11",
    "djangorestframework-simplejwt==5.5.1",
    "drf-spectacular==0.29.0",
    "num2words==0.5.14",
    "pytz==2025.2",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

### **Ventajas de TOML sobre requirements.txt**

- **Metadatos estructurados**: Versión, descripción, Python mínimo
- **Build system integrado**: Configuración de construcción incluida
- **Futuro-proof**: Estándar PEP 621 moderno

---

## 🛡️ Características de Seguridad

### **Por Capas de Infraestructura**

1. **Red Aislada**: `backend_net` con subnet específica
2. **PgBouncer como firewall**: PostgreSQL no expuesto directamente
3. **Autenticación JWT**: Tokens firmados con expiración
4. **Configuración PostgreSQL**: Solo conexiones desde red interna

### **Autenticación de Base de Datos**

- **Django → PgBouncer**: Credenciales desde .env
- **PgBouncer → PostgreSQL**: Autenticación MD5 (configuración pg_hba.conf)
- **Encriptación**: SCRAM-SHA-256 para autenticación segura

---

## 🔧 Flujo de Desarrollo y Deployment

### **Desarrollo Local**

```bash
# Iniciar todos los servicios
docker-compose up

# Acceder a la aplicación
http://localhost:8000/api/docs/

# Conectar a PostgreSQL vía PgBouncer
psql -h localhost -p 6432 -U tree_user tree_db
```

### **Comandos Útiles**

```bash
# Ver logs específicos
docker-compose logs -f web
docker-compose logs -f pgbouncer

# Ejecutar comandos Django
docker-compose exec web python manage.py shell

# Reconstruir servicios
docker-compose up --build
```

---

## 📊 Métricas y Monitoreo

### **PgBouncer Statistics**

```sql
-- Conectar a PgBouncer (puerto 6432)
SHOW POOLS;
SHOW STATS;
SHOW CLIENTS;
```

### **Indicadores Clave**

- **Pool usage**: Conexiones activas/inactivas
- **Query timing**: Tiempos promedio de consulta
- **Cache hit rate**: Efectividad de cache Django
- **Connection churn**: Nuevas conexiones vs reutilizadas

---

## 🚦 Estado del Sistema

**✅ Producción Optimizada**

- [X] **Infraestructura Docker completa** con 3 servicios coordinados
- [X] **Connection pooling** con PgBouncer para alta concurrencia
- [X] **Inicialización automática** con entrypoint inteligente
- [X] **Configuración PostgreSQL** segura y aislada
- [X] **Gestión moderna de dependencias** con TOML
- [X] **Red aislada** con subnet específica para seguridad
- [X] **Health checks** para verificación de servicios

---

## ⚠️ Consideraciones Técnicas Importantes

### **Para Producción**

1. **Variables de entorno**: Todas las credenciales via .env
2. **Backups PostgreSQL**: Volume `postgres_data` persistente
3. **Monitoring PgBouncer**: Estadísticas críticas para escalabilidad
4. **Escalabilidad**: Aumentar `DEFAULT_POOL_SIZE` según carga

### **Configuraciones Críticas**

```yaml
# NO cambiar sin entender implicaciones
POOL_MODE: transaction  # Django requiere este modo
AUTH_TYPE: scram-sha-256  # Autenticación moderna
DB_HOST: pgbouncer  # Django debe apuntar a PgBouncer, no a DB directo
```

---

## 🔄 Workflow de Actualización

1. **Actualizar dependencias** en `pyproject.toml`
2. **Reconstruir imagen** de Django
3. **Mantener volumen** de PostgreSQL para persistencia
4. **Verificar configuración** de PgBouncer
5. **Testear conexiones** en entorno staging

---

**Versión Técnica**: 1.0.0
**Última actualización**: Febrero 2026
**Arquitectura**: Microservicios Docker con optimización PgBouncer
**Soporte**: Red aislada + Connection Pooling + Cache Estratégico
