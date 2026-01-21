from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class PantryItemBase(BaseModel):
    quantity: float
    unit: str
    expires_at: Optional[datetime] = None

class PantryItemCreate(PantryItemBase):
    ingredient_id: int

class PantryItemUpdate(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None
    expires_at: Optional[datetime] = None

class PantryItemRead(PantryItemBase):
    id: int
    ingredient_id: int
    ingredient_name: str # Translated name
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

