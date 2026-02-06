# 📂 Módulo: Nodos Jerárquicos (`nodes`)

Este módulo encapsula la lógica de negocio central para la gestión del árbol de nodos. Implementa la jerarquía, la lógica de localización (idioma/timezone), la seguridad granular por roles y las validaciones de integridad de datos.

---

## 🏗️ Estructura del Módulo

| Archivo                  | Descripción Principal                                                                                |
| :----------------------- | :---------------------------------------------------------------------------------------------------- |
| **models.py**      | Define el modelo `Node` con Autorreferencia, Soft Delete, y Auditoría.                             |
| **serializers.py** | Gestiona la transformación de datos (Números a Palabras) y la serialización recursiva (`depth`). |
| **views.py**       | Contiene el `NodeViewSet` con lógica de Caching, Permisos y Query optimizado.                      |
| **permissions.py** | Define la Matriz de Seguridad (Roles SUDO/ADMIN/USER y Confirmación de Email).                       |
| **management/**    | Contiene comandos personalizados para la inicialización automática de datos (`seed_nodes`).       |
| **tests.py**       | Suite de pruebas para Serializer, Vistas, Lógica de Borrado y Unicidad.                              |

---

## 🧠 Lógica de Negocio y Restricciones (Senior)

### 1. Jerarquía y Persistencia

* **Autorreferencia:** El campo `parent` permite la estructura de árbol (`parent` FK a `self`).
* **Soft Delete (Borrado Lógico):** El campo `is_deleted=True` oculta nodos de la API, manteniendo la integridad referencial y el historial en la DB.
* **Integridad de Unicidad:** Se utilizan `UniqueConstraint` en `models.py` para asegurar que:
  1. No existan dos nodos activos (`is_deleted=False`) con el mismo `title` bajo el mismo `parent`.
  2. No existan dos nodos activos raíz con el mismo `title`.

### 2. Lógica de Localización (Multi-Idioma y Timezone)

| Lógica                             | Implementación                   | Origen de Datos                         |
| :---------------------------------- | :-------------------------------- | :-------------------------------------- |
| **Title** (Número a Palabra) | `NodeSerializer.validate_title` | Header `Accept-Language` (ISO 639-1). |
| **Created At** (Zona Horaria) | `NodeSerializer.get_created_at` | Header `X-Timezone`.                  |

### 3. Rendimiento y Consultas

* **Consulta Jerárquica:** El `NodeViewSet.get_queryset` filtra solo nodos raíz (`parent__isnull=True`) y usa `prefetch_related('children')` para cargar todos los hijos en solo dos consultas SQL (Fix del problema N+1).
* **Profundidad Dinámica:** El `NodeSerializer.get_children` controla la recursividad por el parámetro `?depth=X` del URL, evitando bucles infinitos.
* **Caching:** El método `NodeViewSet.list` está decorado con `@cache_page(60)` para optimizar el rendimiento del listado. La caché es invalidada automáticamente en `perform_create`, `perform_update` y `destroy`.

### 4. Seguridad y Auditoría

* **Auditoría Automática:** Los métodos `perform_create` y `perform_update` asignan automáticamente los usuarios `created_by` y `updated_by` desde el `request.user`.
* **Control de Acceso:** La seguridad se aplica a nivel de Vista:
  * **LECTURA:** Requiere `IsActiveAndConfirmed` (Cualquier usuario logueado con email verificado).
  * **ESCRITURA/BORRADO:** Requiere `IsAdminUserCustom` (Roles ADMIN o SUDO con email verificado).

---

## 🔑 Endpoint Principal (API)

| Método             | URL                  | Funcionalidad                           | Permisos                     |
| :------------------ | :------------------- | :-------------------------------------- | :--------------------------- |
| **GET**       | `/api/nodes/`      | Lista el árbol jerárquico (cacheado). | LECTURA (Usuario Verificado) |
| **GET**       | `/api/nodes/{id}/` | Detalle del nodo.                       | LECTURA (Usuario Verificado) |
| **POST**      | `/api/nodes/`      | Crea un nuevo nodo.                     | ESCRITURA (ADMIN/SUDO)       |
| **PUT/PATCH** | `/api/nodes/{id}/` | Actualiza un nodo.                      | ESCRITURA (ADMIN/SUDO)       |
| **DELETE**    | `/api/nodes/{id}/` | Borrado lógico (`is_deleted=True`).  | ESCRITURA (ADMIN/SUDO)       |

---

**NOTA:** Este módulo depende de la app `users` para el modelo de usuario personalizado y las reglas de rol.
