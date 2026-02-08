# 📂 Módulo: Nodos Jerárquicos (`nodes`)

Módulo Django REST Framework para gestionar una estructura jerárquica de árbol con control de profundidad, internacionalización y manejo de zonas horarias.

---

## 🏗️ Estructura del Módulo

| Archivo                                     | Descripción Principal                                                                                               |
| :------------------------------------------ | :------------------------------------------------------------------------------------------------------------------- |
| **models.py**                         | Define el modelo `Node` con autorreferencia (`parent`), borrado lógico y restricciones de unicidad condicional. |
| **serializers.py**                    | Serializador con generación dinámica de `title` (num2words) y control recursivo de profundidad (`depth`).      |
| **views.py**                          | `NodeViewSet` con caching (180s), validación de IDs y procesamiento de headers de idioma/zona horaria.            |
| **permissions.py**                    | Permisos por acción: lectura para usuarios activos, escritura solo para ADMIN/SUDO.                                 |
| **management/commands/seed_nodes.py** | Comando para poblar la DB con una estructura jerárquica de 3-4 niveles.                                             |
| **tests.py**                          | Suite de pruebas para serialización, validaciones y lógica de negocio.                                             |

---

## 🧠 Características Principales

### 1. Estructura Jerárquica

- **Autorreferencia:** Campo `parent` (ForeignKey a `self`) para crear árboles
- **Múltiples raíces:** `parent = null` para nodos raíz
- **Borrado lógico:** `is_deleted=True` en lugar de eliminación física
- **Integridad:** Unicidad de `content` por nivel de parentesco

### 2. Internacionalización Dinámica

- **Título generado:** Campo `title` creado automáticamente usando `num2words`
- **Idiomas soportados:** `en`, `es`, `fr`, `de`, `it`, `pt`, `ru`, `ar`
- **Header requerido:** `Accept-Language` (ej: `es`, `fr`, `de`)

### 3. Zona Horaria Personalizada

- **Fecha adaptativa:** `created_at` se convierte a la zona horaria solicitada
- **Header requerido:** `Time-Zone` (ej: `America/New_York`, `Europe/Madrid`, `Asia/Tokyo`)
- **Fallback a UTC:** Si la zona no es válida
- **Normalización automática:** Convierte abreviaturas (EST, CET) a formatos IANA

### 4. Control de Profundidad Recursiva

- **Parámetro opcional:** `?depth=N` en cualquier endpoint GET
- **Valores especiales:**
  - `depth=0`: Sin hijos
  - `depth=1`: Solo hijos directos (default)
  - `depth=2`: Hijos + nietos
  - `depth=-1`: Todos los niveles (limitado a 10 por seguridad)
- **Sin parámetro:** Comportamiento por defecto (solo hijos directos)

---

## 🔑 Endpoints API

### **Endpoints Principales**

| Método          | URL                  | Descripción                | Permisos            |
| ---------------- | -------------------- | --------------------------- | ------------------- |
| **GET**    | `/api/nodes/`      | Lista nodos raíz           | Usuario autenticado |
| **GET**    | `/api/nodes/{id}/` | Obtiene nodo específico    | Usuario autenticado |
| **POST**   | `/api/nodes/`      | Crea nuevo nodo             | ADMIN/SUDO          |
| **PATCH**  | `/api/nodes/{id}/` | Actualiza nodo parcialmente | ADMIN/SUDO          |
| **DELETE** | `/api/nodes/{id}/` | Borrado lógico             | ADMIN/SUDO          |

### **Endpoints Especializados**

| Método       | URL                              | Descripción                    |
| ------------- | -------------------------------- | ------------------------------- |
| **GET** | `/api/nodes/{id}/descendants/` | Obtiene todos los descendientes |
| **GET** | `/api/trees/`                  | Obtiene árboles completos      |

### **Parámetros de Consulta**

| Parámetro        | Valores          | Descripción                             | Ejemplo        |
| ----------------- | ---------------- | ---------------------------------------- | -------------- |
| **depth**   | 0, 1, 2, ..., -1 | Controla niveles de profundidad          | `?depth=2`   |
| **root_id** | número          | Para `/api/trees/`, árbol específico | `?root_id=5` |

### **Headers Personalizados**

| Header                    | Valores Ejemplo                                         | Propósito                       |
| ------------------------- | ------------------------------------------------------- | -------------------------------- |
| **Accept-Language** | `es`, `fr`, `de`, `en`                          | Idioma para campo `title`      |
| **Time-Zone**       | `America/New_York`, `Europe/Madrid`, `Asia/Tokyo` | Zona horaria para `created_at` |

---

## 📊 Estructura de Respuesta

### **Ejemplo de Nodo (JSON):**

