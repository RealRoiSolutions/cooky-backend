from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List

# --- Create Schemas ---

class RecipeLogCreate(BaseModel):
    recipe_id: int
    servings: float = 1.0
    logged_at: Optional[datetime] = None


class IngredientLogCreate(BaseModel):
    ingredient_id: int
    quantity: float
    unit: str = "g"
    logged_at: Optional[datetime] = None


# --- Response Schemas ---

class MacroTotals(BaseModel):
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0


class FoodLogEntryRead(BaseModel):
    id: int
    type: str  # "recipe" or "ingredient"
    recipe_id: Optional[int] = None
    recipe_title: Optional[str] = None
    ingredient_id: Optional[int] = None
    ingredient_name_es: Optional[str] = None
    quantity: float
    unit: str
    logged_at: datetime
    macros: MacroTotals
    
    model_config = ConfigDict(from_attributes=True)


class DailySummary(BaseModel):
    date: date
    totals: MacroTotals
    entries: List[FoodLogEntryRead]
