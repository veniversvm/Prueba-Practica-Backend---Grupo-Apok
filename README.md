# 🌳 Sistema de Gestión de Árboles Jerárquicos

## 📋 Descripción del Proyecto

**Sistema API REST** para la gestión de árboles de nodos jerárquicos con soporte multi-idioma, timezone dinámico, seguridad basada en roles y auditoría completa. Este proyecto implementa una prueba técnica para desarrolladores backend senior.

---

## 🎯 Objetivos Cumplidos

### ✅ **Requerimientos Funcionales Implementados**

| Requerimiento                         | Implementación                                                | Estado |
| ------------------------------------- | -------------------------------------------------------------- | ------ |
| **Modelo de datos jerárquico** | Modelo `Node` con autorreferencia (`parent` FK a `self`) | ✅     |
| **Endpoints CRUD completos**    | API REST con Django REST Framework                             | ✅     |
| **Traducción multi-idioma**    | Header `Accept-Language` (ISO 639-1)                         | ✅     |
| **Timezone dinámico**          | Header `X-Timezone`                                          | ✅     |
| **Profundidad configurable**    | Parámetro `?depth=X` en queries                             | ✅     |
| **Validación de borrado**      | Solo nodos hoja pueden ser eliminados                          | ✅     |
| **Seeder automático**          | Comandos de gestión para datos iniciales                      | ✅     |
| **Documentación API**          | Swagger UI con drf-spectacular                                 | ✅     |
| **Contenerización**            | Docker + Docker Compose                                        | ✅     |

---

## 🏗️ Arquitectura del Sistema

### **Estructura del Proyecto**

```
app_nodos/
├── app_nodos/          # Configuración principal del proyecto
├── nodes/             # Módulo de gestión de árboles jerárquicos
├── users/             # Módulo de gestión de usuarios y autenticación
├── docker-compose.yml # Orquestación de contenedores
├── Dockerfile        # Imagen de la aplicación
├── requirements.txt  # Dependencias Python
└── README.md         # Esta documentación
```

### **Tecnologías Principales**

- **Backend**: Django 6.0 + Django REST Framework
- **Base de datos**: PostgreSQL 15 + PgBouncer (connection pooling)
- **Autenticación**: JWT (Simple JWT)
- **Documentación**: OpenAPI 3.0 + Swagger UI
- **Contenerización**: Docker + Docker Compose
- **Testing**: Django Test Framework

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

# 2. Iniciar todos los servicios
docker-compose up --build

# 3. Acceder a la aplicación
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

## 🔧 Características Técnicas

### **1. Modelo de Datos Jerárquico**

```json
{
  "id": 1,
  "parent": null,
  "title": "one",
  "created_at": "2022-10-21T00:00:00Z",
  "updated_at": "2022-10-21T00:00:00Z",
  "created_by": 1,
  "updated_by": 1,
  "is_deleted": false
}
```

### **2. Sistema de Roles y Seguridad**

| Rol             | Permisos                                 | Descripción                          |
| --------------- | ---------------------------------------- | ------------------------------------- |
| **SUDO**  | Acceso completo                          | Super User Ops (único en el sistema) |
| **ADMIN** | CRUD de nodos, gestión de usuarios USER | Administrador                         |
| **USER**  | Solo lectura de sus propios nodos        | Usuario regular                       |

### **3. Internacionalización**

- **Idioma**: Header `Accept-Language` (ej: `en`, `es`, `fr`)
- **Timezone**: Header `X-Timezone` (ej: `America/New_York`, `Europe/Madrid`)
- **Traducción automática**: Números a palabras en el idioma seleccionado

### **4. Performance y Optimización**

- **Caché**: 180 segundos para listados de nodos
- **Query optimization**: `select_related` + `prefetch_related` para evitar N+1
- **Connection pooling**: PgBouncer para manejo eficiente de conexiones
- **Soft delete**: Borrado lógico manteniendo integridad referencial

---

## 📚 Documentación API

### **Autenticación**

```bash
# 1. Obtener token JWT
POST /api/token/
{
  "username": "admin@system.com",
  "password": "Admin123!"
}

# 2. Usar token en requests
Authorization: Bearer <access_token>
```

### **Endpoints Principales**

#### **Gestión de Nodos**

| Método       | Endpoint                 | Descripción              | Headers Especiales                  |
| ------------- | ------------------------ | ------------------------- | ----------------------------------- |
| `GET`       | `/api/nodes/`          | Listar árbol completo    | `Accept-Language`, `X-Timezone` |
| `GET`       | `/api/nodes/{id}/`     | Detalle de nodo           | `Accept-Language`, `X-Timezone` |
| `POST`      | `/api/nodes/`          | Crear nodo                | -                                   |
| `PUT/PATCH` | `/api/nodes/{id}/`     | Actualizar nodo           | -                                   |
| `DELETE`    | `/api/nodes/{id}/`     | Eliminar nodo (solo hoja) | -                                   |
| `GET`       | `/api/nodes/my-nodes/` | Mis nodos creados         | -                                   |

#### **Gestión de Usuarios**

| Método       | Endpoint                           | Descripción                 |
| ------------- | ---------------------------------- | ---------------------------- |
| `GET`       | `/api/users/`                    | Listar usuarios (según rol) |
| `POST`      | `/api/users/`                    | Crear usuario                |
| `GET`       | `/api/users/me/`                 | Mi perfil                    |
| `PUT/PATCH` | `/api/users/me/update/`          | Actualizar mi perfil         |
| `POST`      | `/api/users/me/change-password/` | Cambiar contraseña          |
| `GET`       | `/api/users/{id}/nodes-created/` | Auditoría de nodos          |

