from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api import deps
from app.models.recipe import ExternalRecipe, RecipeTranslation, RecipeIngredient
from app.models.ingredient import Ingredient, IngredientTranslation
from app.models.user_pantry_log import User, PantryItem, ShoppingListItem
from app.schemas.recipe import RecipeList, RecipeDetail
from app.schemas.ingredient import IngredientInRecipe
from pydantic import BaseModel
from typing import Any, List, Optional

router = APIRouter()


class AddMissingRequest(BaseModel):
    include_partially_available: bool = True


class AddIngredientRequest(BaseModel):
    ingredient_id: int


class AddedItemResponse(BaseModel):
    ingredient_id: int
    ingredient_name: str
    quantity: float
    unit: str | None


async def get_pantry_for_ingredients(
    db: AsyncSession, 
    user_id: int, 
    ingredient_ids: List[int]
) -> dict:
    """
    Get pantry quantities for given ingredient IDs, grouped by ingredient_id and unit.
    Returns: {ingredient_id: {unit: total_quantity}}
    """
    stmt = select(PantryItem).where(
        PantryItem.user_id == user_id,
        PantryItem.ingredient_id.in_(ingredient_ids)
    )
    result = await db.execute(stmt)
    pantry_items = result.scalars().all()
    
    # Group by ingredient_id and unit
    pantry_map = {}
    for item in pantry_items:
        if item.ingredient_id not in pantry_map:
            pantry_map[item.ingredient_id] = {}
        unit = item.unit or ""
        if unit not in pantry_map[item.ingredient_id]:
            pantry_map[item.ingredient_id][unit] = 0
        pantry_map[item.ingredient_id][unit] += item.quantity
    
    return pantry_map


def calculate_availability(
    recipe_amount: float | None,
    recipe_unit: str | None,
    pantry_map: dict
) -> tuple[float, str | None, bool, float | None]:
    """
    Calculate availability for an ingredient.
    Returns: (pantry_quantity, pantry_unit, is_available, missing_quantity)
    """
    recipe_amount = recipe_amount or 0
    recipe_unit = recipe_unit or ""
    
    if not pantry_map:
        # No pantry items for this ingredient
        return 0, None, False, recipe_amount if recipe_amount > 0 else None
    
    # Check if we have matching unit
    if recipe_unit in pantry_map:
        pantry_qty = pantry_map[recipe_unit]
        is_available = pantry_qty >= recipe_amount
        missing = max(recipe_amount - pantry_qty, 0) if not is_available else 0
        return pantry_qty, recipe_unit, is_available, missing if missing > 0 else None
    
    # If unit doesn't match, consider as not available (no conversion)
    # But show what we have in the first available unit
    first_unit = list(pantry_map.keys())[0]
    first_qty = pantry_map[first_unit]
    return first_qty, first_unit, False, recipe_amount



# Diet compatibility mapping: diet_type -> acceptable recipe diet labels
DIET_COMPATIBILITY = {
    "vegan": ["vegan"],
    "vegetarian": ["vegetarian", "vegan"],
    "pescatarian": ["pescatarian", "vegetarian", "vegan"],
    "omnivore": None,  # None means all diets are ok
    "keto": ["ketogenic", "keto"],
    "paleo": ["paleo", "whole30"],
}


def check_diet_compatible(recipe_diets: list, user_diet: str) -> bool:
    """
    Check if recipe is compatible with user's diet.
    
    Logic:
    - vegan: recipe must have "vegan" label
    - vegetarian: recipe must have "vegetarian" OR "vegan" label
    - pescatarian: recipe must have "pescatarian", "vegetarian", OR "vegan" label
    - omnivore/None: all recipes are ok
    
    Recipes WITHOUT diet labels are treated as "unknown" - they pass for omnivore only.
    """
    if not user_diet or user_diet.lower() == "omnivore":
        return True  # Omnivores can eat everything
    
    acceptable_labels = DIET_COMPATIBILITY.get(user_diet.lower())
    if acceptable_labels is None:
        return True  # Unknown diet type, allow all
    
    if not recipe_diets:
        # Recipe has no diet labels - we can't confirm it's safe for restrictive diets
        return False
    
    # Check if recipe has at least one of the acceptable labels
    recipe_diets_lower = [d.lower() for d in recipe_diets]
    return any(label in recipe_diets_lower for label in acceptable_labels)


