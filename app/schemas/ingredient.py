from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class IngredientBase(BaseModel):
    canonical_name: str
    display_name: str | None = None
    category: str | None = None
    default_unit: str | None = None

class IngredientRead(IngredientBase):
    id: int
    nutrition_per_100g: dict | None = None
    
    model_config = ConfigDict(from_attributes=True)

class IngredientInRecipe(BaseModel):
    id: int
    name: str # Translated or canonical
    canonical_name: str
    amount: float | None = None
    unit: str | None = None
    nutrition: dict | None = None
    # Availability from pantry
    pantry_quantity: float | None = None
    pantry_unit: str | None = None
    is_available: bool = False
    missing_quantity: float | None = None
    
    model_config = ConfigDict(from_attributes=True)

class IngredientSearchResult(BaseModel):
    ingredient_id: int
    name_es: str
    category: str | None = None
    is_translation_verified: bool | None = None
    
    model_config = ConfigDict(from_attributes=True)

