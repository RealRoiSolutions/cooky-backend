# Plan de Integración de Traducciones con DeepL

## 📊 Estimación de Caracteres (Datos Actuales)

| Contenido | Cantidad | Caracteres |
|-----------|----------|------------|
| Recetas - Títulos | 8 | ~400 |
| Recetas - Instrucciones | 8 | ~6,000 |
| Ingredientes - Nombres | ~60 | ~1,200 |
| **TOTAL** | - | **~7,600 caracteres** |

---

## 💰 Análisis de Costes

### DeepL Free Tier
| Métrica | Valor |
|---------|-------|
| Límite mensual | 500,000 caracteres |
| Uso actual | ~7,600 caracteres |
| **Uso del límite** | **1.5%** |
| Caracteres disponibles | ~492,000 |

### Capacidad restante (Free Tier)
- **Recetas adicionales**: ~600-800 recetas más
- **Ingredientes adicionales**: ~25,000 ingredientes

### DeepL Pro (si se excede el límite)
| Volumen | Coste |
|---------|-------|
| 1 millón de caracteres | $20 USD |
| Coste actual (7,600 chars) | $0.15 USD |
| 100 recetas estimadas | ~$2 USD |

---

## ✅ Conclusión de Costes

> **DENTRO DEL TIER GRATUITO** con un margen enorme (98.5% de capacidad libre).
> 
> Puedes añadir cientos de recetas sin coste alguno.

---

## 🔧 Plan de Implementación

### Archivo a modificar
`app/services/translation.py`

### Cambio requerido

```python
# ANTES (Stub actual)
async def translate_text(text: str, target_lang: str = "es") -> str:
    if not text:
        return text
    return f"[{target_lang.upper()}] {text}"  # Fake translation

# DESPUÉS (Con DeepL)
import httpx
from app.core.config import settings

async def translate_text(text: str, target_lang: str = "es") -> str:
    if not text or not text.strip():
        return text
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api-free.deepl.com/v2/translate",  # o api.deepl.com para Pro
            data={
                "auth_key": settings.DEEPL_API_KEY,
                "text": text,
                "target_lang": target_lang.upper(),
                "source_lang": "EN",  # Asumimos inglés como origen
            }
        )
        response.raise_for_status()
        result = response.json()
        return result["translations"][0]["text"]
```

### Cambios en configuración

**`app/core/config.py`**
```python
class Settings(BaseSettings):
    # ... existing settings ...
    DEEPL_API_KEY: str = ""
```

**`.env`**
```
DEEPL_API_KEY=your-api-key-here
```

### Script de traducción (sin cambios)
El script `app/scripts/run_translation_batch.py` **no necesita cambios**.
- Ya procesa jobs con `status = "pending"`
- Ya guarda en `IngredientTranslation` / `RecipeTranslation`
- Ya marca como `done` o `error`

Solo depende de `translate_text()`, que es lo único que modificamos.

---

## 🚀 Pasos para Activar

1. **Crear cuenta DeepL API** → https://www.deepl.com/pro-api
2. **Obtener API Key** (Free tier incluye 500K chars/mes)
3. **Añadir a `.env`**: `DEEPL_API_KEY=...`
4. **Modificar** `app/services/translation.py` con el código de arriba
5. **Ejecutar**: `python -m app.scripts.run_translation_batch`
6. **Verificar** que las traducciones ya no tienen prefijo `[ES]`

---

## ⚠️ Consideraciones

- **Rate Limiting**: DeepL Free tiene límites de velocidad. El script actual procesa 20 jobs por lote, suficiente.
- **Fallback**: Si la API falla, el stub actual sigue funcionando.
- **Caché**: No es necesario para este volumen, pero podría añadirse a futuro.
- **HTML en instrucciones**: DeepL preserva tags HTML automáticamente con `tag_handling=xml`.
