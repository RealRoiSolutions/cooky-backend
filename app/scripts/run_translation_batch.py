import asyncio
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.models.translation import TranslationJob
from app.models.ingredient import Ingredient, IngredientTranslation
from app.models.recipe import ExternalRecipe, RecipeTranslation
from app.services.translation import translate_text

async def process_translation_jobs():
    async with AsyncSessionLocal() as session:
        # Fetch pending jobs
        result = await session.execute(
            select(TranslationJob).where(
                and_(TranslationJob.status == "pending", TranslationJob.target_lang == "es")
            ).limit(20) # Process in batches
        )
        jobs = result.scalars().all()
        
        if not jobs:
            print("No pending translation jobs found.")
            return

        print(f"Processing {len(jobs)} translation jobs...")
        
        for job in jobs:
            job.status = "in_progress"
            await session.commit() # Commit status change
            
            try:
                if job.entity_type == "ingredient":
                    ingredient = await session.get(Ingredient, job.entity_id)
                    if ingredient:
                        # Translate canonical_name
                        input_text = ingredient.display_name or ingredient.canonical_name
                        translated = await translate_text(input_text, target_lang="es")
                        
                        # Upsert Translation
                        # Check if exists
                        existing_q = await session.execute(select(IngredientTranslation).where(
                            and_(IngredientTranslation.ingredient_id == ingredient.id, IngredientTranslation.lang == "es")
                        ))
                        existing = existing_q.scalar_one_or_none()
                        
                        if existing:
                            existing.name = translated
                            existing.updated_at = datetime.utcnow() # Warning: datetime need import
                        else:
                            new_trans = IngredientTranslation(
                                ingredient_id=ingredient.id,
                                lang="es",
                                name=translated,
                                is_verified=False
                            )
                            session.add(new_trans)
                        
                        job.status = "done"

                elif job.entity_type == "recipe":
                    recipe = await session.get(ExternalRecipe, job.entity_id)
                    if recipe:
                        title_trans = await translate_text(recipe.title_original, "es")
                        instr_trans = await translate_text(recipe.instructions_raw or "", "es")
                        
                        # Upsert
                        existing_q = await session.execute(select(RecipeTranslation).where(
                            and_(RecipeTranslation.recipe_id == recipe.id, RecipeTranslation.lang == "es")
                        ))
                        existing = existing_q.scalar_one_or_none()
                        
                        if existing:
                            existing.title = title_trans
                            existing.instructions = instr_trans
                        else:
                            new_trans = RecipeTranslation(
                                recipe_id=recipe.id,
                                lang="es",
                                title=title_trans,
                                instructions=instr_trans
                            )
                            session.add(new_trans)
                        
                        job.status = "done"
                
                else:
                    job.status = "error"
                    job.error_message = f"Unknown entity_type: {job.entity_type}"
            
            except Exception as e:
                job.status = "error"
                job.error_message = str(e)
                print(f"Error processing job {job.id}: {e}")
            
            await session.commit()

if __name__ == "__main__":
    from datetime import datetime
    # Fix import if run directly
    import sys, os
    sys.path.append(os.getcwd())
    
    asyncio.run(process_translation_jobs())
