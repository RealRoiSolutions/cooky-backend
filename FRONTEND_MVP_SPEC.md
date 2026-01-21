# Frontend Task: Despensa (Pantry) MVP

**Objetivo**: Implementar la pantalla "Mi despensa" conectada al backend existente.

## Endpoints Disponibles

### 1. Listar Despensa
- **GET** `/pantry/`
- **Response**:
```json
[
  {
    "id": 2,
    "ingredient_id": 16,
    "ingredient_name": "[ES] garlic",
    "quantity": 5.0,
    "unit": "cloves"
  }
]
```

### 2. Buscar Ingredientes
- **GET** `/ingredients/search?q=...&limit=20`
- **Response**:
```json
[
  {
    "ingredient_id": 16,
    "name_es": "[ES] garlic",
    "category": null,  // e.g. "vegetable"
    "is_translation_verified": false
  }
]
```

### 3. Añadir a Despensa
- **POST** `/pantry/`
- **Body**:
```json
{
  "ingredient_id": 16,
  "quantity": 2.0,
  "unit": "unit"
}
```

### 4. Editar Item
- **PATCH** `/pantry/{id}`
- **Body** (campos opcionales):
```json
{
  "quantity": 10.0,
  "unit": "grams"
}
```

### 5. Eliminar Item
- **DELETE** `/pantry/{id}`

---

## Requisitos de UI/UX

### Vista Principal ("Mi Despensa")
1.  **Carga Inicial**: Al entrar, llamar a `GET /pantry` y mostrar la lista de ingredientes.
2.  **Lista de Items**:
    *   Mostrar `ingredient_name` (ya viene traducido si existe).
    *   Mostrar `quantity` + `unit`.
    *   Acciones: **Editar** y **Borrar**.

### Añadir Ingrediente (Modal)
1.  **Input de Búsqueda**:
    *   Texto con *debounce* que llama a `GET /ingredients/search` (min 2 chars).
2.  **Lista de Resultados**:
    *   Mostrar `name_es` (y `category` si existe).
    *   Al hacer click en uno, seleccionarlo.
3.  **Formulario de Cantidad**:
    *   Una vez seleccionado el ingrediente, pedir `quantity` y `unit`.
    *   Botón "Guardar" -> `POST /pantry`.
    *   Cerrar modal y recargar lista.

### Edición Inline o Modal
*   Permitir cambiar cantidad o unidad.
*   Llamar a `PATCH /pantry/{id}`.

### Notas
*   No implementar lógica compleja de cocina o listados de compra aún.
*   Manejar estados de `loading` y errores básicos (4xx/5xx).
