"""
Estimation of characters to translate for DeepL API cost analysis.
"""
import asyncio
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.recipe import ExternalRecipe, RecipeTranslation
from app.models.ingredient import Ingredient, IngredientTranslation

async def estimate_characters():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("📊 TRANSLATION CHARACTER ESTIMATION")
        print("=" * 60)
        
        # =====================================================
        # RECIPES
        # =====================================================
        result = await db.execute(select(ExternalRecipe))
        recipes = result.scalars().all()
        
        recipe_title_chars = 0
        recipe_instruction_chars = 0
        recipes_with_instructions = 0
        
        for r in recipes:
            if r.title_original:
                recipe_title_chars += len(r.title_original)
            if r.instructions_raw:
                recipe_instruction_chars += len(r.instructions_raw)
                recipes_with_instructions += 1
        
        print(f"\n🍳 RECIPES ({len(recipes)} total)")
        print(f"   Titles: {recipe_title_chars:,} characters")
        print(f"   Instructions: {recipe_instruction_chars:,} characters ({recipes_with_instructions} recipes with instructions)")
        print(f"   Subtotal: {recipe_title_chars + recipe_instruction_chars:,} characters")
        
        # =====================================================
        # INGREDIENTS
        # =====================================================
        result = await db.execute(select(Ingredient))
        ingredients = result.scalars().all()
        
        ingredient_chars = 0
        for i in ingredients:
            name = i.display_name or i.canonical_name
            if name:
                ingredient_chars += len(name)
        
        print(f"\n🥕 INGREDIENTS ({len(ingredients)} total)")
        print(f"   Names: {ingredient_chars:,} characters")
        
        # =====================================================
        # TOTALS
        # =====================================================
        total_chars = recipe_title_chars + recipe_instruction_chars + ingredient_chars
        
        print(f"\n" + "=" * 60)
        print(f"📈 TOTAL CHARACTERS TO TRANSLATE: {total_chars:,}")
        print("=" * 60)
        
        # =====================================================
        # COST ANALYSIS
        # =====================================================
        print(f"\n💰 DEEPL API COST ANALYSIS")
        print("-" * 40)
        
        # DeepL Free tier
        free_limit = 500_000
        free_remaining = free_limit - total_chars
        free_percentage = (total_chars / free_limit) * 100
        
        print(f"   DeepL Free Tier: 500,000 chars/month")
        print(f"   Current usage: {total_chars:,} chars ({free_percentage:.2f}%)")
        print(f"   Remaining: {free_remaining:,} chars")
        
        # How many more recipes could we add?
        avg_chars_per_recipe = (recipe_title_chars + recipe_instruction_chars) / max(len(recipes), 1)
        recipes_remaining = int(free_remaining / avg_chars_per_recipe) if avg_chars_per_recipe > 0 else 0
        
        print(f"\n   Average chars per recipe: {avg_chars_per_recipe:,.0f}")
        print(f"   📊 Can add ~{recipes_remaining} more recipes without exceeding free tier")
        
        # Pro tier cost
        pro_rate = 20  # USD per 1M characters
        pro_cost = (total_chars / 1_000_000) * pro_rate
        
        print(f"\n   DeepL Pro rate: $20/million characters")
        print(f"   Cost for current volume: ${pro_cost:.4f} USD")
        
        print("\n" + "=" * 60)
        print("✅ CONCLUSION")
        print("=" * 60)
        if total_chars < free_limit:
            print(f"   ✅ WELL WITHIN FREE TIER")
            print(f"   You can translate {recipes_remaining}+ more recipes for FREE")
        else:
            print(f"   ⚠️ EXCEEDS FREE TIER")
            print(f"   Estimated monthly cost: ${pro_cost:.2f} USD")

asyncio.run(estimate_characters())
