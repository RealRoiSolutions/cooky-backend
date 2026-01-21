from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timedelta
from typing import Any, List

from app.api import deps
from app.models.user_pantry_log import User, UserFoodLog
from app.models.recipe import ExternalRecipe, RecipeTranslation
from app.models.ingredient import Ingredient, IngredientTranslation
from app.schemas.log import (
    RecipeLogCreate, IngredientLogCreate, 
    FoodLogEntryRead, DailySummary, MacroTotals
)

router = APIRouter()


def calculate_recipe_macros(nutrition: dict, servings: float) -> MacroTotals:
    """Calculate macros for a recipe based on servings."""
    if not nutrition:
        return MacroTotals()
    
    return MacroTotals(
        calories=round((nutrition.get('calories', 0) or 0) * servings, 1),
        protein=round((nutrition.get('protein', 0) or 0) * servings, 1),
        carbs=round((nutrition.get('carbohydrates', 0) or nutrition.get('carbs', 0) or 0) * servings, 1),
        fat=round((nutrition.get('fat', 0) or 0) * servings, 1)
    )


def calculate_ingredient_macros(nutrition_per_100g: dict, quantity: float, unit: str) -> MacroTotals:
    """
    Calculate macros for an ingredient based on quantity and unit.
    Simple approach: assumes unit is grams (g) or kg.
    For other units, treats quantity as grams.
    """
    if not nutrition_per_100g:
        return MacroTotals()
    
    # Convert to grams
    grams = quantity
    if unit.lower() == 'kg':
        grams = quantity * 1000
    elif unit.lower() in ['g', 'gr', 'gramos']:
        grams = quantity
    # For other units (pcs, ml, etc.), treat quantity as approximate grams
    # This is a simplification documented in the code
    
    multiplier = grams / 100.0
    
    return MacroTotals(
        calories=round((nutrition_per_100g.get('calories', 0) or nutrition_per_100g.get('kcal', 0) or 0) * multiplier, 1),
        protein=round((nutrition_per_100g.get('protein', 0) or 0) * multiplier, 1),
        carbs=round((nutrition_per_100g.get('carbohydrates', 0) or nutrition_per_100g.get('carbs', 0) or 0) * multiplier, 1),
        fat=round((nutrition_per_100g.get('fat', 0) or 0) * multiplier, 1)
    )


