import asyncio
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.recipe import RecipeTranslation, ExternalRecipe
from app.models.ingredient import IngredientTranslation

async def check():
    async with AsyncSessionLocal() as db:
        # Count recipes
        result = await db.execute(select(func.count(ExternalRecipe.id)))
        recipe_count = result.scalar()
        
        # Count recipe translations
        result = await db.execute(select(func.count(RecipeTranslation.id)).where(RecipeTranslation.lang == "es"))
        recipe_trans_count = result.scalar()
        
        # Count ingredient translations
        result = await db.execute(select(func.count(IngredientTranslation.id)).where(IngredientTranslation.lang == "es"))
        ing_trans_count = result.scalar()
        
        print(f"Recipes: {recipe_count}")
        print(f"Recipe Translations (ES): {recipe_trans_count}")
        print(f"Ingredient Translations (ES): {ing_trans_count}")
        
        # Show sample
        result = await db.execute(select(RecipeTranslation).where(RecipeTranslation.lang == "es").limit(3))
        for t in result.scalars():
            print(f"  - Recipe {t.recipe_id}: {t.title[:60] if t.title else 'No title'}...")

asyncio.run(check())
