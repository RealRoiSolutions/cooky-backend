from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, UniqueConstraint, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    diet_type = Column(String, nullable=True)
    intolerances = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class PantryItem(Base):
    __tablename__ = "pantry_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), index=True, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    ingredient = relationship("Ingredient")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('user_id', 'ingredient_id', 'unit', name='uq_pantry_user_ingredient_unit'),
    )

class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), index=True, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    linked_recipe_id = Column(Integer, ForeignKey("external_recipes.id"), nullable=True)
    is_checked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    ingredient = relationship("Ingredient")
    user = relationship("User")

class UserFoodLog(Base):
    __tablename__ = "user_food_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    type = Column(String, nullable=False) # "recipe" or "ingredient"
    recipe_id = Column(Integer, ForeignKey("external_recipes.id"), nullable=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    nutrition_snapshot = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    ingredient = relationship("Ingredient")
    recipe = relationship("ExternalRecipe")
    user = relationship("User")
