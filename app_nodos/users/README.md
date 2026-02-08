
# 🔒 Módulo: Gestión de Usuarios y Autenticación (`users`)

Este módulo implementa el sistema central de **Gestión de Identidad y Acceso (IAM)** con autenticación JWT, control de roles jerárquico y seguridad avanzada.

## 📁 Estructura del Módulo

```
users/
├── models.py               # Modelo User personalizado con roles SUDO/ADMIN/USER
├── views.py               # ViewSet con lógica de permisos granular
├── serializers.py         # Serializers para CRUD con validaciones
├── backends.py           # Backend de autenticación dual (email/username)
├── permissions.py        # Permisos personalizados basados en roles
├── urls.py              # Rutas API del módulo
├── admin.py             # Configuración del admin de Django
├── tests.py             # Suite completa de tests unitarios
├── management/
│   ├── commands/
│   │   ├── setup_sudo.py    # Comando para crear usuario SUDO inicial
│   │   └── seed_users.py    # Comando para poblar usuarios de prueba
└── migrations/           # Migraciones de base de datos
```

## 🏗️ Arquitectura

### **Modelo User Personalizado**

```python
# Extiende AbstractUser de Django añadiendo:
- role: SUDO | ADMIN | USER (jerarquía estricta)
- is_email_confirmed: Requerido para autenticación
- is_deleted: Soft delete para mantener integridad
- Regla única: Solo UN usuario SUDO permitido
```

### **Sistema de Roles**

| Rol             | Permisos                                                          | Restricciones                                               |
| --------------- | ----------------------------------------------------------------- | ----------------------------------------------------------- |
| **SUDO**  | Acceso total, crear cualquier usuario, eliminar cualquier usuario | Solo uno por sistema, no puede eliminarse a sí mismo       |
| **ADMIN** | Crear/eliminar USER, ver/modificar contenido                      | No puede ver/modificar SUDO, no puede modificar otros ADMIN |
| **USER**  | Ver/modificar propio perfil, operaciones de lectura               | Solo ve su perfil, no puede cambiar su rol                  |

## 🔐 Autenticación

### **Login Dual**

```python
# EmailOrUsernameBackend permite:
POST /api/token/ {"username": "user@email.com" OR "username", "password": "..."}
```

- ✅ Login con email o username
- ❌ Falla si `is_email_confirmed=False`
- ❌ Falla si `is_deleted=True`

### **Flujo de Autenticación**

```
Registro → Email no confirmado → Confirmar email → Login exitoso → Obtener JWT
```

## 🌐 API Endpoints

### **Gestión de Usuarios (`/api/users/`)**

| Método       | Endpoint             | Permiso            | Descripción                                        |
| ------------- | -------------------- | ------------------ | --------------------------------------------------- |
| `GET`       | `/api/users/`      | SUDO/ADMIN/USER*   | Lista usuarios según rol (*USER solo ve su perfil) |
| `POST`      | `/api/users/`      | SUDO/ADMIN         | Crear usuario (SUDO solo para crear SUDO)           |
| `GET`       | `/api/users/{id}/` | Según visibilidad | Detalle con métricas (nodos creados)               |
| `PUT/PATCH` | `/api/users/{id}/` | Según jerarquía  | Actualizar usuario                                  |
| `DELETE`    | `/api/users/{id}/` | Según jerarquía  | Soft delete (valida nodos activos)                  |

### **Auto-gestión (`/api/users/me/`)**

| Endpoint                           | Método       | Descripción                        |
| ---------------------------------- | ------------- | ----------------------------------- |
| `/api/users/me/`                 | `GET`       | Obtener perfil propio con métricas |
| `/api/users/me/update/`          | `PUT/PATCH` | Actualizar perfil propio            |
| `/api/users/me/change-password/` | `POST`      | Cambiar contraseña propia          |

### **Auditoría**

| Endpoint                           | Método | Descripción                     |
| ---------------------------------- | ------- | -------------------------------- |
| `/api/users/{id}/nodes-created/` | `GET` | Listar nodos creados por usuario |

## ⚙️ Configuración

### **settings.py**

```python
AUTH_USER_MODEL = 'users.User'
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
```

### **Variables de Entorno (SUDO inicial)**

```bash
SUDO_USERNAME=superadmin
SUDO_EMAIL=admin@system.com
SUDO_PASSWORD=SecurePass123!
```

## 🚀 Inicialización

### **1. Migraciones**

```bash
docker compose exec web python manage.py makemigrations users
docker compose exec web python manage.py migrate users
```

### **2. Crear Usuario SUDO**

```bash
# Usa variables de entorno o interactivo
docker compose exec web python manage.py setup_sudo
```

### **3. Poblar Usuarios de Prueba**

```bash
docker compose exec web python manage.py seed_users

# Crea:
# - admin_boss (ADMIN confirmado)
# - admin_pending (ADMIN no confirmado)
# - user_regular (USER confirmado)
# - user_new (USER no confirmado)
# - staff_dev (ADMIN confirmado)
```

