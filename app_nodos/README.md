
# 🌳 Sistema de Gestión de Árboles Jerárquicos

## 📋 Descripción del Proyecto

**Sistema API REST** para la gestión de árboles de nodos jerárquicos con soporte multi-idioma, timezone dinámico, seguridad basada en roles y auditoría completa. Este proyecto implementa una prueba técnica para desarrolladores backend senior.

---

## 📚 Documentación de Módulos

### **Módulos Principales**

| Módulo                | Descripción                                                                          | Documentación                      |
| ---------------------- | ------------------------------------------------------------------------------------- | ----------------------------------- |
| **🔒 `users`** | Gestión de Usuarios y Autenticación JWT con roles jerárquicos (SUDO/ADMIN/USER)    | [Ver README completo](users/README.md) |
| **📂 `nodes`** | Nodos Jerárquicos con internacionalización, control de profundidad y zonas horarias | [Ver README completo](nodes/README.md) |

---

## 🎯 Objetivos Cumplidos

### ✅ **Requerimientos Funcionales Implementados**

| Requerimiento                         | Implementación                                                | Módulo   | Estado |
| ------------------------------------- | -------------------------------------------------------------- | --------- | ------ |
| **Modelo de datos jerárquico** | Modelo `Node` con autorreferencia (`parent` FK a `self`) | `nodes` | ✅     |
| **Endpoints CRUD completos**    | API REST con Django REST Framework                             | Ambos     | ✅     |
| **Traducción multi-idioma**    | Header `Accept-Language` (ISO 639-1)                         | `nodes` | ✅     |
| **Timezone dinámico**          | Header `X-Timezone`                                          | `nodes` | ✅     |
| **Profundidad configurable**    | Parámetro `?depth=X` en queries                             | `nodes` | ✅     |
| **Validación de borrado**      | Solo nodos hoja pueden ser eliminados                          | `nodes` | ✅     |
| **Autenticación JWT**          | Login dual (email/username) con confirmación requerida        | `users` | ✅     |
| **Sistema de roles**            | Jerarquía SUDO > ADMIN > USER con permisos granulares         | `users` | ✅     |
| **Soft delete**                 | Eliminación lógica con validación de integridad             | Ambos     | ✅     |
| **Seeder automático**          | Comandos de gestión para datos iniciales                      | Ambos     | ✅     |
| **Documentación API**          | Swagger UI con drf-spectacular                                 | Ambos     | ✅     |
| **Contenerización**            | Docker + Docker Compose                                        | -         | ✅     |

---

## 🏗️ Arquitectura del Sistema

### **Estructura del Proyecto**

```
app_nodos/
├── app_nodos/          # Configuración principal del proyecto
├── middleware/         # Middleware personalizado (timezone)
├── nodes/             # 📂 Módulo de gestión de árboles jerárquicos
├── users/             # 🔒 Módulo de gestión de usuarios y autenticación
├── docker/            # Configuración Docker
├── postgres/          # Configuración PostgreSQL
├── docker-compose.yml # Orquestación de contenedores
├── Dockerfile         # Imagen de la aplicación
├── requirements.txt   # Dependencias Python
└── README.md          # Esta documentación
```

### **Tecnologías Principales**

- **Backend**: Django 6.0 + Django REST Framework
- **Base de datos**: PostgreSQL 15 + PgBouncer (connection pooling)
- **Autenticación**: JWT (Simple JWT) con backend dual
- **Internacionalización**: num2words para conversión número→texto
- **Zonas horarias**: pytz con middleware personalizado
- **Documentación**: OpenAPI 3.0 + Swagger UI (drf-spectacular)
- **Contenerización**: Docker + Docker Compose
- **Testing**: Django Test Framework con cobertura completa

---

## 🔗 Integración entre Módulos

### **Relaciones Clave**

```python
# users.models.User → nodes.models.Node
user.nodes_created.all()        # Nodos creados por el usuario
node.created_by                 # Usuario creador del nodo

# Validación cruzada en soft delete
if user.nodes_created.filter(is_deleted=False).exists():
    raise ValidationError("No se puede eliminar usuario con nodos activos")
```

### **Flujo de Autenticación Unificado**

```
Registro (users) → Confirmación email → Login JWT → Acceso a nodos
```

### **Jerarquía de Permisos**

```
SUDO → Puede todo (usuarios + nodos)
ADMIN → Puede gestionar USER y nodos
USER → Solo lectura propia y nodos propios
```

---

