import asyncio
import sys
import os
import httpx

# Add project root to sys.path
sys.path.append(os.getcwd())

async def check_translations():
    base_url = "http://127.0.0.1:8000"
    print("Checking for translations in API response...")
    
    async with httpx.AsyncClient() as client:
        # Get Recipe 2 (the one we just imported/translated)
        # Note: ID might vary if the user imported multiple times, let's try 1 and 2
        for r_id in [1, 2]:
            resp = await client.get(f"{base_url}/recipes/{r_id}")
            if resp.status_code != 200:
                continue
                
            data = resp.json()
            title = data.get("title")
            ingredients = data.get("ingredients", [])
            
            print(f"\nRecipe ID {r_id}: {title}")
            print("-" * 50)
            if ingredients:
                print(f"First 3 ingredients:")
                for ing in ingredients[:3]:
                    print(f" - {ing['name']} ({ing['amount']} {ing['unit']})")
            else:
                print("No ingredients found.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_translations())
