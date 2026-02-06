# Módulo Principal - app_nodos

## 📋 Descripción del Módulo

El módulo principal `app_nodos` es el corazón del proyecto Django que gestiona el sistema de árboles jerárquicos. Configura la aplicación completa, define las rutas principales y establece la configuración global del proyecto.

## 🏗️ Arquitectura del Módulo

### Estructura de Archivos

```
app_nodos/
├── __init__.py          # Identifica el directorio como paquete Python
├── settings.py          # Configuración global del proyecto Django
├── urls.py             # Enrutamiento principal de la aplicación
├── wsgi.py             # Configuración WSGI para despliegue
└── asgi.py             # Configuración ASGI para async (futuro)
```

## 🔧 Componentes Principales

### 1. Configuración Global (`settings.py`)

**Responsabilidad**: Definir toda la configuración del proyecto Django

#### Configuraciones Clave:

**Aplicaciones Instaladas**:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... apps de Django core
    'rest_framework',           # Framework REST
    'rest_framework_simplejwt', # Autenticación JWT
    'drf_spectacular',         # Documentación OpenAPI
    'nodes',                   # App de gestión de nodos
    'users',                   # App de gestión de usuarios
]
```

**Configuración de Base de Datos**:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT"),
    }
}
```

**Configuración REST Framework**:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

**JWT Configuration**:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

**Modelo de Usuario Personalizado**:

```python
AUTH_USER_MODEL = 'users.User'  # Usa el modelo User personalizado
```

**Backends de Autenticación**:

```python
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameBackend',  # Backend personalizado
    'django.contrib.auth.backends.ModelBackend',  # Backend por defecto
]
```

**Configuración de Caché**:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "node-cache",
    }
}
```

**Lógica Especial para Testing**:

```python
if 'test' in sys.argv:
    # Bypass de pgbouncer para tests directos a PostgreSQL
    DATABASES['default']['HOST'] = 'db'
    DATABASES['default']['PORT'] = '5432'
