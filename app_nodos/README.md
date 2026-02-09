# 🌳 Sistema de Gestión de Árboles Jerárquicos

## 📋 Descripción del Proyecto

**Sistema API REST** para la gestión de árboles de nodos jerárquicos con soporte multi-idioma, *timezone* dinámico, seguridad basada en roles y auditoría completa. Este proyecto implementa una prueba técnica para desarrolladores *backend senior*.

---

## 📚 Documentación de Módulos

### **Módulos Principales**

| Módulo                | Descripción                                                                          | Documentación                      |
| :--------------------- | :------------------------------------------------------------------------------------ | :---------------------------------- |
| **🔒 `users`** | Gestión de Usuarios y Autenticación JWT con roles jerárquicos (SUDO/ADMIN/USER)    | [Ver README completo](users/README.md) |
| **📂 `nodes`** | Nodos Jerárquicos con internacionalización, control de profundidad y zonas horarias | [Ver README completo](nodes/README.md) |

---

## 🎯 Objetivos Cumplidos

### ✅ **Requerimientos Funcionales Implementados**

| Requerimiento                         | Implementación                                                | Módulo   | Estado |
| :------------------------------------ | :------------------------------------------------------------- | :-------- | :----- |
| **Modelo de datos jerárquico** | Modelo `Node` con autorreferencia (`parent` FK a `self`) | `nodes` | ✅     |
| **Endpoints CRUD completos**    | API REST con Django REST Framework                             | Ambos     | ✅     |
| **Traducción multi-idioma**    | *Header* `Accept-Language` (ISO 639-1)                     | `nodes` | ✅     |
| **Timezone dinámico**          | *Header* `X-Timezone`                                      | `nodes` | ✅     |
| **Profundidad configurable**    | Parámetro `?depth=X` en *queries*                         | `nodes` | ✅     |
| **Validación de borrado**      | Solo nodos hoja pueden ser eliminados                          | `nodes` | ✅     |
| **Autenticación JWT**          | Login dual (email/username) con confirmación requerida        | `users` | ✅     |
| **Sistema de roles**            | Jerarquía SUDO > ADMIN > USER con permisos granulares         | `users` | ✅     |
| **Soft delete**                 | Eliminación lógica con validación de integridad             | Ambos     | ✅     |
| **Seeder automático**          | Comandos de gestión para datos iniciales                      | Ambos     | ✅     |
| **Documentación API**          | Swagger UI con drf-spectacular                                 | Ambos     | ✅     |
| **Contenerización**            | Docker + Docker Compose                                        | -         | ✅     |

---

## 🚀 Tecnologías Utilizadas - Detallado

### **Backend & Framework**

- **Django 6.0.2** - *Framework* web Python con soporte asíncrono
- **Django REST Framework 3.16.1** - Construcción de APIs RESTful con serialización avanzada
- **TOML para dependencias** - Gestión moderna de paquetes con `pyproject.toml`

### **Base de Datos & Optimización**

- **PostgreSQL 18 Alpine** - Versión ligera y eficiente (*postgres:18-alpine*)
- **PgBouncer** - *Connection pooling* para alta concurrencia (*imagen: edoburu/pgbouncer*)
- **Django Caching** - *Cache* integrado para reducir conexiones a base de datos
- **Configuración PostgreSQL** - Archivo `pg_hba.conf` personalizado para red Docker

### **Autenticación & Seguridad**

- **Simple JWT 5.5.1** - Autenticación con JSON Web *Tokens* robusta
- **SCRAM-SHA-256** - Autenticación moderna en PgBouncer
- **Custom Authentication Backend** - Login dual (email/username)
- **Django CORS Headers** - Control de acceso entre dominios seguro

### **Internacionalización**

- **num2words 0.5.14** - Conversión de números a texto en múltiples idiomas
- **pytz 2025.2** - Manejo completo de zonas horarias
- **Custom Middleware** - Procesamiento dinámico de *headers* de idioma y zona horaria

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

## 📂 Estructura del Repositorio (Infraestructura y Configuración)

