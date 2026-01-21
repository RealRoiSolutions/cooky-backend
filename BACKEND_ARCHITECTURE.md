# Cooky Backend Architecture

This document describes the technical architecture of the Cooky backend, designed to be scalable, efficient, and offline-first (once imported).

## 1. Core Philosophy

*   **Offline First**: The frontend NEVER communicates directly with Spoonacular. All data is served from our local PostgreSQL database.
*   **Import on Demand**: We only fetch data from Spoonacular via specific Admin API calls. Once imported, the data belongs to us.
*   **Detailed Nutrition**: We store nutrition data at the *Ingredient* level (per 100g), allowing flexible recalculations for any recipe or diary entry.
*   **Localization**: All user-facing text (ingredient names, recipe titles) passes through a translation layer.

## 2. Technology Stack

*   **Language**: Python 3.x
*   **Framework**: FastAPI (High performance, async)
*   **Database**: PostgreSQL
*   **ORM**: SQLAlchemy (Async mode with `asyncpg`)
*   **Migrations**: Alembic
*   **External API**: Spoonacular (via `httpx` client)

## 3. Key Workflows

### 3.1. Recipe Import Flow
**Endpoint**: `POST /admin/spoonacular/import-recipe/{id}`

1.  **Fetch Recipe**: Downloads detailed recipe info from Spoonacular.
2.  **Create/Update Recipe**: Saves to `external_recipes`.
3.  **Process Ingredients**:
    *   Iterates through every ingredient.
    *   **Normalization**: Cleans the name (lowercase, unaccented) -> `canonical_name`.
    *   **Check Existence**: Looks for existing `Ingredient`.
    *   **Nutrition Backfill**: If the ingredient is new OR lacks nutrition data, calls Spoonacular (`/food/ingredients/{id}/information`) to get macros per 100g.
    *   **Link**: Creates a `RecipeIngredient` connecting Recipe ↔ Ingredient with the specific amount for that recipe.
4.  **Queue Translation**: Creates `TranslationJob` entries for the recipe and all new ingredients.

### 3.2. Public API (Frontend Reading)
**Endpoints**: `GET /recipes`, `GET /recipes/{id}`

1.  **Read Only**: Queries the local DB. Zero external API calls.
2.  **Multilingual**: Joins with `RecipeTranslation` and `IngredientTranslation`.
    *   If `lang='es'` exists, returns the translated text (e.g., "Mantequilla").
    *   Fallback: Returns the original English text (e.g., "Butter").
3.  **Performance**: Uses efficient SQL joins (`selectinload`) to prevent N+1 query problems.

### 3.3. Translation System
**Script**: `python app/scripts/run_translation_batch.py`

1.  **Async Queue**: The Import process inserts jobs into `translation_jobs` table (status: `pending`).
2.  **Batch Processing**: The script picks up pending jobs.
    *   Currently: Applies a stub translation (e.g., adds `[ES]` prefix).
    *   Future: Will call Google Translate or DeepL API.
3.  **Result Storage**: Saves the result in `ingredient_translations` or `recipe_translations`.

## 4. Data Model (Key Tables)

### `Ingredient`
The master catalog of foods.
*   `id`: Primary Key
*   `canonical_name`: Unique identifier (e.g., "skim milk").
*   `nutrition_per_100g`: JSONB (`{calories: 34, protein: 3.4, ...}`). Critical for all math.

### `ExternalRecipe`
Stores the raw recipe data.
*   `source`: "spoonacular"
*   `nutrition_totals_per_serving`: Cached totals for the specific recipe serving.

### `RecipeIngredient`
The link table (associative entity).
*   `amount`: How much of the ingredient (e.g., 200).
*   `unit`: The unit used in this recipe (e.g., "grams").

### `TranslationJob`
Manages the async translation workflow.
*   `entity_type`: "ingredient" or "recipe".
*   `status`: "pending", "done", "error".

## 5. Directory Structure

```
app/
├── api/             # API Routes & Dependencies
├── core/            # Config & Settings
├── db/              # Database Connection & Base Models
├── integrations/    # External Clients (Spoonacular)
├── models/          # SQLAlchemy Models
├── schemas/         # Pydantic Schemas (Request/Response)
├── scripts/         # Standalone Scripts (Init DB, Translation)
└── services/        # Business Logic (Normalization, Translation)
```

## 6. How to Extend

*   **Add Pantry**: Create endpoints in `app/api/routes/pantry.py` that read/write to `pantry_items` table using `Ingredient.id`.
*   **Real Translation**: Update `app/services/translation.py` to use a real API client.
*   **Search**: Add specific FTS (Full Text Search) indexes on `IngredientTranslation.name` for fast Spanish search.
