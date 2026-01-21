from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import List, Optional
from app.schemas.ingredient import IngredientInRecipe

class RecipeBase(BaseModel):
    title: str
    image_url: str | None = None
    servings: int | None = 1
    
class RecipeList(RecipeBase):
    id: int
    nutrition_totals_per_serving: dict | None = None
    # User compatibility fields
    is_compatible_with_user: bool | None = None
    intolerance_warnings: List[str] = []
    diets: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)

class RecipeDetail(RecipeList):
    ingredients: List[IngredientInRecipe] = []
    instructions: str | None = None
    summary: str | None = None

class RecipeImportResponse(BaseModel):
    recipe_id: int
    title: str
    ingredients_count: int
    status: str

