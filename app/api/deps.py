from typing import Generator, AsyncGenerator
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.user_pantry_log import User

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """
    Stub for authentication. Returns the first user in DB or creates a test User.
    """
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create Dummy User for MVP testing
        user = User(
            email="test@cooky.com",
            password_hash="hashed_secret",
            name="Test User"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user
