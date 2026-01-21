from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# Valid diet types for reference (not strictly enforced)
# omnivore, vegetarian, vegan, pescatarian, keto, paleo, etc.

# Common intolerances for reference
# gluten, dairy, egg, nut, soy, shellfish, fish, wheat, sesame

class UserProfileRead(BaseModel):
    diet_type: Optional[str] = None
    intolerances: List[str] = []
    name: Optional[str] = None
    email: str
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    diet_type: Optional[str] = None
    intolerances: Optional[List[str]] = None
    name: Optional[str] = None
