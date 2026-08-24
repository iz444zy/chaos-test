from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class RecipeStatus(str, Enum):
    DEVELOPING = "DEVELOPING"
    FINALIZED = "FINALIZED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    supabase_user_id: Mapped[str | None] = mapped_column(String(36), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    recipes: Mapped[list["RecipeProfile"]] = relationship(back_populates="user")


class IngredientType(Base):
    __tablename__ = "ingredient_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    products: Mapped[list["IngredientProduct"]] = relationship(back_populates="ingredient_type")


class IngredientProduct(Base):
    __tablename__ = "ingredient_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_type_id: Mapped[int | None] = mapped_column(ForeignKey("ingredient_types.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    upc: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingredient_type: Mapped[IngredientType | None] = relationship(back_populates="products")


class RecipeProfile(Base):
    __tablename__ = "recipe_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    ingredients: Mapped[str] = mapped_column(Text, default="[]")
    instructions: Mapped[str] = mapped_column(Text, default="[]")
    prep_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cook_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    yield_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[RecipeStatus] = mapped_column(
        SqlEnum(RecipeStatus), default=RecipeStatus.DEVELOPING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finalized_instance_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_instances.id", use_alter=True), nullable=True
    )
    parent_recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_profiles.id"), nullable=True
    )
    user: Mapped[User] = relationship(back_populates="recipes")
    instances: Mapped[list["RecipeInstance"]] = relationship(
        foreign_keys="RecipeInstance.recipe_id",
        back_populates="recipe",
        cascade="all, delete-orphan",
        order_by="RecipeInstance.attempted_on",
    )
    media: Mapped[list["Media"]] = relationship(
        primaryjoin="and_(RecipeProfile.id == foreign(Media.recipe_id), Media.instance_id == None)",
        cascade="all, delete-orphan",
    )


class RecipeInstance(Base):
    __tablename__ = "recipe_instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipe_profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="Attempt")
    attempted_on: Mapped[date] = mapped_column(Date, default=date.today)
    ingredients: Mapped[str] = mapped_column(Text, default="[]")
    instructions: Mapped[str] = mapped_column(Text, default="[]")
    techniques: Mapped[str | None] = mapped_column(Text, nullable=True)
    timing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    recipe: Mapped[RecipeProfile] = relationship(
        foreign_keys=[recipe_id], back_populates="instances"
    )
    media: Mapped[list["Media"]] = relationship(
        primaryjoin="RecipeInstance.id == foreign(Media.instance_id)",
        cascade="all, delete-orphan",
    )
    ingredient_entries: Mapped[list["InstanceIngredient"]] = relationship(
        back_populates="instance", cascade="all, delete-orphan", order_by="InstanceIngredient.position"
    )
    steps: Mapped[list["RecipeStep"]] = relationship(
        back_populates="instance", cascade="all, delete-orphan", order_by="RecipeStep.position"
    )


class InstanceIngredient(Base):
    __tablename__ = "instance_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("recipe_instances.id"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("ingredient_products.id"), nullable=True)
    line: Mapped[str] = mapped_column(Text)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    instance: Mapped[RecipeInstance] = relationship(back_populates="ingredient_entries")
    product: Mapped[IngredientProduct | None] = relationship()


class RecipeStep(Base):
    __tablename__ = "recipe_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("recipe_instances.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    action_type: Mapped[str] = mapped_column(String(120), default="custom")
    instruction: Mapped[str] = mapped_column(Text)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    equipment_setting: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    instance: Mapped[RecipeInstance] = relationship(back_populates="steps")


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_profiles.id"), nullable=True, index=True
    )
    instance_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_instances.id"), nullable=True, index=True
    )
    url: Mapped[str] = mapped_column(String(2048))
    media_type: Mapped[str] = mapped_column(String(16), default="photo")
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
