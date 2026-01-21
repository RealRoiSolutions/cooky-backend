"""
Reset all translation jobs to pending and clear existing translations
so they get re-translated with DeepL.
"""
import asyncio
from sqlalchemy import select, update, delete
from app.db.session import AsyncSessionLocal
from app.models.translation import TranslationJob
from app.models.ingredient import IngredientTranslation
from app.models.recipe import RecipeTranslation

async def reset_translations():
    async with AsyncSessionLocal() as db:
        # Delete existing translations
        await db.execute(delete(IngredientTranslation).where(IngredientTranslation.lang == "es"))
        await db.execute(delete(RecipeTranslation).where(RecipeTranslation.lang == "es"))
        
        # Reset all jobs to pending
        await db.execute(
            update(TranslationJob)
            .where(TranslationJob.target_lang == "es")
            .values(status="pending")
        )
        
        await db.commit()
        
        # Count
        result = await db.execute(
            select(TranslationJob).where(TranslationJob.status == "pending")
        )
        jobs = result.scalars().all()
        print(f"✅ Reset complete! {len(jobs)} translation jobs ready to process.")

asyncio.run(reset_translations())