```json
{
  "id": 1,
  "content": "Departamento de Tecnología",
  "title": "uno",  // Generado del ID según Accept-Language
  "parent": null,   // null para raíces
  "children": [     // Array controlado por ?depth
    {
      "id": 2,
      "content": "Equipo Desarrollo",
      "title": "dos",
      "parent": 1,
      "children": []  // Vacío si depth=1
    }
  ],
  "created_at": "2024-01-15 10:00:00"  // Formateado según Time-Zone
}
```

### **Ejemplo con Profundidad 2:**

```bash
GET /api/nodes/1/?depth=2
Accept-Language: es
Time-Zone: Europe/Madrid
```

---

## 🔐 Permisos y Seguridad

### **Modelo de Permisos:**

- **GET/LIST:** Usuario autenticado + email confirmado + activo
- **POST/PUT/PATCH/DELETE:** Rol `ADMIN` o `SUDO` + email confirmado

### **Restricciones de Negocio:**

1. **ID Validation:** Solo IDs ≥ 1 aceptados
2. **Soft Delete:** No se puede eliminar nodos con hijos activos
3. **Auto-referencia:** Un nodo no puede ser su propio padre
4. **Unicidad:** No puede haber dos nodos con mismo `content` bajo mismo `parent`

---

## ⚡ Rendimiento y Caching

### **Estrategia de Cache:**

- **Duración:** 180 segundos (3 minutos)
- **Alcance:** Solo endpoint `GET /api/nodes/`
- **Invalidación:** Automática en operaciones de escritura
- **Diferenciación:** Cache separado por idioma, zona horaria y parámetro `depth`

### **Optimizaciones:**

- **Validación temprana:** IDs se validan antes de consultar DB
- **Profundidad controlada:** Límite de 10 niveles para `depth=-1`
- **Querysets eficientes:** Exclusión automática de nodos eliminados

---

## 🌐 Internacionalización

### **Idiomas Soportados:**

```python
['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ar']
```

### **Ejemplos de Conversión:**

| ID | Español (`es`) | Francés (`fr`) | Alemán (`de`) | Inglés (`en`) |
| -- | ----------------- | ----------------- | ---------------- | ---------------- |
| 1  | uno               | un                | eins             | one              |
| 2  | dos               | deux              | zwei             | two              |
| 3  | tres              | trois             | drei             | three            |
| 10 | diez              | dix               | zehn             | ten              |
| 21 | veintiuno         | vingt et un       | einundzwanzig    | twenty-one       |

---

## 🕐 Manejo de Zonas Horarias

### **Zonas Comunes:**

```python
# Abreviaturas soportadas (se normalizan automáticamente)
EST -> America/New_York
CST -> America/Chicago  
MST -> America/Denver
PST -> America/Los_Angeles
CET -> Europe/Paris
UTC -> UTC
```

### **Diferencias de Tiempo:**

| Comparación | Diferencia  | Notas                     |
| ------------ | ----------- | ------------------------- |
| NY vs Madrid | ~6 horas    | Madrid siempre adelantado |
| NY vs Tokyo  | 13-14 horas | Depende de DST en USA     |
| UTC vs Local | Variable    | Según zona solicitada    |

---

## 🧪 Testing

### **Comando para Ejecutar Pruebas:**

```bash
# Ejecutar todas las pruebas del módulo
python manage.py test nodes

# Ejecutar pruebas específicas
python manage.py test nodes.tests.NodeAPITest
```

### **Cobertura de Pruebas:**

1. ✅ Serialización con diferentes idiomas
2. ✅ Control de profundidad (`depth` parameter)
3. ✅ Conversión de zonas horarias
4. ✅ Validaciones de negocio
5. ✅ Permisos y autorización
6. ✅ Borrado lógico

---

## 🛠️ Comandos de Gestión

### **Seeder de Datos de Prueba:**

```bash
# Crear estructura jerárquica de 3-4 niveles
python manage.py seed_nodes

# Estadísticas del seeder:
# - 7-10 nodos raíz
# - 1-3 hijos por raíz
# - 60% probabilidad de nietos
# - 30% probabilidad de bisnietos
# - Nodos con contenido numérico para pruebas
```

---

## 📁 Estructura de Archivos

```
nodes/
├── __init__.py
├── admin.py              # Configuración Django Admin
├── apps.py               # Configuración de la app
├── models.py             # Modelo Node
├── serializers.py        # Serializador con num2words
├── views.py              # ViewSet con caching
├── permissions.py        # Lógica de permisos
├── urls.py               # Rutas API
├── mixins.py             # Validación de IDs
├── tests.py              # Suite de pruebas
├── management/
│   └── commands/
│       ├── __init__.py
│       └── seed_nodes.py # Comando seeder
└── migrations/           # Migraciones de base de datos
```

---

## 🔧 Dependencias Clave

```python
# requirements.txt (parcial)
Django>=4.2
djangorestframework>=3.14
django-cors-headers>=4.0
drf-spectacular>=0.26  # Documentación OpenAPI
num2words>=0.5.10      # Conversión número→texto
pytz>=2023.3           # Zonas horarias
```
