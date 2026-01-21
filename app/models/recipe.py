from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class ExternalRecipe(Base):
    __tablename__ = "external_recipes"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False) # e.g. spoonacular
    external_id = Column(String, index=True, nullable=False)
    title_original = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    servings = Column(Integer, default=1)
    diets = Column(JSONB, nullable=True)
    intolerances_warn = Column(JSONB, nullable=True)
    nutrition_totals_per_serving = Column(JSONB, nullable=True)
    instructions_raw = Column(Text, nullable=True)
    instructions_steps_original = Column(JSONB, nullable=True)
    raw_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    translations = relationship("RecipeTranslation", back_populates="recipe")
    ingredients = relationship("RecipeIngredient", back_populates="recipe")

    __table_args__ = (
        UniqueConstraint('source', 'external_id', name='uq_source_external_id'),
    )

class RecipeTranslation(Base):
    __tablename__ = "recipe_translations"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("external_recipes.id"), index=True, nullable=False)
    lang = Column(String, nullable=False)
    title = Column(String, nullable=False)
    instructions = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    recipe = relationship("ExternalRecipe", back_populates="translations")

    __table_args__ = (
        UniqueConstraint('recipe_id', 'lang', name='uq_recipe_lang'),
    )

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("external_recipes.id"), index=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), index=True, nullable=False)
    amount = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    position = Column(Integer, nullable=True)
    nutrition_for_amount = Column(JSONB, nullable=True)
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    recipe = relationship("ExternalRecipe", back_populates="ingredients")
    ingredient = relationship("app.models.ingredient.Ingredient")