El proyecto utiliza una estructura de aplicación plana donde las *apps* personalizadas (`nodes`, `users`) son hermanas del directorio de configuración (`app_nodos`).

```
. (Raíz del repositorio, contiene docker-compose.yml y manage.py)
├── app_nodos/             # Directorio de configuración de Django (settings, urls, wsgi/asgi).
├── manage.py              # Script de gestión de Django.
├── middleware/            # Módulo de lógica de intercepción (timezone, cache de idioma).
├── nodes/                 # 📂 Módulo de gestión de árboles jerárquicos.
├── users/                 # 🔒 Módulo de gestión de usuarios y autenticación.
├── docker/                # Scripts de orquestación y arranque de Docker.
│   └── django/
│       ├── entrypoint-dev.sh    # Script de arranque para Desarrollo (manage.py runserver).
│       └── entrypoint-prod.sh   # Script de arranque para Producción (uvicorn).
├── postgres/              # Archivos de configuración de la base de datos.
│   └── pg_hba.conf        # Reglas de autenticación de PostgreSQL (CRÍTICO para PgBouncer).
├── postman/               # Colecciones de Postman para probar la API.
│   ├── Nodes.postman_collection.json
│   ├── Token.postman_collection.json
│   └── Users.postman_collection.json
├── Dockerfile             # Definición de la imagen con Multi-Stage Builds (builder, dev, prod).
├── pyproject.toml         # Gestión de dependencias (PEP 621).
└── logs/                  # (Volumen) Archivos de log de la aplicación.
```

### Descripción de Componentes de Infraestructura

