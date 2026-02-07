# 📂 Módulo: Nodos Jerárquicos (`nodes`)

Este módulo encapsula la lógica de negocio central para la gestión de una estructura jerárquica de árbol. Implementa autorreferencia, borrado lógico, auditoría completa, validaciones de negocio, lógica de localización y optimización de rendimiento.

---

## 🏗️ Estructura del Módulo

| Archivo                                      | Descripción Principal                                                                                                         |
| :------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| **models.py**                          | Define el modelo `Node` con Autorreferencia, Soft Delete, Auditoría y Restricciones de Unicidad Condicional.                |
| **serializers.py**                     | Gestiona la transformación de datos (Números a Palabras) y la serialización recursiva limitada por profundidad (`depth`). |
| **views.py**                           | Contiene el `NodeViewSet` con Caching (60s) para listados y lógica de permisos por acción.                                 |
| **permissions.py**                     | Define los permisos mínimos requeridos para las operaciones (ej.`IsActiveAndConfirmed`).                                    |
| **management/commands/seed\_nodes.py** | Comando para poblar la DB con una estructura de árbol de 3 niveles para testing.                                              |
| **tests.py**                           | Suite de pruebas para Serializer, Vistas, Lógica de Borrado y Unicidad.                                                       |

---

## 🧠 Lógica de Negocio y Restricciones (Senior)

### 1. Jerarquía y Persistencia

- **Autorreferencia:** `parent` (FK a `self`). Múltiples raíces permitidas.
- **Soft Delete:** `is_deleted=True` oculta nodos de la API. El borrado físico está prohibido por la API.
- **Integridad de Unicidad:** Restricción en DB para títulos únicos *solo* entre nodos activos y bajo el mismo padre.

### 2. Lógica de Localización (Internacionalización)

- **Título (Número a Palabra):** `title` se convierte a texto (ej. `1` → `"uno"`) usando `num2words` basado en el header **`Accept-Language`** (ISO 639-1).
- **Fecha (`created_at`):** Se convierte de UTC a la zona horaria solicitada en el header **`X-Timezone`**.

### 3. Rendimiento

- **Caché:** El endpoint `GET /api/nodes/` está cacheado por 60 segundos. La caché se invalida automáticamente en cualquier operación de escritura (`POST`, `PUT`, `PATCH`, `DELETE`).
- **Consultas Optimizadas:** Uso de `prefetch_related` para evitar el problema N+1 en listados jerárquicos.

### 4. Seguridad y Auditoría

- **Auditoría:** Los nodos rastrean al usuario responsable de su creación (`created_by`) y última actualización (`updated_by`).
- **Control de Acceso (Permisos):**
  - **LECTURA:** Requiere usuario autenticado, activo y con email confirmado.
  - **ESCRITURA/BORRADO:** Requiere rol `ADMIN` o `SUDO`.

---

## 🔑 Endpoints API

| Método          | URL                  | Funcionalidad                                     | Permisos                     |
| :--------------- | :------------------- | :------------------------------------------------ | :--------------------------- |
| **GET**    | `/api/nodes/`      | Lista raíces, respeta `depth` y aplica caché. | Lectura (Usuario Verificado) |
| **POST**   | `/api/nodes/`      | Crea nuevo nodo (con auditoría).                 | Escritura (ADMIN/SUDO)       |
| **DELETE** | `/api/nodes/{id}/` | Borrado lógico (`soft_delete`).                | Escritura (ADMIN/SUDO)       |

### Parámetros Importantes

- **Query Param:** `?depth={X}` (Controla la profundidad de la respuesta JSON).
- **Header:** `Accept-Language` (Para traducción del título).
- **Header:** `X-Timezone` (Para conversión de fechas).

---

## 🧪 Testing y Validación

El módulo cuenta con suite de pruebas que cubren:

1. Serialización (Conversión numérica).
2. Validación de unicidad por nivel.
3. Control de profundidad (`depth`).
4. Lógica de **Soft Delete** (Verifica que no se borra si tiene hijos activos).

### Ejecución de Pruebas

```bash
# Ejecutar solo las pruebas del módulo Nodes
docker compose exec web python manage.py test nodes --noinput
```


<pre class="vditor-reset" placeholder="" contenteditable="true" spellcheck="false"><hr data-block="0"/></pre>

## 🛠️ Comandos de Gestión

### Precarga de Datos

Este comando ejecuta el seeder para poblar la base de datos con datos de prueba complejos.

```bash
# Crea una estructura de árbol de 3 niveles con datos de prueba 
# (incluyendo títulos numéricos para probar la conversión a palabras).
python manage.py seed_nodes
```


<pre class="vditor-reset" placeholder="" contenteditable="true" spellcheck="false"><hr data-block="0"/></pre>

**Versión del Módulo:** 1.0.0
**Dependencias Clave:** `num2words`, `pytz`, `drf-spectacular` (para documentación)
