from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.api import deps
from app.models.user_pantry_log import User, PantryItem
from app.models.ingredient import Ingredient, IngredientTranslation
from app.schemas.pantry import PantryItemCreate, PantryItemUpdate, PantryItemRead

router = APIRouter()

@router.get("/", response_model=List[PantryItemRead])
async def get_pantry_items(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    
    # Fetch Pantry Items with Ingredients and Translations
    stmt = select(PantryItem).where(PantryItem.user_id == current_user.id).options(
        selectinload(PantryItem.ingredient).selectinload(Ingredient.translations)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    response = []
    for item in items:
        # Resolve Name
        ing = item.ingredient
        # Find ES translation
        trans = next((t for t in ing.translations if t.lang == "es"), None)
        name = trans.name if trans else (ing.display_name or ing.canonical_name)
        
        response.append(PantryItemRead(
            id=item.id,
            ingredient_id=item.ingredient_id,
            ingredient_name=name,
            quantity=item.quantity,
            unit=item.unit,
            expires_at=item.expires_at,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
        
    return response

@router.post("/", response_model=PantryItemRead, status_code=status.HTTP_201_CREATED)
async def create_pantry_item(
    item_in: PantryItemCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    
    # 1. Validate Ingredient Exists
    ing = await db.get(Ingredient, item_in.ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
        
    # 2. Check Duplicates for User
    stmt = select(PantryItem).where(
        PantryItem.user_id == current_user.id,
        PantryItem.ingredient_id == item_in.ingredient_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Item already in pantry. Use PATCH to update.")
        
    # 3. Create
    new_item = PantryItem(
        user_id=current_user.id,
        ingredient_id=item_in.ingredient_id,
        quantity=item_in.quantity,
        unit=item_in.unit,
        expires_at=item_in.expires_at
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    
    # Reload for naming logic (could be optimized)
    stmt_refetch = select(PantryItem).where(PantryItem.id == new_item.id).options(
         selectinload(PantryItem.ingredient).selectinload(Ingredient.translations)
    )
    res_refetch = await db.execute(stmt_refetch)
    final_item = res_refetch.scalar_one()
    
    # Resolve Name
    ing = final_item.ingredient
    trans = next((t for t in ing.translations if t.lang == "es"), None)
    name = trans.name if trans else (ing.display_name or ing.canonical_name)
    
    return PantryItemRead(
        id=final_item.id,
        ingredient_id=final_item.ingredient_id,
        ingredient_name=name,
        quantity=final_item.quantity,
        unit=final_item.unit,
        expires_at=final_item.expires_at,
        created_at=final_item.created_at,
        updated_at=final_item.updated_at
    )

@router.get("/{item_id}", response_model=PantryItemRead)
async def get_pantry_item(
    item_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    stmt = select(PantryItem).where(
        PantryItem.id == item_id,
        PantryItem.user_id == current_user.id
    ).options(
         selectinload(PantryItem.ingredient).selectinload(Ingredient.translations)
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Pantry item not found")
        
    # Resolve Name
    ing = item.ingredient
    trans = next((t for t in ing.translations if t.lang == "es"), None)
    name = trans.name if trans else (ing.display_name or ing.canonical_name)
    
    return PantryItemRead(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=name,
        quantity=item.quantity,
        unit=item.unit,
        expires_at=item.expires_at,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@router.patch("/{item_id}", response_model=PantryItemRead)
async def update_pantry_item(
    item_id: int,
    item_update: PantryItemUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    stmt = select(PantryItem).where(
        PantryItem.id == item_id,
        PantryItem.user_id == current_user.id
    ).options(
         selectinload(PantryItem.ingredient).selectinload(Ingredient.translations)
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Pantry item not found")
        
    if item_update.quantity is not None:
        item.quantity = item_update.quantity
    if item_update.unit is not None:
        item.unit = item_update.unit
    if item_update.expires_at is not None:
        item.expires_at = item_update.expires_at
        
    await db.commit()
    await db.refresh(item)
    
    # Resolve Name
    ing = item.ingredient
    trans = next((t for t in ing.translations if t.lang == "es"), None)
    name = trans.name if trans else (ing.display_name or ing.canonical_name)
    
    return PantryItemRead(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name=name,
        quantity=item.quantity,
        unit=item.unit,
        expires_at=item.expires_at,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pantry_item(
    item_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    stmt = select(PantryItem).where(
        PantryItem.id == item_id,
        PantryItem.user_id == current_user.id
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Pantry item not found")
        
    await db.delete(item)
    await db.commit()