```

### 2. Enrutamiento Principal (`urls.py`)

**Responsabilidad**: Definir las rutas URL principales de la aplicación

#### Estructura de Rutas:

```python
urlpatterns = [
    # Administración Django
    path('admin/', admin.site.urls),
  
    # Autenticación JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
  
    # Rutas de la aplicación
    path('api/', include('nodes.urls')),   # Endpoints de nodos
    path('api/', include('users.urls')),   # Endpoints de usuarios
  
    # Documentación API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

**Health Check Endpoint**:

```python
def health_check(request):
    """Endpoint simple para verificar que la aplicación está funcionando"""
    return JsonResponse({
        "message": "Hello World! El sistema está online.",
        "status": 200
    })
```

### 3. Configuración WSGI (`wsgi.py`)

**Responsabilidad**: Configurar la aplicación WSGI para despliegue en producción

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_nodos.settings')
application = get_wsgi_application()
```

### 4. Configuración ASGI (`asgi.py`)

**Responsabilidad**: Configurar la aplicación ASGI para soporte async (futuro)

```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_nodos.settings')
application = get_asgi_application()
```

## 🔐 Arquitectura de Seguridad

### Autenticación

- **JWT como estándar**: Tokens Bearer para todas las APIs
- **Doble backend**: Sistema personalizado + sistema Django por defecto
- **Protección global**: `IsAuthenticated` por defecto en todas las APIs

### Configuración de Entorno

- **Variables de entorno**: Configuración sensible (DB, JWT, etc.)
- **Entornos separados**: Configuración diferenciada para dev/test/prod
- **Secrets management**: Claves fuera del código fuente

## 🗺️ Estructura de URLs

### API Principal (`/api/`)

```
/api/
├── token/                    # Obtener token JWT
├── token/refresh/           # Refrescar token
├── nodes/                   # Gestión de nodos
│   ├── (listado)
│   ├── {id}/               # Detalle/actualización
│   └── my-nodes/           # Nodos del usuario actual
├── users/                   # Gestión de usuarios
│   ├── (listado)
│   ├── {id}/               # Detalle de usuario
│   ├── me/                 # Perfil actual
│   ├── me/update/          # Actualizar perfil
│   ├── me/change-password/ # Cambiar contraseña
│   └── {id}/nodes-created/ # Auditoría de nodos
├── schema/                  # Esquema OpenAPI
└── docs/                    # Documentación Swagger UI
```

### Panel de Administración (`/admin/`)

- Interfaz Django Admin completa
- Configuración personalizada de modelos
- Gestión de usuarios y nodos

## 🛠️ Configuración de Desarrollo

### Variables de Entorno Requeridas

```env
# Base de Datos PostgreSQL
POSTGRES_DB=tree_db
POSTGRES_USER=tree_user
POSTGRES_PASSWORD=tree_password
POSTGRES_HOST=pgbouncer
POSTGRES_PORT=5432

# Configuración Django
DJANGO_SETTINGS_MODULE=app_nodos.settings
DJANGO_SECRET_KEY=tu_clave_secreta_aqui
```

### Dependencias Externas

```txt
Django==6.0.2
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
drf-spectacular==0.26.5
psycopg2-binary==2.9.9
```

## 🔧 Características Técnicas

### Base de Datos

- **PostgreSQL**: Base de datos principal
- **PgBouncer**: Connection pooling para producción
- **Optimización para tests**: Bypass directo a PostgreSQL

### Caché

- **Memoria local**: Para caché de listados de nodos
- **Configurable**: Fácil cambio a Redis/Memcached

### Documentación

- **OpenAPI 3.0**: Esquema automático con drf-spectacular
- **Swagger UI**: Interfaz interactiva de documentación
- **Health Check**: Endpoint simple para monitoreo

## 🧪 Soporte para Testing

### Configuración Especial

```python
# Bypass de pgbouncer en tests
if 'test' in sys.argv:
    DATABASES['default']['HOST'] = 'db'
    DATABASES['default']['PORT'] = '5432'
```

### Ejecución de Tests

```bash
# Ejecutar todos los tests
python manage.py test

# Ejecutar tests específicos
python manage.py test users.tests
python manage.py test nodes.tests
```

## 🔄 Flujos de Configuración

### Inicialización del Proyecto

1. Configurar variables de entorno
2. Ejecutar migraciones: `python manage.py migrate`
3. Crear usuario SUDO: `python manage.py setup_sudo`
4. Poblar datos de prueba: `python manage.py seed_users`

### Despliegue

1. Configurar entorno de producción
2. Recopilar archivos estáticos: `python manage.py collectstatic`
3. Configurar servidor WSGI/ASGI
4. Configurar balanceador de carga y SSL

## 📊 Métricas y Monitoreo

### Health Check

- Endpoint: `/` (pendiente de implementar)
- Respuesta JSON estructurada
- Estado del sistema y versiones

### Logging

- Configuración Django estándar
- Niveles configurables por entorno
- Integración con servicios de monitoreo

## 🚨 Consideraciones de Producción

### Seguridad

- **DEBUG=False** en producción
- **ALLOWED_HOSTS** configurado correctamente
- **HTTPS** obligatorio para APIs
- **Rate limiting** recomendado

### Performance

- **Connection pooling** con PgBouncer
- **Caché** para operaciones costosas
- **Optimización de consultas** con select_related/prefetch_related

### Escalabilidad

- **Stateless**: JWT permite escalado horizontal
- **Microservicios ready**: APIs bien definidas
- **Contenerización**: Configuración Docker incluida

## 🔮 Extensiones Futuras

### Potenciales Mejoras

1. **Configuración por entorno**: settings/development.py, settings/production.py
2. **Logging avanzado**: Integración con ELK/Sentry
3. **Métricas**: Integración con Prometheus
4. **Caché distribuido**: Redis para producción
5. **CDN**: Para archivos estáticos en producción

---

**Responsabilidad**: Configuración global y coordinación del proyecto
**Integración**: Conexión entre todos los módulos y servicios
**Mantenimiento**: Equipo DevOps y desarrolladores senior