@router.post("/recipe", response_model=FoodLogEntryRead, status_code=status.HTTP_201_CREATED)
async def log_recipe(
    body: RecipeLogCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Log consumption of a recipe."""
    # Validate recipe exists
    stmt = select(ExternalRecipe).where(ExternalRecipe.id == body.recipe_id).options(
        selectinload(ExternalRecipe.translations)
    )
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Get title
    r_trans = next((t for t in recipe.translations if t.lang == "es"), None)
    title = r_trans.title if r_trans else recipe.title_original
    
    # Calculate macros
    macros = calculate_recipe_macros(recipe.nutrition_totals_per_serving, body.servings)
    
    # Determine log time
    logged_at = body.logged_at or datetime.now()
    log_date = logged_at.date()
    
    # Create log entry
    new_log = UserFoodLog(
        user_id=current_user.id,
        date=log_date,
        type="recipe",
        recipe_id=body.recipe_id,
        ingredient_id=None,
        quantity=body.servings,
        unit="servings",
        nutrition_snapshot=macros.model_dump(),
        created_at=logged_at
    )
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    
    return FoodLogEntryRead(
        id=new_log.id,
        type="recipe",
        recipe_id=body.recipe_id,
        recipe_title=title,
        ingredient_id=None,
        ingredient_name_es=None,
        quantity=body.servings,
        unit="servings",
        logged_at=logged_at,
        macros=macros
    )


@router.post("/ingredient", response_model=FoodLogEntryRead, status_code=status.HTTP_201_CREATED)
async def log_ingredient(
    body: IngredientLogCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Log consumption of an ingredient (standalone, not from a recipe)."""
    # Validate ingredient exists
    stmt = select(Ingredient).where(Ingredient.id == body.ingredient_id).options(
        selectinload(Ingredient.translations)
    )
    result = await db.execute(stmt)
    ingredient = result.scalar_one_or_none()
    
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    
    # Get name
    i_trans = next((t for t in ingredient.translations if t.lang == "es"), None)
    name = i_trans.name if i_trans else (ingredient.display_name or ingredient.canonical_name)
    
    # Calculate macros
    macros = calculate_ingredient_macros(ingredient.nutrition_per_100g, body.quantity, body.unit)
    
    # Determine log time
    logged_at = body.logged_at or datetime.now()
    log_date = logged_at.date()
    
    # Create log entry
    new_log = UserFoodLog(
        user_id=current_user.id,
        date=log_date,
        type="ingredient",
        recipe_id=None,
        ingredient_id=body.ingredient_id,
        quantity=body.quantity,
        unit=body.unit,
        nutrition_snapshot=macros.model_dump(),
        created_at=logged_at
    )
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    
    return FoodLogEntryRead(
        id=new_log.id,
        type="ingredient",
        recipe_id=None,
        recipe_title=None,
        ingredient_id=body.ingredient_id,
        ingredient_name_es=name,
        quantity=body.quantity,
        unit=body.unit,
        logged_at=logged_at,
        macros=macros
    )


@router.get("/daily-summary", response_model=DailySummary)
async def get_daily_summary(
    log_date: date = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """Get the daily summary of food logs with macro totals."""
    if log_date is None:
        log_date = date.today()
    
    # Fetch logs for the date
    stmt = select(UserFoodLog).where(
        UserFoodLog.user_id == current_user.id,
        UserFoodLog.date == log_date
    ).options(
        selectinload(UserFoodLog.recipe).selectinload(ExternalRecipe.translations),
        selectinload(UserFoodLog.ingredient).selectinload(Ingredient.translations)
    ).order_by(UserFoodLog.created_at)
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    # Build entries and calculate totals
    entries = []
    total_macros = MacroTotals()
    
    for log in logs:
        # Get macros from snapshot or recalculate
        if log.nutrition_snapshot:
            macros = MacroTotals(**log.nutrition_snapshot)
        elif log.type == "recipe" and log.recipe:
            macros = calculate_recipe_macros(
                log.recipe.nutrition_totals_per_serving, log.quantity
            )
        elif log.type == "ingredient" and log.ingredient:
            macros = calculate_ingredient_macros(
                log.ingredient.nutrition_per_100g, log.quantity, log.unit
            )
        else:
            macros = MacroTotals()
        
        # Get names
        recipe_title = None
        ingredient_name = None
        
        if log.type == "recipe" and log.recipe:
            r_trans = next((t for t in log.recipe.translations if t.lang == "es"), None)
            recipe_title = r_trans.title if r_trans else log.recipe.title_original
        
        if log.type == "ingredient" and log.ingredient:
            i_trans = next((t for t in log.ingredient.translations if t.lang == "es"), None)
            ingredient_name = i_trans.name if i_trans else (
                log.ingredient.display_name or log.ingredient.canonical_name
            )
        
        entries.append(FoodLogEntryRead(
            id=log.id,
            type=log.type,
            recipe_id=log.recipe_id,
            recipe_title=recipe_title,
            ingredient_id=log.ingredient_id,
            ingredient_name_es=ingredient_name,
            quantity=log.quantity,
            unit=log.unit,
            logged_at=log.created_at,
            macros=macros
        ))
        
        # Accumulate totals
        total_macros.calories += macros.calories
        total_macros.protein += macros.protein
        total_macros.carbs += macros.carbs
        total_macros.fat += macros.fat
    
    # Round totals
    total_macros.calories = round(total_macros.calories, 1)
    total_macros.protein = round(total_macros.protein, 1)
    total_macros.carbs = round(total_macros.carbs, 1)
    total_macros.fat = round(total_macros.fat, 1)
    
    return DailySummary(
        date=log_date,
        totals=total_macros,
        entries=entries
    )


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log_entry(
    log_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> None:
    """Delete a food log entry."""
    stmt = select(UserFoodLog).where(
        UserFoodLog.id == log_id,
        UserFoodLog.user_id == current_user.id
    )
    result = await db.execute(stmt)
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    
    await db.delete(log)
    await db.commit()