### **Parámetros de Consulta**

```bash
# Profundidad del árbol
GET /api/nodes/?depth=3

# Filtrar por padre
GET /api/nodes/?parent=1

# Buscar nodos
GET /api/nodes/?search=root

# Paginación
GET /api/nodes/?page=2&page_size=20
```

---

## 🧪 Testing

### **Ejecutar Pruebas**

```bash
# Ejecutar todas las pruebas
docker-compose exec app python manage.py test

# Pruebas específicas
docker-compose exec app python manage.py test nodes.tests
docker-compose exec app python manage.py test users.tests

# Con coverage
docker-compose exec app python -m pytest --cov=nodes --cov=users
```

### **Comandos de Gestión**

```bash
# Crear usuario SUDO inicial
docker-compose exec app python manage.py setup_sudo

# Poblar usuarios de prueba
docker-compose exec app python manage.py seed_users

# Poblar árbol de nodos
docker-compose exec app python manage.py seed_nodes

# Verificar salud del sistema
curl http://localhost:8000/api/
```

---

## 🔄 Flujos de Trabajo

### **1. Configuración Inicial**

```bash
# 1. Iniciar contenedores
docker-compose up -d

# 2. Aplicar migraciones
docker-compose exec app python manage.py migrate

# 3. Crear usuario administrador
docker-compose exec app python manage.py setup_sudo

# 4. Poblar datos de prueba
docker-compose exec app python manage.py seed_users
docker-compose exec app python manage.py seed_nodes
```

### **2. Desarrollo Local**

```bash
# Modo desarrollo (con recarga automática)
docker-compose up --build

# Acceder a la consola Django
docker-compose exec app python manage.py shell

# Ver logs en tiempo real
docker-compose logs -f app
```

### **3. Producción**

```env
# Configuración producción (.env.production)
DEBUG=False
ALLOWED_HOSTS=*.dominio.com
DJANGO_SECRET_KEY=clave_segura_produccion
```

---

## 🛡️ Seguridad y Mejores Prácticas

### **Características de Seguridad**

- ✅ **JWT con expiración**: 60 minutos acceso, 1 día refresh
- ✅ **Email confirmado requerido**: Doble factor implícito
- ✅ **Único usuario SUDO**: Regla de negocio estricta
- ✅ **Soft delete**: Previene pérdida de datos
- ✅ **Auditoría completa**: `created_by`, `updated_by`, timestamps
- ✅ **Validación de input**: Serializers con validaciones estrictas
- ✅ **CORS configurado**: Solo dominios permitidos en producción

### **Optimizaciones Implementadas**

- **Database indexing**: Índices en campos de búsqueda frecuente
- **Query optimization**: Uso de `select_related` y `prefetch_related`
- **Caching estratégico**: Listados frecuentes en caché
- **Connection pooling**: PgBouncer para alta concurrencia
- **Lazy loading**: Serialización recursiva controlada por profundidad

---

## 📊 Estructura de Datos

### **Base de Datos**

```sql
-- Ejemplo de estructura jerárquica
1 - Root (null)
├── 2 - Child 1 (parent: 1)
│   ├── 4 - Grandchild 1 (parent: 2)
│   └── 5 - Grandchild 2 (parent: 2)
└── 3 - Child 2 (parent: 1)
    └── 6 - Grandchild 3 (parent: 3)
```

### **Relaciones**

- **Usuario → Nodo**: One-to-Many (un usuario crea muchos nodos)
- **Nodo → Nodo**: Self-referential (árbol jerárquico)
- **Soft delete cascade**: Los hijos se marcan como eliminados si el padre se elimina

---

## 🔮 Roadmap y Mejoras Futuras

### **Próximas Características**

1. **Email service**: Verificación de email automática
2. **File uploads**: Adjuntar documentos a nodos
3. **Search engine**: Búsqueda full-text en títulos
4. **Export/Import**: JSON/CSV para backup
5. **WebSocket**: Actualizaciones en tiempo real
6. **Metrics dashboard**: Estadísticas de uso

### **Escalabilidad**

- **Horizontal scaling**: Stateless con JWT
- **Database sharding**: Por tenant o región
- **CDN integration**: Para archivos estáticos
- **Queue system**: Para tareas asíncronas

---

## 🤝 Contribución

### **Reportar Issues**

1. Verificar si el issue ya existe
2. Proporcionar pasos para reproducir
3. Incluir versiones y logs relevantes

### **Pull Requests**

1. Fork del repositorio
2. Crear branch descriptivo
3. Incluir tests relevantes
4. Actualizar documentación

---

## 📞 Soporte

### **Recursos**

- **Documentación API**: `http://localhost:8000/api/docs/`
- **Panel de Admin**: `http://localhost:8000/admin/`
- **Health Check**: `http://localhost:8000/api/`

### **Contacto**

- **Issues**: [GitHub Issues](link)
- **Email**: desarrollo@empresa.com
- **Slack**: #backend-support

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- **Django Community**: Por el excelente framework
- **DRF Team**: Por las herramientas REST
- **PostgreSQL Team**: Por la base de datos robusta
- **Docker Team**: Por la contenerización

---

**Versión**: 1.0.0
**Última actualización**: Febrero 2026
**Mantenido por**: Francisco A. Hernandez S. (github @veniversvm)
