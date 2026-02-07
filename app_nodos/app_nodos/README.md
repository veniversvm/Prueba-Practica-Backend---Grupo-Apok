# 🏆 API REST de Gestión de Árbol de Nodos

Este proyecto es una **API REST de nivel Senior** en Django, diseñada para gestionar un árbol jerárquico. Destaca por su arquitectura moderna, seguridad granular (JWT, Roles) y optimización de rendimiento (PgBouncer, Caching).

---

## 🎯 Resumen de Cumplimiento

El sistema cumple con todos los requerimientos funcionales y técnicos:

| Categoría                      | Funcionalidad Clave                                                                                                         |
| :------------------------------ | :-------------------------------------------------------------------------------------------------------------------------- |
| **Funcionalidad Central** | Árbol jerárquico, Conversión Numérica a Texto en `title`, Timezone Dinámico en `created_at`.                       |
| **Integridad de Datos**   | **Soft Delete** en nodos, **Auditoría** (`created_by`, `updated_by`) y **Unicidad** a nivel de nodo. |
| **Seguridad**             | Autenticación**JWT**, Roles (`SUDO`, `ADMIN`, `USER`) y validación de confirmación de email.                 |
| **Infraestructura**       | Dockerizado, uso de**PgBouncer** para *connection pooling*.                                                         |
| **Rendimiento**           | **Caching** de 60s en la lectura de nodos.                                                                            |

---

## 🧱 Stack Tecnológico

- **Backend:** Python 3.14 / Django 6.0
- **API:** Django REST Framework
- **Base de Datos:** PostgreSQL 18+
- **Middleware:** **PgBouncer** (Connection Pooling)
- **Seguridad:** JWT (SimpleJWT)
- **Testing:** Django Test Framework (Completo)
- **Documentación:** OpenAPI 3.0 (Swagger UI)

---

## 🚀 Guía de Despliegue Rápido (Automático)

El proceso de inicialización está automatizado en el `entrypoint.sh` para ser **Idempotente**.

### 1. Configuración de Entorno (`.env`)

Asegúrate de que tu archivo `.env` contenga las credenciales de DB y las de creación del usuario `SUDO` inicial:

```env
# Base de Datos
POSTGRES_DB=tree_db
POSTGRES_USER=tree_user
POSTGRES_PASSWORD=tree_password 

# SUDO Inicial (para el primer login)
SUDO_USERNAME=admin_sudo
SUDO_EMAIL=sudo@ejemplo.com
SUDO_PASSWORD=cambiame_12345
```

### 2. Ejecución

```bash
# Construye la imagen (por si hay cambios en Dockerfile/requirements) y levanta todo.
# Esto aplica migraciones, crea el SUDO, crea usuarios de prueba y carga el árbol de nodos.
docker-compose up --build -d
```

### 3. Acceso a Endpoints

| Recurso                  | URL                                  | Uso                                   |
| :----------------------- | :----------------------------------- | :------------------------------------ |
| **API Base**       | `http://localhost:8000/api/`       | Base para todos los endpoints.        |
| **Documentación** | `http://localhost:8000/api/docs/`  | Interfaz Swagger.                     |
| **Login JWT**      | `http://localhost:8000/api/token/` | POST para obtener el token de acceso. |

---

## 🌳 Módulo Clave: Gestión de Nodos (`nodes/`)

Este es el corazón funcional del proyecto.

### Modelo `Node` (Jerarquía y Auditoría)

- **Estructura:** Campos `title`, `parent` (autorreferencia), campos de auditoría (`created_by`, `updated_by`), y Soft Delete (`is_deleted`).
- **Validación:** Unicidad de `title` por nivel jerárquico y protección contra borrado si tiene hijos activos.
- **Serialización:** El Serializer realiza la **conversión numérica a texto** basada en `Accept-Language` y ajusta `created_at` basado en `X-Timezone`.

### API Endpoints (`/api/nodes/`)

| Método          | Endpoint             | Funcionalidad Principal | Permisos                     |
| :--------------- | :------------------- | :---------------------- | :--------------------------- |
| **GET**    | `/api/nodes/`      | Listar nodos raíz.     | LECTURA (Usuario Verificado) |
| **POST**   | `/api/nodes/`      | Crear nodo.             | ESCRITURA (ADMIN/SUDO)       |
| **DELETE** | `/api/nodes/{id}/` | Borrado Lógico.        | ESCRITURA (ADMIN/SUDO)       |

### Optimización

- **Caching:** El listado (`GET /api/nodes/`) está **cacheado por 60 segundos**. La caché se invalida automáticamente tras cualquier operación de escritura.
- **Consultas:** Se usa `prefetch_related` para cargar la jerarquía de forma eficiente.

---

## 🛡️ Sistema de Seguridad y Usuarios (`users/`)

### Autenticación y Roles

- **Autenticación:** JWT obligatoria. El backend custom permite login por **username o email**.
- **Validación:** **Requiere** que `is_email_confirmed=True` para cualquier acceso (incluso para obtener el token).
- **Roles:** **SUDO** (control total), **ADMIN** (gestión de usuarios/nodos), **USER** (lectura). Solo se permite **un único** usuario SUDO en el sistema.

### Endpoints de Gestión de Usuarios

- **Protegidos por Rol:** Listado, creación y modificación de usuarios están restringidos a ADMIN/SUDO.
- **Endpoints Personalizados:** Incluye rutas para el perfil propio (`/api/users/me/`) y el cambio de contraseña.
- **Auditoría de Nodos:** Endpoint customizado para ver qué nodos creó un usuario específico.

---

## 🧪 Testing y Calidad de Código

- **Suite de Tests:** Cobertura completa sobre el modelo, serializadores, lógica de seguridad (roles, sudo único, confirmación), y endpoints API (CRUD, Soft Delete).
- **Conformidad:** Código conforme a **PEP 8** y documentación detallada (`Docstrings` PEP 257) en modelos, serializers y vistas.

---

## 🔗 Archivos de Entrega

1. **Código Fuente:** [ENLACE AL REPOSITORIO GIT PÚBLICO]
2. **Guía de Pruebas:** Archivo `TEST_GUIA.txt` adjunto.
3. **Documentación Interactiva:** Disponible en `http://localhost:8000/api/docs/`

---

**¡Entrega finalizada!**
