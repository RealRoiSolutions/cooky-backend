import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.ingredient import Ingredient

async def check_nutrition():
    print("Generating report...")
    async with AsyncSessionLocal() as session:
        stmt = select(Ingredient).limit(20)
        result = await session.execute(stmt)
        ingredients = result.scalars().all()
        
        with open("nutrition_report.txt", "w", encoding="utf-8") as f:
            f.write("Checking Ingredient table for nutrition_per_100g data...\n")
            f.write("-" * 120 + "\n")
            
            if not ingredients:
                f.write("No ingredients found.\n")
                return

            f.write(f"{'ID':<5} {'Name':<35} {'Has Nutrition?'}\n")
            f.write("-" * 120 + "\n")
            for ing in ingredients:
                has_nutrition = "✅ YES" if ing.nutrition_per_100g else "❌ NO"
                f.write(f"{ing.id:<5} {ing.canonical_name[:35]:<35} {has_nutrition}\n")
                if ing.nutrition_per_100g:
                     f.write(f"      -> {ing.nutrition_per_100g}\n")
    
    print("Report generated in nutrition_report.txt")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_nutrition())
