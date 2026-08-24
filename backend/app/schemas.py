from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .models import RecipeStatus


class RecipeBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    source_url: str | None = None
    ingredients: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    prep_time: str | None = None
    cook_time: str | None = None
    total_time: str | None = None
    yield_text: str | None = None


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(RecipeBase):
    pass


class MediaCreate(BaseModel):
    url: str
    media_type: str = Field(default="photo", pattern="^(photo|video)$")
    caption: str | None = None


class MediaRead(MediaCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class InstanceCreate(BaseModel):
    name: str = Field(default="Attempt", min_length=1, max_length=255)
    attempted_on: date = Field(default_factory=date.today)
    ingredients: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    techniques: str | None = None
    timing_notes: str | None = None
    notes: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    media: list[MediaCreate] = Field(default_factory=list)


class IngredientEntryCreate(BaseModel):
    product_id: int | None = None
    line: str = Field(min_length=1)
    amount: float | None = None
    unit: str | None = None
    notes: str | None = None
    position: int = 0


class IngredientEntryRead(IngredientEntryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class StepCreate(BaseModel):
    position: int = Field(ge=0)
    action_type: str = "custom"
    instruction: str = Field(min_length=1)
    duration: float | None = None
    duration_unit: str | None = None
    temperature: float | None = None
    temperature_unit: str | None = None
    equipment_setting: str | None = None
    notes: str | None = None


class StepRead(StepCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class IngredientTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class IngredientTypeRead(IngredientTypeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProductCreate(BaseModel):
    ingredient_type_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    brand: str | None = None
    upc: str | None = None
    notes: str | None = None


class ProductRead(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class InstanceRead(InstanceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class RecipeSummary(BaseModel):
    id: int
    name: str
    status: RecipeStatus
    source_url: str | None
    created_at: datetime
    finalized_at: datetime | None
    attempts_count: int
    most_recent_attempt: date | None
    thumbnail_url: str | None


class RecipeRead(RecipeBase):
    id: int
    status: RecipeStatus
    created_at: datetime
    updated_at: datetime
    finalized_at: datetime | None
    finalized_instance_id: int | None
    parent_recipe_id: int | None
    instances: list[InstanceRead] = Field(default_factory=list)
    media: list[MediaRead] = Field(default_factory=list)


class ImportRequest(BaseModel):
    url: HttpUrl


class ImportPreview(RecipeBase):
    parse_succeeded: bool


class FinalizeRequest(BaseModel):
    instance_id: int
