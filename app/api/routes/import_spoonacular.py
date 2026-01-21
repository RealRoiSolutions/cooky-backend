from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.integrations.spoonacular_client import spoonacular_client
from app.models.recipe import ExternalRecipe, RecipeTranslation, RecipeIngredient
from app.models.ingredient import Ingredient, IngredientTranslation
from app.models.translation import TranslationJob
from app.schemas.recipe import RecipeImportResponse
from app.services.normalization import normalize_ingredient_name
from app.core.config import settings

router = APIRouter()

@router.post("/import-recipe/{spoonacular_id}", response_model=RecipeImportResponse)
async def import_recipe(
    spoonacular_id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    # 1. Fetch from Spoonacular (ONLY here)
    try:
        data = await spoonacular_client.get_recipe_information(int(spoonacular_id))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch from Spoonacular: {str(e)}")

    # 2. Check or Create ExternalRecipe
    stmt = select(ExternalRecipe).where(
        ExternalRecipe.source == "spoonacular",
        ExternalRecipe.external_id == str(spoonacular_id)
    )
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        recipe = ExternalRecipe(
            source="spoonacular",
            external_id=str(spoonacular_id),
            title_original=data.get("title", ""),
            image_url=data.get("image", ""),
            servings=data.get("servings", 1),
            diets=data.get("diets", []),
            # nutrition_totals_per_serving could be calculated or taken from Spoonacular if properly parsed
            # For MVP, we presume Spoonacular structure or leave null
            instructions_raw=data.get("instructions", ""),
            raw_json=data
        )
        if data.get("nutrition") and data["nutrition"].get("nutrients"):
             # Simple macro extraction
             macros = {}
             for n in data["nutrition"]["nutrients"]:
                 name = n["name"].lower()
                 if name in ["calories", "protein", "carbohydrates", "fat"]: # Adjust names as needed
                     macros[name] = n["amount"]
             recipe.nutrition_totals_per_serving = macros
             
        db.add(recipe)
        await db.commit()
        await db.refresh(recipe)
        
        # Create Translation Job For Recipe
        db.add(TranslationJob(entity_type="recipe", entity_id=recipe.id, target_lang="es", status="pending"))

    # 3. Process Ingredients
    ingredients_processed = 0
    raw_ingredients = data.get("extendedIngredients", [])
    
    for raw_ing in raw_ingredients:
        # Normalize
        original_name = raw_ing.get("name", "")
        canonical = normalize_ingredient_name(original_name)
        
        if not canonical:
            continue
            
        # Find or Create Ingredient
        stmt_ing = select(Ingredient).where(Ingredient.canonical_name == canonical)
        res_ing = await db.execute(stmt_ing)
        ingredient = res_ing.scalar_one_or_none()
        
        if not ingredient:
            # Create new ingredient
            spoon_id = raw_ing.get("id")
            source_ids = {"spoonacular_id": spoon_id} if spoon_id else {}
            
            nutrition_100g = None
            if spoon_id:
                try:
                    ing_data = await spoonacular_client.get_ingredient_information(
                        ingredient_id=spoon_id, amount=100, unit="g"
                    )
                    if ing_data.get("nutrition") and ing_data["nutrition"].get("nutrients"):
                        macros = {}
                        for n in ing_data["nutrition"]["nutrients"]:
                            name = n["name"].lower()
                            if name in ["calories", "protein", "carbohydrates", "fat"]: 
                                macros[name] = n["amount"]
                        nutrition_100g = macros
                except Exception as e:
                    print(f"Failed to fetch nutrition for ingredient {spoon_id}: {e}")

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
            
            # Translation Job
            db.add(TranslationJob(entity_type="ingredient", entity_id=ingredient.id, target_lang="es", status="pending"))
            
        # Check if existing ingredient needs nutrition backfill
        elif ingredient.nutrition_per_100g is None:
            spoon_id = raw_ing.get("id")
            # Only if we have a spoon_id from the current raw data or saved in source_ids
            # (Raw data is safer as source_ids is JSONB)
            if spoon_id:
                try:
                    ing_data = await spoonacular_client.get_ingredient_information(
                        ingredient_id=spoon_id, amount=100, unit="g"
                    )
                    if ing_data.get("nutrition") and ing_data["nutrition"].get("nutrients"):
                        macros = {}
                        for n in ing_data["nutrition"]["nutrients"]:
                            name = n["name"].lower()
                            if name in ["calories", "protein", "carbohydrates", "fat"]: 
                                macros[name] = n["amount"]
                        
                        ingredient.nutrition_per_100g = macros
                        # Update source_ids if missing
                        if not ingredient.source_ids:
                            ingredient.source_ids = {}
                        if "spoonacular_id" not in ingredient.source_ids:
                             ingredient.source_ids["spoonacular_id"] = spoon_id
                             
                        db.add(ingredient)
                        await db.commit()
                        await db.refresh(ingredient)
                except Exception as e:
                    print(f"Failed to backfill nutrition for ingredient {spoon_id}: {e}")
        
        # Link RecipeIngredient
        # Check uniqueness for this recipe
        stmt_link = select(RecipeIngredient).where(
            RecipeIngredient.recipe_id == recipe.id,
            RecipeIngredient.ingredient_id == ingredient.id
        )
        res_link = await db.execute(stmt_link)
        link = res_link.scalar_one_or_none()
        
        if not link:
            link = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                amount=raw_ing.get("amount"),
                unit=raw_ing.get("unit"),
                note=raw_ing.get("original")
            )
            db.add(link)
            ingredients_processed += 1
            
    await db.commit()
    
    return RecipeImportResponse(
        recipe_id=recipe.id,
        title=recipe.title_original,
        ingredients_count=ingredients_processed,
        status="success"
    )
