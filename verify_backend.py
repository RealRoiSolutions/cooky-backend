import asyncio
import httpx
import sys

async def verify_flow():
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Check health
        try:
            r = await client.get(f"{base_url}/")
            print(f"Root endpoint: {r.status_code}")
        except Exception as e:
            print(f"Server not up: {e}")
            return

        # 2. Import a Recipe (Pasta with Garlic, Scallions, Cauliflower & Breadcrumbs - ID: 716429)
        print("Importing recipe 716429...")
        r = await client.post(f"{base_url}/admin/spoonacular/import-recipe/716429", timeout=60.0)
        if r.status_code == 200:
            print("Import Success:", r.json())
        else:
            print("Import Failed:", r.text)

        # 3. List Recipes
        print("Listing recipes...")
        r = await client.get(f"{base_url}/recipes/")
        print("List:", r.json())
        
        # 4. Get Detail (Assuming ID 2 for the new recipe)
        print("Getting detail for new recipe...")
        # Note: In a real test we would parse the ID from the import response
        if r.status_code == 200:
             new_id = r.json().get("recipe_id")
             r = await client.get(f"{base_url}/recipes/{new_id}") 
             print("Detail:", r.json())

if __name__ == "__main__":
    asyncio.run(verify_flow())
