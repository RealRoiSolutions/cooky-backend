from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List

from app.api import deps
from app.models.ingredient import Ingredient, IngredientTranslation
from app.schemas.ingredient import IngredientSearchResult

router = APIRouter()

@router.get("/search", response_model=List[IngredientSearchResult])
async def search_ingredients(
    q: str = Query(..., min_length=2),
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(deps.get_db)
):
    if limit > 50:
        limit = 50
        
    # Search logic: Left Join Ingredient -> IngredientTranslation (lang='es')
    # Filter: matches translation OR matches display_name
    stmt = select(Ingredient, IngredientTranslation).\
        outerjoin(IngredientTranslation, and_(
            Ingredient.id == IngredientTranslation.ingredient_id, 
            IngredientTranslation.lang == "es"
        )).\
        where(
            or_(
                IngredientTranslation.name.ilike(f"%{q}%"),
                Ingredient.display_name.ilike(f"%{q}%")
            )
        ).\
        limit(limit).offset(offset)
        
    result = await db.execute(stmt)
    rows = result.all()
    
    results = []
    for ing, trans in rows:
        # Determine name_es: preference to translation, then display_name, then canonical_name (safety)
        if trans and trans.name:
            name_es = trans.name
            verified = trans.is_verified
        else:
            name_es = ing.display_name or ing.canonical_name
            verified = None
            
        results.append(IngredientSearchResult(
            ingredient_id=ing.id,
            name_es=name_es,
            category=ing.category,
            is_translation_verified=verified
        ))
        
    return results
