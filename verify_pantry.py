import asyncio
import httpx
import sys
import json

async def verify_pantry():
    base_url = "http://127.0.0.1:8000"
    print("Verifying Pantry Endpoints...")
    print("-" * 60)
    
    async with httpx.AsyncClient() as client:
        # 1. Create (POST)
        # Using ID 16 (Garlic) from previous report
        print("\n1. Adding Garlic to Pantry...")
        payload = {
            "ingredient_id": 16, 
            "quantity": 5.0, 
            "unit": "cloves"
        }
        r = await client.post(f"{base_url}/pantry/", json=payload)
        
        if r.status_code == 201:
            try:
                item = r.json()
            except json.JSONDecodeError:
                print(f"❌ JSON Decode Error. Status: {r.status_code}, Body: {r.text}")
                return
            print(f"✅ Created Item ID: {item['id']}")
            print(f"   Name: {item['ingredient_name']}")
            print(f"   Qty: {item['quantity']} {item['unit']}")
            item_id = item['id']
        elif r.status_code == 400:
             print("⚠️ Item already exists (expected if re-running)")
             # Try to get list to find ID
             r_list = await client.get(f"{base_url}/pantry/")
             items = r_list.json()
             target = next((i for i in items if i["ingredient_id"] == 16), None)
             if target:
                 item_id = target["id"]
                 print(f"   Found existing ID: {item_id}")
             else:
                 print("❌ Failed to find item")
                 return
        else:
            print(f"❌ Failed: {r.status_code} - {r.text}")
            return

        # 2. List (GET)
        print("\n2. Listing Pantry...")
        r = await client.get(f"{base_url}/pantry/")
        print(f"✅ Items: {len(r.json())}")
        print(json.dumps(r.json(), indent=2))
        
        # 3. Update (PATCH)
        print(f"\n3. Updating Item {item_id} (Quantity -> 10)...")
        r = await client.patch(f"{base_url}/pantry/{item_id}", json={"quantity": 10.0})
        if r.status_code == 200:
            print(f"✅ Updated: {r.json()['quantity']} {r.json()['unit']}")
        else:
             print(f"❌ Failed: {r.status_code}")

        # 4. Details (GET)
        print(f"\n4. Get Detail {item_id}...")
        r = await client.get(f"{base_url}/pantry/{item_id}")
        if r.status_code == 200:
             print(f"✅ Verified: {r.json()['quantity']}")

        # 5. Delete (DELETE)
        # 5. Delete (DELETE)
        print(f"\n5. Deleting Item {item_id}...")
        r = await client.delete(f"{base_url}/pantry/{item_id}")
        if r.status_code == 204:
             print("✅ Deleted")
        else:
             print(f"❌ Failed: {r.status_code}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_pantry())
