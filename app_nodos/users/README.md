# 🔒 Módulo: Gestión de Usuarios y Autenticación (`users`)

Este módulo implementa el sistema central de **Gestión de Identidad y Acceso (IAM)**, incluyendo un modelo de usuario extendido, autenticación JWT avanzada, y control de acceso granular basado en roles.

---

## 🏗️ Arquitectura del Módulo

| Archivo                  | Rol Principal                                                                                                       |
| :----------------------- | :------------------------------------------------------------------------------------------------------------------ |
| **models.py**      | Define el `User` customizado con roles, confirmación de email y la restricción de **SUDO único**.        |
| **backends.py**    | Implementa el `EmailOrUsernameBackend` para el login dual (email/username).                                       |
| **permissions.py** | Define las políticas de acceso basadas en roles (`IsActiveAndConfirmed`, `IsAdminUserCustom`, `IsSudoUser`). |
| **serializers.py** | Define la lógica de validación para creación/actualización, incluyendo la validación de contraseñas y roles.  |
| **views.py**       | Implementa `UserViewSet` con lógica de filtrado de datos basada en el rol del usuario autenticado.               |
| **management/**    | Contiene comandos para inicializar el SUDO (`setup_sudo`) y crear usuarios de prueba (`seed_users`).            |

---

## 🔑 Sistema de Autenticación y Seguridad

### 1. Autenticación (JWT + Backend Custom)

- **Login Dual:** El backend permite iniciar sesión con **username o email**.
- **Regla de Oro:** El login **falla** si el usuario no tiene `is_email_confirmed=True`, forzando la verificación por email.

### 2. Control de Acceso (Roles y Permisos)

El acceso a los endpoints del ViewSet está estrictamente controlado:

- **Lectura (`GET`):** Requiere autenticación y que el email esté confirmado.
- **Escritura/Eliminación (`POST`/`PUT`/`DELETE`):** Requiere rol **ADMIN** o **SUDO**.
- **Restricción de Rol SUDO:** El modelo impide la creación de más de un usuario con rol `SUDO` (validado en `User.save()`).

### 3. Auditoría y Soft Delete

- **Soft Delete:** Los usuarios eliminados (`DELETE /users/{id}`) se marcan como `is_deleted=True` en lugar de borrarse físicamente.
- **Auditoría de Nodos:** Los nodos creados rastrean al usuario (`created_by`) mediante una relación `ForeignKey`.

---

## 🌐 Endpoints API (`/api/users/`)

Todos los endpoints están protegidos por JWT.

| Acción        | URL                                | Permiso de Acceso             | Comentario Clave                                                           |
| :------------- | :--------------------------------- | :---------------------------- | :------------------------------------------------------------------------- |
| **POST** | `/api/users/`                    | ADMIN/SUDO                    | El rol `SUDO` se puede asignar solo por otro `SUDO`.                   |
| **GET**  | `/api/users/`                    | ADMIN/SUDO                    | El ADMIN no ve al `SUDO`. El USER es rechazado.                          |
| **GET**  | `/api/users/{id}/`               | USER (solo propio)/ADMIN/SUDO | Filtro de acceso basado en el ID del usuario.                              |
| **GET**  | `/api/users/{id}/nodes-created/` | Lógica de Permisos Especial  | Permite ver los nodos creados por ese usuario (USER solo si es él mismo). |
| **POST** | `/api/users/token/`              | Público                      | Genera el Token JWT.                                                       |

---

## 🚀 Inicialización y Testing

Para que el sistema esté listo para probar los permisos:

1. **Levantar Entorno:** `docker-compose up --build -d`
2. **Migrar/Seed:** El `entrypoint.sh` aplica migraciones y ejecuta los comandos `setup_sudo`, `seed_users`, y `seed_nodes`.
3. **Testear:** `docker compose exec web python manage.py test users`

---

**Responsabilidad Principal:** Gestión de Identidad, Roles, Permisos y Auditoría de Acciones.