| Archivo/Carpeta          | Propósito Principal                                                                                                                                                                                                                                                       |
| :----------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docker/django/*.sh`   | Contienen la lógica de arranque de la aplicación. Se diferencian en la fase final:**`entrypoint-dev.sh`** lanza `runserver` con *hot reload*, mientras que **`entrypoint-prod.sh`** lanza `uvicorn` con *workers* y colecta archivos estáticos. |
| `Dockerfile`           | Implementa*Multi-Stage Builds* para crear una imagen ligera de producción y una imagen funcional de desarrollo a partir del mismo código base.                                                                                                                         |
| `postgres/pg_hba.conf` | **Seguridad** de PostgreSQL. Configura el tipo de autenticación (`md5`) y, crucialmente, restringe las conexiones a la red interna de Docker, forzando a que todo el tráfico pase a través de PgBouncer.                                                        |
| `postman/`             | Colecciones pre-diseñadas para Postman que permiten a los desarrolladores y QA ejecutar peticiones y*tests* de la API rápidamente. Incluye flujos de `Token`, `Users` y `Nodes`.                                                                                 |
| `docker-compose.*.yml` | Define y coordina los servicios (`web`, `db`, `pgbouncer`). El archivo `prod.yml` sobrescribe la configuración de desarrollo para usar la imagen optimizada y el servidor Uvicorn.                                                                                |

---

## 💻 Comandos de Ejecución

El proyecto está configurado para ejecutarse en dos modos distintos (Desarrollo y Producción) utilizando Docker Compose y *Multi-stage builds*.

### 1. Modo Desarrollo (`development`)

Este modo utiliza `docker-compose.yml` y automáticamente aplica `docker-compose.override.yml`. Está configurado para:

* Usar el *target* `development` del Dockerfile (con `netcat`, etc.).
* Montar los volúmenes de código (`./app_nodos`) para permitir cambios en vivo.
* Ejecutar el servidor de desarrollo de Django (`runserver`) con *autoreload*.

| Uso                     | Comando                          |
| :---------------------- | :------------------------------- |
| **Foreground**    | `docker compose up --build`    |
| **Detached (-d)** | `docker compose up -d --build` |
| **Logs**          | `docker compose logs -f web`   |
| **Detener**       | `docker compose down -v`       |

### 2. Modo Producción (`production`)

Este modo se invoca explícitamente combinando `docker-compose.yml` y `docker-compose.prod.yml`. Está configurado para:

* Usar el *target* `production` del Dockerfile (*imagen final más ligera*).
* **NO montar volúmenes** de código (usa la imagen compilada e inmutable).
* Ejecutar `Uvicorn` + ASGI con *workers* para alta *performance*.
* Forzar `DEBUG=False` y aplicar configuraciones de seguridad.

| Uso                     | Comando                                                                           |
| :---------------------- | :-------------------------------------------------------------------------------- |
| **Foreground**    | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build`    |
| **Detached (-d)** | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build` |
| **Logs**          | `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f web`   |
| **Detener**       | `docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v`       |

**Nota Importante:** Si estás ejecutando en producción, verifica tu archivo de entorno (`.env`) para configurar correctamente las variables de seguridad (p.ej., `SECRET_KEY`) y la configuración de acceso (`CORS_ALLOWED_ORIGINS`).

---

## 🏗️ Arquitectura del Sistema - Infraestructura Docker

### **Servicios Configurados**

| Servicio             | Imagen/Config          | Puerto         | Propósito              | Dependencias |
| :------------------- | :--------------------- | :------------- | :---------------------- | :----------- |
| **PostgreSQL** | *postgres:18-alpine* | 5432 (interno) | Base de datos principal | -            |
| **PgBouncer**  | *edoburu/pgbouncer*  | 6432 (host)    | *Pool* de conexiones  | PostgreSQL   |
| **Django App** | Custom Dockerfile      | 8000           | Aplicación principal   | PgBouncer    |

### **Flujo de Conexiones Optimizado**

```
Aplicación Django → PgBouncer (Pool: 20 conexiones) → PostgreSQL
```

- **Modo transacción**: Configuración óptima para Django
- **Max conexiones**: 100 clientes, *pool* de 20
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

1. **Espera para PostgreSQL** (*Health Check*)

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

- **Cache de 180 segundos** en *endpoints* de listado
- **Reducción de *queries*** con `select_related` y `prefetch_related`
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
    # Django Core
    "Django==6.0.2",
  
    # Django Extensions
    "django-filter==25.2",
    "django-cors-headers==4.9.0",
  
    # REST Framework
    "djangorestframework==3.16.1",
    "djangorestframework-simplejwt==5.5.1",
  
    # Database
    "psycopg2-binary==2.9.11",
  
    # Documentation
    "drf-spectacular==0.29.0",
    "Markdown==3.10.1",
  
    # Internacionalización
    "num2words==0.5.14",
    "pytz==2025.2",
  
    # ASGI Server (Producción)
    "uvicorn[standard]==0.40.0",
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

1. **Red Aislada**: `backend_net` con *subnet* específica
2. **PgBouncer como *firewall***: PostgreSQL no expuesto directamente
3. **Autenticación JWT**: *Tokens* firmados con expiración
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
docker-compose up --build```

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
- **Cache hit rate**: Efectividad de *cache* Django
- **Connection churn**: Nuevas conexiones vs reutilizadas

---

## 🚦 Estado del Sistema

**✅ Producción Optimizada**

- [X] **Infraestructura Docker completa** con 3 servicios coordinados
- [X] **Connection pooling** con PgBouncer para alta concurrencia
- [X] **Inicialización automática** con *entrypoint* inteligente
- [X] **Configuración PostgreSQL** segura y aislada
- [X] **Gestión moderna de dependencias** con TOML
- [X] **Red aislada** con *subnet* específica para seguridad
- [X] *Health checks* para verificación de servicios

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
5. **Testear conexiones** en entorno *staging*

---

**Versión Técnica**: 1.0.0
**Última actualización**: Febrero 2026
**Arquitectura**: Microservicios Docker con optimización PgBouncer
**Soporte**: Red aislada + *Connection Pooling* + *Cache Estratégico*

## 📊 Características por Módulo

### **🔒 Módulo `users` - Características Principales**

| Característica                      | Descripción                              |
| :----------------------------------- | :---------------------------------------- |
| **Login dual**                 | Autenticación con email o username       |
| **Roles jerárquicos**         | SUDO (único) > ADMIN > USER              |
| **Email confirmado requerido** | Sin confirmación = sin acceso            |
| **Soft delete**                | Eliminación lógica con validaciones     |
| **Auto-gestión**              | *Endpoints* `/me/` para auto-gestión |
| **Auditoría**                 | *Trackeo* de nodos creados por usuario  |
| **Comandos CLI**               | `setup_sudo`, `seed_users`            |

### **📂 Módulo `nodes` - Características Principales**

| Característica                  | Descripción                                      |
| :------------------------------- | :------------------------------------------------ |
| **Estructura jerárquica** | Árbol con*parent self-referential*             |
| **Internacionalización**  | `title` generado con *num2words* en 8 idiomas |
| **Zona horaria dinámica** | `created_at` formateado según *header*       |
| **Control de profundidad** | Parámetro `?depth` (0, 1, 2, ..., -1)          |
| **Caching estratégico**   | 180s para listados con diferenciación            |
| **Validación de borrado** | Solo nodos hoja pueden eliminarse                 |
| **Comando CLI**            | `seed_nodes` para estructura de prueba          |

---

## 🌐 API Endpoints

### **🔐 Autenticación (`users`)**

```bash
# 1. Obtener token JWT
POST /api/token/
{
  "username": "admin@system.com",  # o nombre de usuario
  "password": "Admin123!"
}

# 2. Usar token en requests
Authorization: Bearer <access_token>
```

### **👥 Gestión de Usuarios**

| Método   | Endpoint                           | Permiso               | Descripción                             |
| :-------- | :--------------------------------- | :-------------------- | :--------------------------------------- |
| `GET`   | `/api/users/`                    | SUDO/ADMIN/USER*      | Lista usuarios (*USER solo ve su perfil) |
| `POST`  | `/api/users/`                    | SUDO/ADMIN            | Crear usuario                            |
| `GET`   | `/api/users/me/`                 | Cualquier autenticado | Mi perfil con métricas                  |
| `PATCH` | `/api/users/me/update/`          | Cualquier autenticado | Actualizar mi perfil                     |
| `POST`  | `/api/users/me/change-password/` | Cualquier autenticado | Cambiar contraseña                      |
| `GET`   | `/api/users/{id}/nodes-created/` | Según visibilidad    | Auditoría de nodos creados              |

### **🌳 Gestión de Nodos**

| Método    | Endpoint                         | Permiso             | Headers Especiales                 |
| :--------- | :------------------------------- | :------------------ | :--------------------------------- |
| `GET`    | `/api/nodes/`                  | Usuario autenticado | `Accept-Language`, `Time-Zone` |
| `GET`    | `/api/nodes/{id}/`             | Usuario autenticado | `Accept-Language`, `Time-Zone` |
| `POST`   | `/api/nodes/`                  | ADMIN/SUDO          | -                                  |
| `PATCH`  | `/api/nodes/{id}/`             | ADMIN/SUDO          | -                                  |
| `DELETE` | `/api/nodes/{id}/`             | ADMIN/SUDO          | -                                  |
| `GET`    | `/api/nodes/{id}/descendants/` | Usuario autenticado | `Accept-Language`, `Time-Zone` |
| `GET`    | `/api/trees/`                  | Usuario autenticado | `Accept-Language`, `Time-Zone` |

### **Parámetros de Consulta (`nodes`)**

| Parámetro  | Valores          | Descripción           | Ejemplo        |
| :---------- | :--------------- | :--------------------- | :------------- |
| `depth`   | 0, 1, 2, ..., -1 | Niveles de profundidad | `?depth=2`   |
| `root_id` | número          | Árbol específico     | `?root_id=5` |

### **Headers Personalizados**

| Header              | Valores Ejemplo                         | Módulo   | Propósito                       |
| :------------------ | :-------------------------------------- | :-------- | :------------------------------- |
| `Accept-Language` | `es`, `fr`, `de`, `en`          | `nodes` | Idioma para campo `title`      |
| `Time-Zone`       | `America/New_York`, `Europe/Madrid` | `nodes` | Zona horaria para `created_at` |

---

## 🔧 Configuración y Comandos

### **Inicialización Completa**

```bash
# 1. Iniciar contenedores
docker-compose up -d

# 2. Aplicar migraciones
docker-compose exec web python manage.py migrate

# 3. Crear usuario SUDO inicial
docker-compose exec web python manage.py setup_sudo

# 4. Poblar datos de prueba
docker-compose exec web python manage.py seed_users
docker-compose exec web python manage.py seed_nodes
```

### **Comandos de Gestión por Módulo**

```bash
# 🔒 Módulo users
docker-compose exec web python manage.py setup_sudo    # Crear SUDO
docker-compose exec web python manage.py seed_users    # Usuarios prueba

# 📂 Módulo nodes
docker-compose exec web python manage.py seed_nodes    # Estructura árbol

# 🧪 Testing
docker-compose exec web python manage.py test users    # Tests usuarios
docker-compose exec web python manage.py test nodes    # Tests nodos
```

### **Verificación del Sistema**

```bash
# Salud de la API
curl http://localhost:8000/api/

# Documentación Swagger
curl http://localhost:8000/api/docs/

# Ver logs en tiempo real
docker-compose logs -f web
```

---

## 🧪 Testing y Calidad

### **Ejecutar Pruebas**

```bash
# Todos los tests
docker-compose exec web python manage.py test

# Por módulo
docker-compose exec web python manage.py test users
docker-compose exec web python manage.py test nodes

# Tests específicos
docker-compose exec web python manage.py test users.tests.UserSecurityTest
docker-compose exec web python manage.py test nodes.tests.NodeAPITest
```

### **Cobertura de Tests**

#### **🔒 Módulo `users`**

- ✅ Validación de regla SUDO único
- ✅ Autenticación con email/username
- ✅ Permisos por rol en *endpoints*
- ✅ *Soft delete* y validaciones
- ✅ Cambio de contraseña
- ✅ Auto-gestión de perfil

#### **📂 Módulo `nodes`**

- ✅ Serialización con diferentes idiomas
- ✅ Control de profundidad (`depth` *parameter*)
- ✅ Conversión de zonas horarias
- ✅ Validaciones de negocio
- ✅ Permisos y autorización
- ✅ Borrado lógico

---

## ⚡ Rendimiento y Optimización

### **Estrategias Implementadas**

| Estrategia                        | Módulo   | Beneficio                                 |
| :-------------------------------- | :-------- | :---------------------------------------- |
| **Caching 180s**            | `nodes` | Reduce carga en listados frecuentes       |
| **Connection pooling**      | Ambos     | PgBouncer para alta concurrencia          |
| **Query optimization**      | Ambos     | `select_related` + `prefetch_related` |
| **Validación temprana**    | `nodes` | IDs válidos antes de consultar DB        |
| **Lazy loading controlado** | `nodes` | Serialización recursiva por `depth`    |
| **Indexing estratégico**   | Ambos     | Índices en campos de búsqueda           |

### **Estadísticas de Performance**

- **Tiempo de respuesta API**: < 200ms (listados con caché)
- **Concurrencia**: Soporte para 100+ conexiones simultáneas
- **Memoria**: Uso optimizado con *connection pooling*
- **Escalabilidad**: *Stateless architecture* con JWT

---

## 🛡️ Seguridad

### **Características de Seguridad**

| Característica                      | Módulo   | Descripción                                   |
| :----------------------------------- | :-------- | :--------------------------------------------- |
| **JWT con expiración**        | `users` | 60 minutos acceso, 1 día*refresh*           |
| **Email confirmado requerido** | `users` | Doble factor implícito                        |
| **Único usuario SUDO**        | `users` | Regla de negocio estricta                      |
| **Soft delete**                | Ambos     | Previene pérdida de datos                     |
| **Auditoría completa**        | Ambos     | `created_by`, `updated_by`, *timestamps* |
| **Validación de *input***   | Ambos     | *Serializers* con validaciones estrictas     |
| **CORS configurado**           | Ambos     | Solo dominios permitidos en producción        |
| **Jerarquía de permisos**     | Ambos     | SUDO > ADMIN > USER sin saltos                 |

### **Validaciones de Negocio**

1. **SUDO único**: Solo puede existir un usuario SUDO en el sistema
2. **Jerarquía estricta**: SUDO > ADMIN > USER (sin saltos)
3. **Auto-protección**: Usuario no puede eliminarse/desactivarse a sí mismo
4. **Integridad referencial**: No se puede eliminar usuario/nodo con dependencias activas
5. **Confirmación requerida**: Sin email confirmado = sin autenticación

---

## 🔮 Roadmap y Mejoras Futuras

### **Próximas Características**

| Prioridad | Característica             | Módulo   | Descripción                       |
| :-------- | :-------------------------- | :-------- | :--------------------------------- |
| Alta      | **Email service**     | `users` | Verificación de email automática |
| Alta      | **File uploads**      | `nodes` | Adjuntar documentos a nodos        |
| Media     | **Search engine**     | `nodes` | Búsqueda*full-text* en títulos |
| Media     | **Export/Import**     | Ambos     | JSON/CSV para*backup*            |
| Baja      | **WebSocket**         | Ambos     | Actualizaciones en tiempo real     |
| Baja      | **Metrics dashboard** | Ambos     | Estadísticas de uso               |

### **Escalabilidad**

- ***Horizontal scaling***: *Stateless* con JWT
- ***Database sharding***: Por *tenant* o región
- ***CDN integration***: Para archivos estáticos
- ***Queue system***: Para tareas asíncronas (*Celery + Redis*)
- ***Microservicios***: Separación de módulos si crece la complejidad

---

## 🤝 Contribución

### **Flujo de Trabajo**

1. **Fork** del repositorio
2. **Branch descriptivo**: `feat/nueva-funcionalidad` o `fix/correccion-error`
3. **Tests**: Incluir pruebas para cambios
4. **Documentación**: Actualizar READMEs afectados
5. **Pull Request**: Con descripción detallada

### **Estándares de Código**

- **PEP 8**: Estilo Python consistente
- ***Type hints***: Donde sea aplicable
- ***Docstrings***: Documentación en funciones/métodos importantes
- ***Commits semánticos***: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

---

## 📞 Soporte y Recursos

### **Recursos Disponibles**

| Recurso                                    | URL                                 | Descripción               |
| :----------------------------------------- | :---------------------------------- | :------------------------- |
| **Documentación API**               | `http://localhost:8000/api/docs/` | Swagger UI interactivo     |
| **Panel de Admin**                   | `http://localhost:8000/admin/`    | Django Admin               |
| ***Health Check***                 | `http://localhost:8000/api/`      | Estado del sistema         |
| **Documentación módulo `users`** | `users/README.md`                 | Especificaciones completas |
| **Documentación módulo `nodes`** | `nodes/README.md`                 | Especificaciones completas |

### **Solución de Problemas Comunes**

#### **Error: "Ya existe un usuario SUDO"**

```bash
# Verificar usuarios SUDO existentes
docker-compose exec web python manage.py shell -c "from users.models import User; print(User.objects.filter(role='SUDO').count())"
```

#### **Error: Usuario no puede autenticarse**

1. Verificar `is_email_confirmed=True`
2. Verificar `is_active=True`
3. Verificar `is_deleted=False`
4. Verificar credenciales correctas

#### **Error: Headers no aplicados en `nodes`**

1. Verificar `Accept-Language` está en lista soportada
2. Verificar `Time-Zone` es válida (ej: `America/New_York`)
3. Verificar *headers* están en *request* (no *query params*)

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- **Django Community**: Por el excelente *framework*
- **DRF Team**: Por las herramientas REST
- **PostgreSQL Team**: Por la base de datos robusta
- **Docker Team**: Por la contenerización
- **Contribuidores**: Por mejoras y reportes de *issues*

---

**Versión**: 1.0.0
**Última actualización**: Febrero 2026
**Mantenido por**: Francisco A. Hernandez S. (*github* @veniversvm)
**Documentación módulos**:

- [🔒 Módulo Users](users/README.md)
- [📂 Módulo Nodes](nodes/README.md)
