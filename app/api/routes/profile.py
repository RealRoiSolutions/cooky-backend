from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.api import deps
from app.models.user_pantry_log import User
from app.schemas.user import UserProfileRead, UserProfileUpdate

router = APIRouter()

# Valid diet types (soft validation)
VALID_DIET_TYPES = {"omnivore", "vegetarian", "vegan", "pescatarian", "keto", "paleo"}

# Common intolerances (soft validation)  
VALID_INTOLERANCES = {"gluten", "dairy", "egg", "nut", "soy", "shellfish", "fish", "wheat", "sesame"}


@router.get("/", response_model=UserProfileRead)
async def get_profile(
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Get the current user's profile including diet preferences and intolerances."""
    return UserProfileRead(
        diet_type=current_user.diet_type,
        intolerances=current_user.intolerances or [],
        name=current_user.name,
        email=current_user.email
    )


@router.patch("/", response_model=UserProfileRead)
async def update_profile(
    profile_update: UserProfileUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Update the current user's profile (diet_type, intolerances, name)."""
    
    # Update diet_type if provided
    if profile_update.diet_type is not None:
        if profile_update.diet_type != "" and profile_update.diet_type.lower() not in VALID_DIET_TYPES:
            # Soft warning but still allow
            pass
        current_user.diet_type = profile_update.diet_type if profile_update.diet_type else None
    
    # Update intolerances if provided
    if profile_update.intolerances is not None:
        # Normalize to lowercase
        normalized = [i.lower() for i in profile_update.intolerances]
        current_user.intolerances = normalized
    
    # Update name if provided
    if profile_update.name is not None:
        current_user.name = profile_update.name
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserProfileRead(
        diet_type=current_user.diet_type,
        intolerances=current_user.intolerances or [],
        name=current_user.name,
        email=current_user.email
    )
