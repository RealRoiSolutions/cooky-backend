from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    canonical_name = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    default_unit = Column(String, nullable=True)
    nutrition_per_100g = Column(JSONB, nullable=True)
    source_ids = Column(JSONB, nullable=True)
    source_priority = Column(Integer, default=2)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    translations = relationship("IngredientTranslation", back_populates="ingredient")
    
    # Indexes for JSONB fields can be added via Alembic or generic Index here if needed, 
    # but specific JSONB path indexes often need raw SQL or specific constructs. 
    # For now, we rely on standard indexes.

class IngredientTranslation(Base):
    __tablename__ = "ingredient_translations"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, index=True, nullable=False) # FK added in foreign_keys step or via logic
    # Adding ForeignKey explicitly if we want strict integrity, user asked for FK -> Ingredient.id
    from sqlalchemy import ForeignKey
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), index=True, nullable=False)
    
    lang = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    ingredient = relationship("Ingredient", back_populates="translations")

    __table_args__ = (
        UniqueConstraint('ingredient_id', 'lang', name='uq_ingredient_lang'),
    )