## 🧪 Testing

### **Ejecutar Tests**

```bash
# Todos los tests del módulo
docker compose exec web python manage.py test users

# Tests específicos
docker compose exec web python manage.py test users.tests.UserSecurityTest
docker compose exec web python manage.py test users.tests.JWTAuthenticationTest
docker compose exec web python manage.py test users.tests.UserViewSetEndpointTest
```

### **Cobertura de Tests**

- ✅ Validación de regla SUDO único
- ✅ Autenticación con email/username
- ✅ Permisos por rol en endpoints
- ✅ Soft delete y validaciones
- ✅ Cambio de contraseña
- ✅ Auto-gestión de perfil

## 🔧 Comandos de Gestión

### **setup_sudo**

```bash
python manage.py setup_sudo
```

Crea el usuario SUDO inicial usando variables de entorno. Idempotente: si ya existe SUDO, no hace nada.

### **seed_users**

```bash
python manage.py seed_users
```

Pobla la base de datos con usuarios de prueba para QA/desarrollo. Password: `password123`.

## 🛡️ Seguridad

### **Características de Seguridad**

1. **Confirmación de Email Obligatoria**: Sin email confirmado = sin autenticación
2. **Soft Delete**: Eliminación lógica mantiene integridad referencial
3. **Validaciones en Múltiples Niveles**:
   - Modelo: Regla SUDO único en `save()`
   - Serializer: Validación de roles y unicidad
   - View: Permisos granulares por acción
4. **Contraseñas**: Hash automático, validación de fortaleza
5. **Auditoría**: Trackeo de nodos creados por usuario

### **Reglas de Negocio**

1. **SUDO Único**: Solo puede existir un usuario SUDO en el sistema
2. **Jerarquía Estricta**: SUDO > ADMIN > USER (sin saltos)
3. **Auto-protección**: Usuario no puede eliminarse/desactivarse a sí mismo
4. **Integridad**: No se puede eliminar usuario con nodos activos

## 📊 Auditoría y Monitoreo

### **Métricas Disponibles**

```python
# En UserDetailSerializer
{
    "nodes_created_count": 15,  # Nodos activos creados
    "role_display": "Administrador",  # Nombre legible del rol
    "last_login": "2024-01-15T09:30:00Z",
    "date_joined": "2024-01-01T12:00:00Z"
}
```

### **Endpoint de Auditoría**

```
GET /api/users/{id}/nodes-created/
```

Lista todos los nodos activos creados por un usuario específico, con permisos controlados por rol.

## 🤝 Integración con Otros Módulos

### **Con Módulo `nodes`**

```python
# Relación User → Node
user.nodes_created.all()  # Nodos creados por el usuario
node.created_by  # Usuario creador del nodo

# Validación en soft delete
if user.nodes_created.filter(is_deleted=False).exists():
    raise ValidationError("No se puede eliminar usuario con nodos activos")
```

### **Con Django Admin**

- Usuarios SUDO/ADMIN tienen acceso al admin (`is_staff=True`)
- Interface personalizada en `admin.py`
- Filtros por rol, estado de confirmación y actividad

## 🐛 Solución de Problemas

### **Error: "Ya existe un usuario SUDO"**

```bash
# Verificar usuarios SUDO existentes
docker compose exec web python manage.py shell -c "from users.models import User; print(User.objects.filter(role='SUDO').count())"

# Solución: Eliminar SUDO existente (cuidado)
docker compose exec web python manage.py shell -c "from users.models import User; User.objects.filter(role='SUDO').delete()"
```

### **Error: Usuario no puede autenticarse**

1. Verificar `is_email_confirmed=True`
2. Verificar `is_active=True`
3. Verificar `is_deleted=False`
4. Verificar credenciales correctas

### **Error: Permisos denegados**

```python
# Verificar rol del usuario
user.role  # Debe ser SUDO o ADMIN para operaciones de escritura

# Verificar permisos específicos
from users.permissions import IsAdminUserCustom
permission = IsAdminUserCustom()
permission.has_permission(request, view)
```

## 📈 Mejores Prácticas

### **Para Desarrollo**

1. Usar `seed_users` para tener datos de prueba consistentes
2. Ejecutar tests después de cambios en modelos o lógica de negocio
3. Usar `setup_sudo` para ambiente de producción

### **Para Producción**

1. Establecer `is_email_confirmed=False` por defecto en creación
2. Implementar flujo de confirmación de email
3. Monitorear creación de usuarios SUDO
4. Revisar logs de autenticación fallida

## 📚 Referencias

- **Documentación Django**: Modelos de usuario personalizados
- **DRF Simple JWT**: Autenticación JWT para Django REST Framework
- **DRF Spectacular**: Documentación OpenAPI/Swagger
- **OWASP**: Mejores prácticas de seguridad para APIs