def get_intolerance_warnings(recipe_intolerances: list, user_intolerances: list) -> list:
    """Get list of user intolerances that the recipe contains."""
    if not recipe_intolerances or not user_intolerances:
        return []
    
    recipe_set = {i.lower() for i in recipe_intolerances}
    user_set = {i.lower() for i in user_intolerances}
    return list(recipe_set & user_set)


@router.get("/", response_model=dict)
async def get_recipes(
    skip: int = 0,
    limit: int = 20,
    diet_type: str = None,
    exclude_intolerances: List[str] = Query(None),
    use_user_profile: bool = False,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get recipes list with optional filtering by diet and intolerances.
    
    - diet_type: Filter by diet (vegan, vegetarian, etc.)
    - exclude_intolerances: Exclude recipes with these intolerances
    - use_user_profile: If true, use current user's diet/intolerances as defaults
    """
    # Resolve effective diet and intolerances
    effective_diet = diet_type
    effective_intolerances = exclude_intolerances or []
    
    if use_user_profile and current_user:
        if not effective_diet and current_user.diet_type:
            effective_diet = current_user.diet_type
        if not effective_intolerances and current_user.intolerances:
            effective_intolerances = current_user.intolerances
    
    # Fetch recipes with translations and ingredients
    stmt = select(ExternalRecipe).options(
        selectinload(ExternalRecipe.translations),
        selectinload(ExternalRecipe.ingredients)
    )
    
    result = await db.execute(stmt)
    all_recipes = result.scalars().all()
    
    # Filter recipes
    filtered_recipes = []
    for r in all_recipes:
        # Skip recipes without ingredients
        if not r.ingredients or len(r.ingredients) == 0:
            continue
            
        recipe_diets = r.diets or []
        recipe_intolerances = r.intolerances_warn or []
        
        # Diet filter
        if effective_diet:
            if not check_diet_compatible(recipe_diets, effective_diet):
                continue
        
        # Intolerance filter
        if effective_intolerances:
            warnings = get_intolerance_warnings(recipe_intolerances, effective_intolerances)
            if warnings:
                continue  # Skip recipes with user's intolerances
        
        filtered_recipes.append(r)
    
    # Apply pagination
    paginated = filtered_recipes[skip:skip + limit]
    
    # Build output with compatibility info
    output = []
    for r in paginated:
        trans = next((t for t in r.translations if t.lang == "es"), None)
        title = trans.title if trans else r.title_original
        
        # Calculate compatibility based on user profile
        is_compatible = None
        intolerance_warnings = []
        
        if current_user and (current_user.diet_type or current_user.intolerances):
            recipe_diets = r.diets or []
            recipe_intolerances = r.intolerances_warn or []
            
            diet_ok = check_diet_compatible(recipe_diets, current_user.diet_type) if current_user.diet_type else True
            intolerance_warnings = get_intolerance_warnings(recipe_intolerances, current_user.intolerances or [])
            
            is_compatible = diet_ok and len(intolerance_warnings) == 0
        
        output.append(RecipeList(
            id=r.id,
            title=title,
            image_url=r.image_url,
            servings=r.servings,
            nutrition_totals_per_serving=r.nutrition_totals_per_serving,
            is_compatible_with_user=is_compatible,
            intolerance_warnings=intolerance_warnings,
            diets=r.diets or []
        ))
        
    return {"recipes": output, "total_filtered": len(filtered_recipes)}



@router.get("/{recipe_id}", response_model=RecipeDetail)
async def get_recipe_detail(
    recipe_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    # Fetch recipe with ingredients and translations
    stmt = select(ExternalRecipe).where(ExternalRecipe.id == recipe_id).options(
        selectinload(ExternalRecipe.translations),
        selectinload(ExternalRecipe.ingredients).selectinload(RecipeIngredient.ingredient).selectinload(Ingredient.translations)
    )
    
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Recipe Translation
    r_trans = next((t for t in recipe.translations if t.lang == "es"), None)
    title = r_trans.title if r_trans else recipe.title_original
    instructions = r_trans.instructions if r_trans else recipe.instructions_raw
    summary = r_trans.summary if r_trans else None
    
    # Get all ingredient IDs for this recipe
    ingredient_ids = [ri.ingredient_id for ri in recipe.ingredients]
    
    # Get pantry availability for current user
    pantry_map = await get_pantry_for_ingredients(db, current_user.id, ingredient_ids)
    
    # Build ingredients list with availability
    ing_list = []
    for ri in recipe.ingredients:
        ing = ri.ingredient
        # Ing Translation
        i_trans = next((t for t in ing.translations if t.lang == "es"), None)
        name = i_trans.name if i_trans else (ing.display_name or ing.canonical_name)
        
        # Calculate availability
        ing_pantry = pantry_map.get(ing.id, {})
        pantry_qty, pantry_unit, is_available, missing = calculate_availability(
            ri.amount, ri.unit, ing_pantry
        )
        
        ing_list.append(IngredientInRecipe(
            id=ing.id,
            name=name,
            canonical_name=ing.canonical_name,
            amount=ri.amount,
            unit=ri.unit,
            nutrition=ri.nutrition_for_amount,
            pantry_quantity=pantry_qty if pantry_qty > 0 else None,
            pantry_unit=pantry_unit,
            is_available=is_available,
            missing_quantity=missing
        ))
        
    # Calculate user compatibility
    is_compatible = None
    intolerance_warnings = []
    
    if current_user and (current_user.diet_type or current_user.intolerances):
        recipe_diets = recipe.diets or []
        recipe_intolerances = recipe.intolerances_warn or []
        
        diet_ok = check_diet_compatible(recipe_diets, current_user.diet_type) if current_user.diet_type else True
        intolerance_warnings = get_intolerance_warnings(recipe_intolerances, current_user.intolerances or [])
        
        is_compatible = diet_ok and len(intolerance_warnings) == 0
        
    return RecipeDetail(
        id=recipe.id,
        title=title,
        image_url=recipe.image_url,
        servings=recipe.servings,
        nutrition_totals_per_serving=recipe.nutrition_totals_per_serving,
        instructions=instructions,
        summary=summary,
        ingredients=ing_list,
        is_compatible_with_user=is_compatible,
        intolerance_warnings=intolerance_warnings,
        diets=recipe.diets or []
    )


@router.post("/{recipe_id}/shopping-list/add-missing", response_model=List[AddedItemResponse])
async def add_missing_ingredients_to_shopping_list(
    recipe_id: int,
    body: AddMissingRequest = AddMissingRequest(),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Add all missing ingredients from a recipe to the shopping list.
    """
    # Fetch recipe with ingredients
    stmt = select(ExternalRecipe).where(ExternalRecipe.id == recipe_id).options(
        selectinload(ExternalRecipe.ingredients).selectinload(RecipeIngredient.ingredient).selectinload(Ingredient.translations)
    )
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Get ingredient IDs
    ingredient_ids = [ri.ingredient_id for ri in recipe.ingredients]
    
    # Get pantry availability
    pantry_map = await get_pantry_for_ingredients(db, current_user.id, ingredient_ids)
    
    added_items = []
    
    for ri in recipe.ingredients:
        ing = ri.ingredient
        ing_pantry = pantry_map.get(ing.id, {})
        pantry_qty, pantry_unit, is_available, missing = calculate_availability(
            ri.amount, ri.unit, ing_pantry
        )
        
        # Skip if fully available
        if is_available:
            continue
        
        # If include_partially_available is False, skip if there's some in pantry
        if not body.include_partially_available and pantry_qty and pantry_qty > 0:
            continue
        
        # Determine quantity to add
        quantity_to_add = missing if missing else (ri.amount or 1.0)
        
        # Get ingredient name
        i_trans = next((t for t in ing.translations if t.lang == "es"), None)
        name = i_trans.name if i_trans else (ing.display_name or ing.canonical_name)
        
        # Create shopping list item
        new_item = ShoppingListItem(
            user_id=current_user.id,
            ingredient_id=ing.id,
            quantity=quantity_to_add,
            unit=ri.unit or "",
            is_checked=False
        )
        db.add(new_item)
        
        added_items.append(AddedItemResponse(
            ingredient_id=ing.id,
            ingredient_name=name,
            quantity=quantity_to_add,
            unit=ri.unit
        ))
    
    await db.commit()
    
    return added_items


@router.post("/{recipe_id}/shopping-list/add-ingredient", response_model=AddedItemResponse)
async def add_single_ingredient_to_shopping_list(
    recipe_id: int,
    body: AddIngredientRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Add a single ingredient from a recipe to the shopping list.
    """
    # Fetch recipe with ingredients
    stmt = select(ExternalRecipe).where(ExternalRecipe.id == recipe_id).options(
        selectinload(ExternalRecipe.ingredients).selectinload(RecipeIngredient.ingredient).selectinload(Ingredient.translations)
    )
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Find the specific ingredient in recipe
    recipe_ingredient = next(
        (ri for ri in recipe.ingredients if ri.ingredient_id == body.ingredient_id), 
        None
    )
    
    if not recipe_ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found in this recipe")
    
    ing = recipe_ingredient.ingredient
    
    # Get pantry availability
    pantry_map = await get_pantry_for_ingredients(db, current_user.id, [ing.id])
    ing_pantry = pantry_map.get(ing.id, {})
    pantry_qty, pantry_unit, is_available, missing = calculate_availability(
        recipe_ingredient.amount, recipe_ingredient.unit, ing_pantry
    )
    
    # Determine quantity to add
    quantity_to_add = missing if missing else (recipe_ingredient.amount or 1.0)
    
    # Get ingredient name
    i_trans = next((t for t in ing.translations if t.lang == "es"), None)
    name = i_trans.name if i_trans else (ing.display_name or ing.canonical_name)
    
    # Create shopping list item
    new_item = ShoppingListItem(
        user_id=current_user.id,
        ingredient_id=ing.id,
        quantity=quantity_to_add,
        unit=recipe_ingredient.unit or "",
        is_checked=False
    )
    db.add(new_item)
    await db.commit()
    
    return AddedItemResponse(
        ingredient_id=ing.id,
        ingredient_name=name,
        quantity=quantity_to_add,
        unit=recipe_ingredient.unit
    )


# --- Expiring Ingredients Recommendations ---

from datetime import datetime, timedelta

class ExpiringIngredientInfo(BaseModel):
    ingredient_id: int
    ingredient_name_es: str
    expires_at: str
    days_until_expiry: int


class RecipeExpiringRecommendation(BaseModel):
    id: int
    title: str
    image_url: str | None = None
    servings: int | None = None
    nutrition_totals_per_serving: dict | None = None
    expiring_ingredients_count: int
    total_ingredients_count: int
    coverage_ratio: float
    expiring_ingredients: List[ExpiringIngredientInfo]


@router.get("/recommendations/expiring", response_model=List[RecipeExpiringRecommendation])
async def get_expiring_recommendations(
    days: int = 3,
    limit: int = 20,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get recipe recommendations based on pantry items that are expiring soon.
    Helps reduce food waste by suggesting recipes that use expiring ingredients.
    """
    # 1. Get current date range
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today + timedelta(days=days)
    
    # 2. Find expiring pantry items for this user
    stmt = select(PantryItem).where(
        PantryItem.user_id == current_user.id,
        PantryItem.expires_at.isnot(None),
        PantryItem.expires_at >= today,
        PantryItem.expires_at <= end_date
    ).options(
        selectinload(PantryItem.ingredient).selectinload(Ingredient.translations)
    )
    result = await db.execute(stmt)
    expiring_items = result.scalars().all()
    
    if not expiring_items:
        return []
    
    # Build map of expiring ingredients with their info
    expiring_map = {}  # ingredient_id -> {name_es, expires_at, days_until}
    expiring_ids = set()
    
    for item in expiring_items:
        ing = item.ingredient
        i_trans = next((t for t in ing.translations if t.lang == "es"), None)
        name = i_trans.name if i_trans else (ing.display_name or ing.canonical_name)
        
        exp_date = item.expires_at
        if hasattr(exp_date, 'date'):
            exp_date = exp_date.date() if hasattr(exp_date, 'date') else exp_date
        days_until = (item.expires_at.replace(tzinfo=None) - today).days
        
        # Keep the one with earliest expiry if multiple
        if ing.id not in expiring_map or days_until < expiring_map[ing.id]['days_until']:
            expiring_map[ing.id] = {
                'name_es': name,
                'expires_at': item.expires_at.strftime('%Y-%m-%d'),
                'days_until': days_until
            }
        expiring_ids.add(ing.id)
    
    # 3. Find recipes that use these ingredients
    stmt = select(RecipeIngredient).where(
        RecipeIngredient.ingredient_id.in_(expiring_ids)
    )
    result = await db.execute(stmt)
    recipe_ingredients = result.scalars().all()
    
    if not recipe_ingredients:
        return []
    
    # Get unique recipe IDs
    recipe_ids = set(ri.recipe_id for ri in recipe_ingredients)
    
    # Map recipe_id -> list of expiring ingredient_ids used
    recipe_expiring_map = {}
    for ri in recipe_ingredients:
        if ri.recipe_id not in recipe_expiring_map:
            recipe_expiring_map[ri.recipe_id] = []
        recipe_expiring_map[ri.recipe_id].append(ri.ingredient_id)
    
    # 4. Fetch full recipe data
    stmt = select(ExternalRecipe).where(
        ExternalRecipe.id.in_(recipe_ids)
    ).options(
        selectinload(ExternalRecipe.translations),
        selectinload(ExternalRecipe.ingredients)
    )
    result = await db.execute(stmt)
    recipes = result.scalars().all()
    
    # 5. Calculate metrics and build response
    recommendations = []
    
    for recipe in recipes:
        # Get translation
        r_trans = next((t for t in recipe.translations if t.lang == "es"), None)
        title = r_trans.title if r_trans else recipe.title_original
        
        # Calculate counts
        total_ingredients = len(recipe.ingredients)
        expiring_ing_ids = recipe_expiring_map.get(recipe.id, [])
        expiring_count = len(expiring_ing_ids)
        coverage = expiring_count / total_ingredients if total_ingredients > 0 else 0
        
        # Build expiring ingredients info list
        exp_ingredients_info = []
        for ing_id in expiring_ing_ids:
            if ing_id in expiring_map:
                info = expiring_map[ing_id]
                exp_ingredients_info.append(ExpiringIngredientInfo(
                    ingredient_id=ing_id,
                    ingredient_name_es=info['name_es'],
                    expires_at=info['expires_at'],
                    days_until_expiry=info['days_until']
                ))
        
        # Sort expiring ingredients by days until expiry
        exp_ingredients_info.sort(key=lambda x: x.days_until_expiry)
        
        recommendations.append({
            'recipe': recipe,
            'title': title,
            'expiring_count': expiring_count,
            'total_count': total_ingredients,
            'coverage': coverage,
            'exp_ingredients': exp_ingredients_info,
            'min_days': min(e.days_until_expiry for e in exp_ingredients_info) if exp_ingredients_info else 999
        })
    
    # 6. Sort: by expiring_count desc, then coverage desc, then min_days asc
    recommendations.sort(key=lambda x: (-x['expiring_count'], -x['coverage'], x['min_days']))
    
    # 7. Build final response
    output = []
    for rec in recommendations[:limit]:
        r = rec['recipe']
        output.append(RecipeExpiringRecommendation(
            id=r.id,
            title=rec['title'],
            image_url=r.image_url,
            servings=r.servings,
            nutrition_totals_per_serving=r.nutrition_totals_per_serving,
            expiring_ingredients_count=rec['expiring_count'],
            total_ingredients_count=rec['total_count'],
            coverage_ratio=round(rec['coverage'], 2),
            expiring_ingredients=rec['exp_ingredients']
        ))
    
    return output

