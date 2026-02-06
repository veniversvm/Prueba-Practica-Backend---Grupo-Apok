# Módulo de Usuarios (users)

## 📋 Descripción del Módulo

El módulo `users` implementa un sistema completo de gestión de usuarios personalizado para la aplicación de gestión de árboles jerárquicos. Proporciona autenticación avanzada, control de acceso basado en roles y un modelo de usuario extendido con reglas de negocio específicas.

## 🏗️ Arquitectura del Módulo

### Estructura de Archivos

```
users/
├── models.py           # Modelo User personalizado con roles y validaciones
├── views.py           # ViewSet con lógica CRUD y endpoints personalizados
├── serializers.py     # Serializers para operaciones de usuario
├── permissions.py     # Sistema de permisos basado en roles (SUDO, ADMIN, USER)
├── backends.py        # Backend de autenticación personalizado (email/username)
├── admin.py          # Configuración personalizada del panel de administración
├── urls.py           # Rutas API REST para usuarios
├── tests.py          # Suite de pruebas unitarias
├── apps.py           # Configuración de la aplicación
└── management/       # Comandos de gestión personalizados
    ├── commands/
    │   ├── setup_sudo.py    # Creación del usuario SUDO inicial
    │   └── seed_users.py    # Población de usuarios de prueba
    └── __init__.py
```

## 🔧 Componentes Principales

### 1. Modelo de Usuario Personalizado (`models.py`)

- **Clase `User`**: Extiende `AbstractUser` de Django
- **Roles**: SUDO, ADMIN, USER con validación de unicidad para SUDO
- **Campos adicionales**:
  - `role`: Rol del usuario (choices: SUDO, ADMIN, USER)
  - `is_email_confirmed`: Flag de confirmación de email
- **Manager personalizado**: `CustomUserManager` para superusuarios SUDO
- **Regla de negocio**: Solo un usuario SUDO permitido en el sistema

### 2. Sistema de Autenticación (`backends.py`)

- **Backend personalizado**: `EmailOrUsernameBackend`
- **Login dual**: Permite autenticación tanto con email como con username
- **Reglas de seguridad**: Requiere `is_email_confirmed=True` para autenticación exitosa
- **Optimización**: Consultas eficientes basadas en el formato del input

### 3. Sistema de Permisos (`permissions.py`)

- **`IsActiveAndConfirmed`**: Acceso solo para usuarios activos con email confirmado (lectura)
- **`IsAdminUserCustom`**: Permite acciones de escritura solo para roles ADMIN y SUDO
- **`IsSudoUser`**: Acceso exclusivo para usuarios con rol SUDO

### 4. API REST (`views.py`, `serializers.py`, `urls.py`)

- **ViewSet**: `UserViewSet` con CRUD completo y endpoints personalizados
- **Serializers especializados**:
  - `UserSerializer`: Operaciones generales
  - `UserDetailSerializer`: Detalle con estadísticas de nodos creados
  - `UserCreateSerializer`: Creación con validación de contraseña
- **Endpoints personalizados**:
  - `/me/`: Perfil del usuario actual
  - `/me/update/`: Actualización del perfil
  - `/me/change-password/`: Cambio de contraseña
  - `/{id}/nodes-created/`: Auditoría de nodos creados

### 5. Panel de Administración (`admin.py`)

- **Admin personalizado**: `CustomUserAdmin` que extiende `UserAdmin`
- **Vistas optimizadas**: Filtros por rol, estado de confirmación y actividad
- **Campos personalizados**: Integración de campos extendidos del modelo

### 6. Comandos de Gestión (`management/`)

- **`setup_sudo`**: Crea el usuario SUDO inicial desde variables de entorno
- **`seed_users`**: Pobla la base de datos con usuarios de prueba para desarrollo/testing

## 🔐 Reglas de Negocio Clave

### Autenticación y Acceso

1. **Email confirmado requerido**: Los usuarios deben tener `is_email_confirmed=True` para autenticarse
2. **Login dual**: Autenticación con email o username
3. **Acceso por rol**: Filtrado automático de usuarios visibles según el rol del usuario autenticado

### Gestión de Usuarios

1. **Unicidad SUDO**: Solo puede existir un usuario con rol SUDO en el sistema
2. **Control de creación de SUDO**: Solo usuarios SUDO pueden crear otros usuarios SUDO
3. **Auto-edición limitada**: Usuarios USER no pueden cambiar su propio rol

### Permisos de Escritura

1. **SUDO**: Acceso completo a todas las operaciones
2. **ADMIN**: Puede crear/editar/eliminar usuarios USER, pero no SUDO u otros ADMIN
3. **USER**: Solo operaciones de lectura en su propio perfil

## 📊 Flujos de Datos

### Creación de Usuario

```
Cliente → POST /api/users/ → UserCreateSerializer → Validación de rol → Creación de usuario
```

### Autenticación

```
Cliente → POST /api/token/ → EmailOrUsernameBackend → Validación de confirmación → JWT Token
```

### Auditoría

```
Cliente → GET /api/users/{id}/nodes-created/ → Filtro por created_by → Serialización de nodos
```

## 🧪 Testing

### Tipos de Pruebas

1. **Pruebas de modelo**: Validación de reglas de negocio (unicidad SUDO)
2. **Pruebas de autenticación**: Login dual y confirmación de email
3. **Pruebas de API**: Endpoints CRUD y personalizados
4. **Pruebas de permisos**: Acceso basado en roles

### Ejecución

```bash
python manage.py test users.tests
```

## ⚙️ Configuración Requerida

### Variables de Entorno para SUDO

```env
SUDO_USERNAME=admin
SUDO_EMAIL=admin@sistema.com
SUDO_PASSWORD=contraseña_segura
```

### Configuración Django

```python
# settings.py
AUTH_USER_MODEL = 'users.User'
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

## 🔄 Dependencias

### Internas

- **Modelo Node**: Para auditoría de nodos creados (`nodes_created_count`)

### Externas

- **Django REST Framework**: Para la API REST
- **Simple JWT**: Para autenticación basada en tokens
- **Django Filters**: Para filtrado avanzado en la API

## 📈 Métricas y Auditoría

### Campos de Auditoría

- `date_joined`: Fecha de registro
- `last_login`: Último acceso
- `nodes_created_count`: Número de nodos creados (métrica de actividad)

### Endpoints de Auditoría

- `GET /api/users/{id}/nodes-created/`: Lista de nodos creados por usuario
- Campos de filtro: `created_at`, `updated_at`, `is_deleted`

## 🚨 Manejo de Errores

### Validaciones Específicas

- **SUDO duplicado**: `ValidationError` con mensaje claro
- **Permisos insuficientes**: `HTTP 403 Forbidden` con detalle del rol requerido
- **Email no confirmado**: `HTTP 401 Unauthorized` en autenticación

### Mensajes de Error Estructurados

```json
{
  "detail": "No tienes permisos para crear usuarios.",
  "code": "permission_denied"
}
```

## 🔮 Extensiones Futuras

### Potenciales Mejoras

1. **Verificación por email**: Envío automático de emails de confirmación
2. **Recuperación de contraseña**: Flujo self-service
3. **Logs de actividad**: Registro detallado de acciones por usuario
4. **Perfiles extendidos**: Campos adicionales según necesidades de negocio

---

**Responsabilidad**: Gestión completa del ciclo de vida de usuarios
**Integración**: Autenticación, autorización y auditoría
**Mantenimiento**: Equipo de desarrollo backend
