from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.api import deps
from app.models.user_pantry_log import User, ShoppingListItem
from app.models.ingredient import Ingredient, IngredientTranslation
from app.schemas.shopping import (
    ShoppingListItemCreate,
    ShoppingListItemUpdate,
    ShoppingListItemRead,
)

router = APIRouter()


def _resolve_ingredient_name_es(ingredient: Ingredient) -> str:
    """Resolve Spanish name for an ingredient, falling back to display_name or canonical_name."""
    trans = next((t for t in ingredient.translations if t.lang == "es"), None)
    return trans.name if trans else (ingredient.display_name or ingredient.canonical_name)


@router.get("/", response_model=List[ShoppingListItemRead])
async def get_shopping_list(
    only_pending: bool = Query(False, description="If true, only return items where is_done is False"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Retrieve the shopping list for the current user.
    Optionally filter to only pending (not yet purchased) items.
    """
    stmt = (
        select(ShoppingListItem)
        .where(ShoppingListItem.user_id == current_user.id)
        .options(selectinload(ShoppingListItem.ingredient).selectinload(Ingredient.translations))
    )

    if only_pending:
        stmt = stmt.where(ShoppingListItem.is_checked == False)

    result = await db.execute(stmt)
    items = result.scalars().all()

    response = []
    for item in items:
        ing = item.ingredient
        name_es = _resolve_ingredient_name_es(ing)

        response.append(
            ShoppingListItemRead(
                id=item.id,
                ingredient_id=item.ingredient_id,
                ingredient_name_es=name_es,
                quantity=item.quantity,
                unit=item.unit,
                is_done=item.is_checked,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    return response


@router.post("/", response_model=ShoppingListItemRead, status_code=status.HTTP_201_CREATED)
async def create_shopping_list_item(
    item_in: ShoppingListItemCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Add a new item to the shopping list.
    Does not enforce uniqueness – multiple items for the same ingredient are allowed.
    """
    # 1. Validate Ingredient Exists
    ing = await db.get(Ingredient, item_in.ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    # 2. Create new ShoppingListItem
    new_item = ShoppingListItem(
        user_id=current_user.id,
        ingredient_id=item_in.ingredient_id,
        quantity=item_in.quantity,
        unit=item_in.unit or "",
        is_checked=False,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    # 3. Reload with ingredient translations for response
    stmt_refetch = (
        select(ShoppingListItem)
        .where(ShoppingListItem.id == new_item.id)
        .options(selectinload(ShoppingListItem.ingredient).selectinload(Ingredient.translations))
    )
    res_refetch = await db.execute(stmt_refetch)
    final_item = res_refetch.scalar_one()

    ing = final_item.ingredient
    name_es = _resolve_ingredient_name_es(ing)

    return ShoppingListItemRead(
        id=final_item.id,
        ingredient_id=final_item.ingredient_id,
        ingredient_name_es=name_es,
        quantity=final_item.quantity,
        unit=final_item.unit,
        is_done=final_item.is_checked,
        created_at=final_item.created_at,
        updated_at=final_item.updated_at,
    )


@router.patch("/{item_id}", response_model=ShoppingListItemRead)
async def update_shopping_list_item(
    item_id: int,
    item_update: ShoppingListItemUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update an existing shopping list item (quantity, unit, or is_done status).
    Cannot change ingredient_id.
    """
    stmt = (
        select(ShoppingListItem)
        .where(ShoppingListItem.id == item_id, ShoppingListItem.user_id == current_user.id)
        .options(selectinload(ShoppingListItem.ingredient).selectinload(Ingredient.translations))
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Shopping list item not found")

    if item_update.quantity is not None:
        item.quantity = item_update.quantity
    if item_update.unit is not None:
        item.unit = item_update.unit
    if item_update.is_done is not None:
        item.is_checked = item_update.is_done

    await db.commit()
    await db.refresh(item)

    ing = item.ingredient
    name_es = _resolve_ingredient_name_es(ing)

    return ShoppingListItemRead(
        id=item.id,
        ingredient_id=item.ingredient_id,
        ingredient_name_es=name_es,
        quantity=item.quantity,
        unit=item.unit,
        is_done=item.is_checked,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list_item(
    item_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete an item from the shopping list.
    """
    stmt = select(ShoppingListItem).where(
        ShoppingListItem.id == item_id, ShoppingListItem.user_id == current_user.id
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Shopping list item not found")

    await db.delete(item)
    await db.commit()