## 🚀 Inicio Rápido

### **Prerrequisitos**

- Docker 20.10+
- Docker Compose 2.20+

### **Ejecutar el Proyecto**

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd app_nodos

# 2. Copiar variables de entorno
cp env.example.txt .env
# Editar .env según necesidades

# 3. Iniciar todos los servicios
docker-compose up --build

# 4. Acceder a la aplicación
# API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
# Docs: http://localhost:8000/api/docs/
```

### **Variables de Entorno (.env)**

```env
# PostgreSQL
POSTGRES_DB=tree_db
POSTGRES_USER=tree_user
POSTGRES_PASSWORD=tree_password

# Usuario SUDO inicial
SUDO_USERNAME=admin
SUDO_EMAIL=admin@system.com
SUDO_PASSWORD=Admin123!
```

---

## 📊 Características por Módulo

### **🔒 Módulo `users` - Características Principales**

| Característica                      | Descripción                          |
| ------------------------------------ | ------------------------------------- |
| **Login dual**                 | Autenticación con email o username   |
| **Roles jerárquicos**         | SUDO (único) > ADMIN > USER          |
| **Email confirmado requerido** | Sin confirmación = sin acceso        |
| **Soft delete**                | Eliminación lógica con validaciones |
| **Auto-gestión**              | Endpoints `/me/` para auto-gestión |
| **Auditoría**                 | Trackeo de nodos creados por usuario  |
| **Comandos CLI**               | `setup_sudo`, `seed_users`        |

### **📂 Módulo `nodes` - Características Principales**

| Característica                  | Descripción                                  |
| -------------------------------- | --------------------------------------------- |
| **Estructura jerárquica** | Árbol con parent self-referential            |
| **Internacionalización**  | `title` generado con num2words en 8 idiomas |
| **Zona horaria dinámica** | `created_at` formateado según header       |
| **Control de profundidad** | Parámetro `?depth` (0, 1, 2, ..., -1)      |
| **Caching estratégico**   | 180s para listados con diferenciación        |
| **Validación de borrado** | Solo nodos hoja pueden eliminarse             |
| **Comando CLI**            | `seed_nodes` para estructura de prueba      |

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
| --------- | ---------------------------------- | --------------------- | ---------------------------------------- |
| `GET`   | `/api/users/`                    | SUDO/ADMIN/USER*      | Lista usuarios (*USER solo ve su perfil) |
| `POST`  | `/api/users/`                    | SUDO/ADMIN            | Crear usuario                            |
| `GET`   | `/api/users/me/`                 | Cualquier autenticado | Mi perfil con métricas                  |
| `PATCH` | `/api/users/me/update/`          | Cualquier autenticado | Actualizar mi perfil                     |
| `POST`  | `/api/users/me/change-password/` | Cualquier autenticado | Cambiar contraseña                      |
| `GET`   | `/api/users/{id}/nodes-created/` | Según visibilidad    | Auditoría de nodos creados              |

### **🌳 Gestión de Nodos**

| Método    | Endpoint                         | Permiso             | Headers Especiales                 |
| ---------- | -------------------------------- | ------------------- | ---------------------------------- |
| `GET`    | `/api/nodes/`                  | Usuario autenticado | `Accept-Language`, `Time-Zone` |
| `GET`    | `/api/nodes/{id}/`             | Usuario autenticado | `Accept-Language`, `Time-Zone` |
| `POST`   | `/api/nodes/`                  | ADMIN/SUDO          | -                                  |
| `PATCH`  | `/api/nodes/{id}/`             | ADMIN/SUDO          | -                                  |
| `DELETE` | `/api/nodes/{id}/`             | ADMIN/SUDO          | -                                  |
| `GET`    | `/api/nodes/{id}/descendants/` | Usuario autenticado | `Accept-Language`, `Time-Zone` |
| `GET`    | `/api/trees/`                  | Usuario autenticado | `Accept-Language`, `Time-Zone` |

### **Parámetros de Consulta (`nodes`)**

| Parámetro  | Valores          | Descripción           | Ejemplo        |
| ----------- | ---------------- | ---------------------- | -------------- |
| `depth`   | 0, 1, 2, ..., -1 | Niveles de profundidad | `?depth=2`   |
| `root_id` | número          | Árbol específico     | `?root_id=5` |

### **Headers Personalizados**

| Header              | Valores Ejemplo                         | Módulo   | Propósito                       |
| ------------------- | --------------------------------------- | --------- | -------------------------------- |
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
- ✅ Permisos por rol en endpoints
- ✅ Soft delete y validaciones
- ✅ Cambio de contraseña
- ✅ Auto-gestión de perfil

#### **📂 Módulo `nodes`**

- ✅ Serialización con diferentes idiomas
- ✅ Control de profundidad (`depth` parameter)
- ✅ Conversión de zonas horarias
- ✅ Validaciones de negocio
- ✅ Permisos y autorización
- ✅ Borrado lógico

---

## ⚡ Rendimiento y Optimización

### **Estrategias Implementadas**

| Estrategia                        | Módulo   | Beneficio                                 |
| --------------------------------- | --------- | ----------------------------------------- |
| **Caching 180s**            | `nodes` | Reduce carga en listados frecuentes       |
| **Connection pooling**      | Ambos     | PgBouncer para alta concurrencia          |
| **Query optimization**      | Ambos     | `select_related` + `prefetch_related` |
| **Validación temprana**    | `nodes` | IDs válidos antes de consultar DB        |
| **Lazy loading controlado** | `nodes` | Serialización recursiva por `depth`    |
| **Indexing estratégico**   | Ambos     | Índices en campos de búsqueda           |

### **Estadísticas de Performance**

- **Tiempo de respuesta API**: < 200ms (listados con caché)
- **Concurrencia**: Soporte para 100+ conexiones simultáneas
- **Memoria**: Uso optimizado con connection pooling
- **Escalabilidad**: Stateless architecture con JWT

---

## 🛡️ Seguridad

### **Características de Seguridad**

| Característica                      | Módulo   | Descripción                               |
| ------------------------------------ | --------- | ------------------------------------------ |
| **JWT con expiración**        | `users` | 60 minutos acceso, 1 día refresh          |
| **Email confirmado requerido** | `users` | Doble factor implícito                    |
| **Único usuario SUDO**        | `users` | Regla de negocio estricta                  |
| **Soft delete**                | Ambos     | Previene pérdida de datos                 |
| **Auditoría completa**        | Ambos     | `created_by`, `updated_by`, timestamps |
| **Validación de input**       | Ambos     | Serializers con validaciones estrictas     |
| **CORS configurado**           | Ambos     | Solo dominios permitidos en producción    |
| **Jerarquía de permisos**     | Ambos     | SUDO > ADMIN > USER sin saltos             |

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
| --------- | --------------------------- | --------- | ---------------------------------- |
| Alta      | **Email service**     | `users` | Verificación de email automática |
| Alta      | **File uploads**      | `nodes` | Adjuntar documentos a nodos        |
| Media     | **Search engine**     | `nodes` | Búsqueda full-text en títulos    |
| Media     | **Export/Import**     | Ambos     | JSON/CSV para backup               |
| Baja      | **WebSocket**         | Ambos     | Actualizaciones en tiempo real     |
| Baja      | **Metrics dashboard** | Ambos     | Estadísticas de uso               |

### **Escalabilidad**

- **Horizontal scaling**: Stateless con JWT
- **Database sharding**: Por tenant o región
- **CDN integration**: Para archivos estáticos
- **Queue system**: Para tareas asíncronas (Celery + Redis)
- **Microservicios**: Separación de módulos si crece la complejidad

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
- **Type hints**: Donde sea aplicable
- **Docstrings**: Documentación en funciones/métodos importantes
- **Commits semánticos**: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

---

## 📞 Soporte y Recursos

### **Recursos Disponibles**

| Recurso                                    | URL                                 | Descripción               |
| ------------------------------------------ | ----------------------------------- | -------------------------- |
| **Documentación API**               | `http://localhost:8000/api/docs/` | Swagger UI interactivo     |
| **Panel de Admin**                   | `http://localhost:8000/admin/`    | Django Admin               |
| **Health Check**                     | `http://localhost:8000/api/`      | Estado del sistema         |
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
3. Verificar headers están en request (no query params)

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- **Django Community**: Por el excelente framework
- **DRF Team**: Por las herramientas REST
- **PostgreSQL Team**: Por la base de datos robusta
- **Docker Team**: Por la contenerización
- **Contribuidores**: Por mejoras y reportes de issues

---

**Versión**: 1.0.0
**Última actualización**: Febrero 2026
**Mantenido por**: Francisco A. Hernandez S. (github @veniversvm)
**Documentación módulos**:

- [🔒 Módulo Users](users/README.md)
- [📂 Módulo Nodes](nodes/README.md)
