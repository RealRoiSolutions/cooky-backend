from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class ShoppingListItemBase(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None


class ShoppingListItemCreate(ShoppingListItemBase):
    ingredient_id: int
    quantity: float = Field(default=1.0)


class ShoppingListItemUpdate(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None
    is_done: Optional[bool] = None  # Maps to is_checked in the DB model


class ShoppingListItemRead(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name_es: str  # Translated name (ES) or display_name fallback
    quantity: Optional[float] = None
    unit: Optional[str] = None
    is_done: bool  # Maps to is_checked in the DB model
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
