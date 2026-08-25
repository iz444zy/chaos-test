import json
import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .auth import current_user, issue_dev_token
from .db import Base, engine, get_db, migrate_database
from .models import (
    IngredientProduct,
    IngredientType,
    InstanceIngredient,
    Media,
    RecipeInstance,
    RecipeProfile,
    RecipeStatus,
    RecipeStep,
    User,
)
from .schemas import (
    FinalizeRequest,
    ImportPreview,
    ImportRequest,
    InstanceCreate,
    InstanceRead,
    IngredientEntryCreate,
    IngredientEntryRead,
    IngredientTypeCreate,
    IngredientTypeRead,
    MediaCreate,
    MediaRead,
    ProductCreate,
    ProductRead,
    RecipeCreate,
    RecipeRead,
    RecipeSummary,
    RecipeUpdate,
    StepCreate,
    StepRead,
)
from .services import import_recipe

Base.metadata.create_all(bind=engine)
migrate_database()
cors_origins = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]

app = FastAPI(title="BatchBook")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

def recipe_for_user(recipe_id: int, user: User, db: Session) -> RecipeProfile:
    recipe = db.scalar(
        select(RecipeProfile)
        .where(RecipeProfile.id == recipe_id, RecipeProfile.user_id == user.id)
        .options(
            selectinload(RecipeProfile.instances).selectinload(RecipeInstance.media),
            selectinload(RecipeProfile.instances).selectinload(RecipeInstance.ingredient_entries),
            selectinload(RecipeProfile.instances).selectinload(RecipeInstance.steps),
            selectinload(RecipeProfile.media),
        )
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


def assert_recipe_editable(recipe: RecipeProfile) -> None:
    if recipe.status == RecipeStatus.FINALIZED:
        raise HTTPException(status_code=409, detail="Finalized recipes are preserved; create a variant instead")


def to_instance(instance: RecipeInstance) -> InstanceRead:
    return InstanceRead(
        id=instance.id,
        name=instance.name,
        attempted_on=instance.attempted_on,
        ingredients=json.loads(instance.ingredients),
        instructions=json.loads(instance.instructions),
        techniques=instance.techniques,
        timing_notes=instance.timing_notes,
        notes=instance.notes,
        rating=instance.rating,
        media=[MediaRead.model_validate(item) for item in instance.media],
        created_at=instance.created_at,
    )


def to_recipe(recipe: RecipeProfile) -> RecipeRead:
    profile_media = [
        MediaRead.model_validate(item)
        for item in recipe.media
        if item.instance_id is None
    ]
    return RecipeRead(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        source_url=recipe.source_url,
        ingredients=json.loads(recipe.ingredients),
        instructions=json.loads(recipe.instructions),
        prep_time=recipe.prep_time,
        cook_time=recipe.cook_time,
        total_time=recipe.total_time,
        yield_text=recipe.yield_text,
        status=recipe.status,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
        finalized_at=recipe.finalized_at,
        finalized_instance_id=recipe.finalized_instance_id,
        parent_recipe_id=recipe.parent_recipe_id,
        instances=[to_instance(item) for item in recipe.instances],
        media=profile_media,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/dev-login")
def dev_login():
    """Issue a server-controlled test token only when explicitly enabled locally."""
    token, user_id = issue_dev_token()
    return {"access_token": token, "token_type": "bearer", "user_id": user_id}


@app.post("/imports/preview", response_model=ImportPreview)
def preview_import(payload: ImportRequest, _: User = Depends(current_user)):
    return import_recipe(str(payload.url))


@app.get("/recipes", response_model=list[RecipeSummary])
def list_recipes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    recipes = db.scalars(
        select(RecipeProfile)
        .where(RecipeProfile.user_id == user.id)
        .options(selectinload(RecipeProfile.instances), selectinload(RecipeProfile.media))
        .order_by(RecipeProfile.updated_at.desc())
    ).all()
    return [
        RecipeSummary(
            id=recipe.id,
            name=recipe.name,
            status=recipe.status,
            source_url=recipe.source_url,
            created_at=recipe.created_at,
            finalized_at=recipe.finalized_at,
            attempts_count=len(recipe.instances),
            most_recent_attempt=max((item.attempted_on for item in recipe.instances), default=None),
            thumbnail_url=next((item.url for item in recipe.media if item.media_type == "photo"), None),
        )
        for recipe in recipes
    ]


@app.post("/recipes", response_model=RecipeRead, status_code=201)
def create_recipe(payload: RecipeCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    recipe = RecipeProfile(user_id=user.id, **payload.model_dump(exclude={"ingredients", "instructions"}))
    recipe.ingredients = json.dumps(payload.ingredients)
    recipe.instructions = json.dumps(payload.instructions)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return to_recipe(recipe)


@app.get("/recipes/{recipe_id}", response_model=RecipeRead)
def get_recipe(recipe_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return to_recipe(recipe_for_user(recipe_id, user, db))


@app.put("/recipes/{recipe_id}", response_model=RecipeRead)
def update_recipe(recipe_id: int, payload: RecipeUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    recipe = recipe_for_user(recipe_id, user, db)
    assert_recipe_editable(recipe)
    for key, value in payload.model_dump(exclude={"ingredients", "instructions"}).items():
        setattr(recipe, key, value)
    recipe.ingredients = json.dumps(payload.ingredients)
    recipe.instructions = json.dumps(payload.instructions)
    db.commit()
    db.refresh(recipe)
    return to_recipe(recipe)


@app.post("/recipes/{recipe_id}/media", response_model=MediaRead, status_code=201)
def add_recipe_media(recipe_id: int, payload: MediaCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    recipe = recipe_for_user(recipe_id, user, db)
    assert_recipe_editable(recipe)
    media = Media(recipe_id=recipe_id, **payload.model_dump())
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@app.post("/recipes/{recipe_id}/instances", response_model=InstanceRead, status_code=201)
def create_instance(recipe_id: int, payload: InstanceCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    recipe = recipe_for_user(recipe_id, user, db)
    assert_recipe_editable(recipe)
    instance = RecipeInstance(
        recipe_id=recipe_id,
        **payload.model_dump(exclude={"ingredients", "instructions", "media"}),
        ingredients=json.dumps(payload.ingredients),
        instructions=json.dumps(payload.instructions),
    )
    db.add(instance)
    db.flush()
    for media in payload.media:
        db.add(Media(instance_id=instance.id, **media.model_dump()))
    db.commit()
    db.refresh(instance)
    return to_instance(instance)


def instance_for_user(instance_id: int, user: User, db: Session) -> RecipeInstance:
    instance = db.scalar(
        select(RecipeInstance)
        .join(RecipeProfile, RecipeInstance.recipe_id == RecipeProfile.id)
        .where(RecipeInstance.id == instance_id, RecipeProfile.user_id == user.id)
        .options(selectinload(RecipeInstance.recipe), selectinload(RecipeInstance.media))
    )
    if not instance:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return instance


def assert_instance_editable(instance: RecipeInstance) -> None:
    if instance.recipe.finalized_instance_id == instance.id:
        raise HTTPException(status_code=409, detail="Finalized attempts are preserved; create a variant instead")


@app.post("/recipes/{recipe_id}/instances/clone", response_model=InstanceRead, status_code=201)
def clone_latest_instance(recipe_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    recipe = recipe_for_user(recipe_id, user, db)
    assert_recipe_editable(recipe)
    source = recipe.instances[-1] if recipe.instances else None
    clone = RecipeInstance(
        recipe_id=recipe.id,
        name=f"Attempt {len(recipe.instances) + 1}",
        ingredients=source.ingredients if source else recipe.ingredients,
        instructions=source.instructions if source else recipe.instructions,
        techniques=source.techniques if source else None,
        timing_notes=source.timing_notes if source else None,
        notes=source.notes if source else None,
    )
    db.add(clone)
    db.flush()
    if source:
        for item in source.ingredient_entries:
            db.add(InstanceIngredient(instance_id=clone.id, product_id=item.product_id, line=item.line, amount=item.amount, unit=item.unit, notes=item.notes, position=item.position))
        for step in source.steps:
            db.add(RecipeStep(instance_id=clone.id, position=step.position, action_type=step.action_type, instruction=step.instruction, duration=step.duration, duration_unit=step.duration_unit, temperature=step.temperature, temperature_unit=step.temperature_unit, equipment_setting=step.equipment_setting, notes=step.notes))
    db.commit()
    db.refresh(clone)
    return to_instance(clone)


@app.post("/instances/{instance_id}/ingredients", response_model=IngredientEntryRead, status_code=201)
def add_instance_ingredient(instance_id: int, payload: IngredientEntryCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    instance = instance_for_user(instance_id, user, db)
    assert_instance_editable(instance)
    if payload.product_id and not db.get(IngredientProduct, payload.product_id):
        raise HTTPException(status_code=422, detail="Product not found")
    entry = InstanceIngredient(instance_id=instance.id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.post("/instances/{instance_id}/steps", response_model=StepRead, status_code=201)
def add_instance_step(instance_id: int, payload: StepCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    instance = instance_for_user(instance_id, user, db)
    assert_instance_editable(instance)
    step = RecipeStep(instance_id=instance.id, **payload.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@app.post("/instances/{instance_id}/media", response_model=MediaRead, status_code=201)
def add_instance_media(instance_id: int, payload: MediaCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    instance = instance_for_user(instance_id, user, db)
    assert_instance_editable(instance)
    media = Media(instance_id=instance.id, **payload.model_dump())
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@app.get("/ingredient-types", response_model=list[IngredientTypeRead])
def list_ingredient_types(_: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(IngredientType).order_by(IngredientType.name)).all()


@app.post("/ingredient-types", response_model=IngredientTypeRead, status_code=201)
def create_ingredient_type(payload: IngredientTypeCreate, _: User = Depends(current_user), db: Session = Depends(get_db)):
    if db.scalar(select(IngredientType).where(IngredientType.name == payload.name)):
        raise HTTPException(status_code=409, detail="Ingredient type already exists")
    item = IngredientType(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/products", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, _: User = Depends(current_user), db: Session = Depends(get_db)):
    if payload.upc:
        existing = db.scalar(select(IngredientProduct).where(IngredientProduct.upc == payload.upc))
        if existing:
            return existing
    if payload.ingredient_type_id and not db.get(IngredientType, payload.ingredient_type_id):
        raise HTTPException(status_code=422, detail="Ingredient type not found")
    product = IngredientProduct(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.get("/products/upc/{upc}", response_model=ProductRead)
def get_product_by_upc(upc: str, _: User = Depends(current_user), db: Session = Depends(get_db)):
    product = db.scalar(select(IngredientProduct).where(IngredientProduct.upc == upc))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/recipes/{recipe_id}/compare", response_model=list[InstanceRead])
def compare_instances(recipe_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [to_instance(item) for item in recipe_for_user(recipe_id, user, db).instances]


@app.post("/recipes/{recipe_id}/finalize", response_model=RecipeRead)
def finalize_recipe(recipe_id: int, payload: FinalizeRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    recipe = recipe_for_user(recipe_id, user, db)
    instance = next((item for item in recipe.instances if item.id == payload.instance_id), None)
    if not instance:
        raise HTTPException(status_code=422, detail="The selected attempt does not belong to this recipe")
    recipe.status = RecipeStatus.FINALIZED
    recipe.finalized_at = datetime.utcnow()
    recipe.finalized_instance_id = instance.id
    db.commit()
    db.refresh(recipe)
    return to_recipe(recipe)


@app.post("/recipes/{recipe_id}/variants", response_model=RecipeRead, status_code=201)
def create_variant(recipe_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    source = recipe_for_user(recipe_id, user, db)
    instance = next((item for item in source.instances if item.id == source.finalized_instance_id), None)
    variant = RecipeProfile(
        user_id=user.id,
        parent_recipe_id=source.id,
        name=f"{source.name} variant",
        description=source.description,
        source_url=source.source_url,
        ingredients=instance.ingredients if instance else source.ingredients,
        instructions=instance.instructions if instance else source.instructions,
        prep_time=source.prep_time,
        cook_time=source.cook_time,
        total_time=source.total_time,
        yield_text=source.yield_text,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return to_recipe(variant)
