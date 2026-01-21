import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def ensure_user():
    async with AsyncSessionLocal() as session:
        # Check if user 1 exists
        result = await session.execute(text("SELECT id FROM users WHERE id = 1"))
        user = result.scalar_one_or_none()
        
        if not user:
            print("Creating dummy user (ID 1) for MVP...")
            await session.execute(
                text("INSERT INTO users (id, email, password_hash, name, created_at, updated_at) VALUES (1, 'test@cooky.com', 'dummy_hash', 'Test User', NOW(), NOW())")
            )
            await session.commit()
            print("User 1 created.")
        else:
            print("User 1 already exists.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(ensure_user())
