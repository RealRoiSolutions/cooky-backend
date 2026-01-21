"""
Script to import 20 recipes from Spoonacular API with FULL details.
Makes individual calls to get_recipe_information for complete data.
"""
import asyncio
import httpx
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.recipe import ExternalRecipe, RecipeTranslation, RecipeIngredient
from app.models.ingredient import Ingredient, IngredientTranslation
from app.models.translation import TranslationJob
from app.services.normalization import normalize_ingredient_name
from app.core.config import settings

API_KEY = settings.SPOONACULAR_API_KEY
BASE_URL = "https://api.spoonacular.com"


async def search_recipe_ids(number: int = 20):
    """Search for recipe IDs."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "apiKey": API_KEY,
            "number": number,
            "sort": "popularity",
            "instructionsRequired": "true",
        }
        response = await client.get(f"{BASE_URL}/recipes/complexSearch", params=params)
        response.raise_for_status()
        data = response.json()
        
        recipe_ids = [r["id"] for r in data.get("results", [])]
        print(f"Found {len(recipe_ids)} recipe IDs")
        return recipe_ids


async def fetch_full_recipe(recipe_id: int):
    """Get full recipe information including ingredients."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "apiKey": API_KEY,
            "includeNutrition": "true",
        }
        response = await client.get(f"{BASE_URL}/recipes/{recipe_id}/information", params=params)
        response.raise_for_status()
        return response.json()


async def fetch_ingredient_nutrition(ingredient_id: int):
    """Get ingredient nutrition per 100g."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {
            "apiKey": API_KEY,
            "amount": 100,
            "unit": "g"
        }
        try:
            response = await client.get(
                f"{BASE_URL}/food/ingredients/{ingredient_id}/information",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ⚠️ Failed to get nutrition for ingredient {ingredient_id}: {e}")
            return None


async def import_single_recipe(db, recipe_data: dict):
    """Import a single recipe with all its ingredients."""
    external_id = str(recipe_data["id"])
    title = recipe_data.get("title", "Unknown")
    
    # Check if already exists
    stmt = select(ExternalRecipe).where(
        ExternalRecipe.source == "spoonacular",
        ExternalRecipe.external_id == external_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing recipe with full data
        print(f"🔄 Updating: {title}")
        recipe = existing
        recipe.instructions_raw = recipe_data.get("instructions", "")
        recipe.diets = recipe_data.get("diets", [])
        
        # Update nutrition
        if recipe_data.get("nutrition") and recipe_data["nutrition"].get("nutrients"):
            macros = {}
            for n in recipe_data["nutrition"]["nutrients"]:
                name = n["name"].lower()
                if name in ["calories", "protein", "carbohydrates", "fat"]:
                    macros[name] = n["amount"]
            recipe.nutrition_totals_per_serving = macros if macros else recipe.nutrition_totals_per_serving
        
        await db.commit()
    else:
        print(f"📥 Importing: {title}")
        
        # Extract nutrition per serving
        nutrition = {}
        if recipe_data.get("nutrition") and recipe_data["nutrition"].get("nutrients"):
            for n in recipe_data["nutrition"]["nutrients"]:
                name = n["name"].lower()
                if name in ["calories", "protein", "carbohydrates", "fat"]:
                    nutrition[name] = n["amount"]
        
        # Create recipe
        recipe = ExternalRecipe(
            source="spoonacular",
            external_id=external_id,
            title_original=title,
            image_url=recipe_data.get("image"),
            servings=recipe_data.get("servings", 1),
            diets=recipe_data.get("diets", []),
            nutrition_totals_per_serving=nutrition if nutrition else None,
            instructions_raw=recipe_data.get("instructions", ""),
            raw_json=recipe_data
        )
        db.add(recipe)
        await db.commit()
        await db.refresh(recipe)
        
        # Create translation job
        db.add(TranslationJob(entity_type="recipe", entity_id=recipe.id, target_lang="es", status="pending"))
    
    # Process ingredients
    raw_ingredients = recipe_data.get("extendedIngredients", [])
    print(f"   Processing {len(raw_ingredients)} ingredients...")
    
    ingredients_added = 0
    for raw_ing in raw_ingredients:
        original_name = raw_ing.get("name", "")
        canonical = normalize_ingredient_name(original_name)
        
        if not canonical:
            continue
        
        # Find or create ingredient
        stmt_ing = select(Ingredient).where(Ingredient.canonical_name == canonical)
        res_ing = await db.execute(stmt_ing)
        ingredient = res_ing.scalar_one_or_none()
        
        spoon_id = raw_ing.get("id")
        
        if not ingredient:
            # Fetch nutrition for this ingredient
            nutrition_100g = None
            if spoon_id:
                ing_data = await fetch_ingredient_nutrition(spoon_id)
                if ing_data and ing_data.get("nutrition") and ing_data["nutrition"].get("nutrients"):
                    macros = {}
                    for n in ing_data["nutrition"]["nutrients"]:
                        name = n["name"].lower()
                        if name in ["calories", "protein", "carbohydrates", "fat"]:
                            macros[name] = n["amount"]
                    nutrition_100g = macros if macros else None
            
            source_ids = {"spoonacular_id": spoon_id} if spoon_id else {}
            
            ingredient = Ingredient(
                canonical_name=canonical,
                display_name=original_name,
                default_unit=raw_ing.get("unit"),
                source_ids=source_ids,
                nutrition_per_100g=nutrition_100g
            )
            db.add(ingredient)
            await db.commit()
            await db.refresh(ingredient)
            
            # Translation job for ingredient
            db.add(TranslationJob(entity_type="ingredient", entity_id=ingredient.id, target_lang="es", status="pending"))
        
        # Link recipe-ingredient (check if already exists)
        stmt_link = select(RecipeIngredient).where(
            RecipeIngredient.recipe_id == recipe.id,
            RecipeIngredient.ingredient_id == ingredient.id
        )
        res_link = await db.execute(stmt_link)
        
        if not res_link.scalar_one_or_none():
            link = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                amount=raw_ing.get("amount"),
                unit=raw_ing.get("unit"),
                note=raw_ing.get("original")
            )
            db.add(link)
            ingredients_added += 1
    
    await db.commit()
    print(f"   ✅ Recipe complete! {ingredients_added} new ingredients linked.")
    return recipe


async def main():
    print("=" * 60)
    print("🍳 Cooky - Spoonacular Full Recipe Import")
    print("=" * 60)
    
    # First get recipe IDs
    recipe_ids = await search_recipe_ids(20)
    
    if not recipe_ids:
        print("❌ No recipes found!")
        return
    
    async with AsyncSessionLocal() as db:
        imported = 0
        for i, recipe_id in enumerate(recipe_ids):
            print(f"\n[{i+1}/{len(recipe_ids)}] Fetching recipe {recipe_id}...")
            try:
                # Fetch full recipe details
                recipe_data = await fetch_full_recipe(recipe_id)
                await import_single_recipe(db, recipe_data)
                imported += 1
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"❌ Error importing recipe {recipe_id}: {e}")
                continue
        
        print("\n" + "=" * 60)
        print(f"✅ Import complete! {imported}/{len(recipe_ids)} recipes imported.")
        print("=" * 60)
        print("\n📝 Remember to run: python -m app.scripts.run_translation_batch")


if __name__ == "__main__":
    asyncio.run(main())
