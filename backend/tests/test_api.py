import os
import tempfile
import uuid

import jwt
from fastapi.testclient import TestClient

database_file = tempfile.NamedTemporaryFile(delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{database_file.name}"
os.environ["ENABLE_DEV_LOGIN_BYPASS"] = "true"
os.environ["DEV_LOGIN_BYPASS_SECRET"] = "test-only-secret-that-is-at-least-32-bytes"

from app.main import app  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402


client = TestClient(app)


def authenticated_headers():
    response = client.post("/auth/dev-login")
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def other_user_headers():
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "role": "authenticated",
            "iss": "recipe-lab-dev-login",
        },
        os.environ["DEV_LOGIN_BYPASS_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_recipe_lifecycle_and_user_ownership():
    headers = authenticated_headers()
    recipe = client.post(
        "/recipes",
        headers=headers,
        json={
            "name": "Brownies",
            "ingredients": ["100g chocolate"],
            "instructions": ["Melt chocolate"],
        },
    )
    assert recipe.status_code == 201
    recipe_id = recipe.json()["id"]

    attempt = client.post(
        f"/recipes/{recipe_id}/instances",
        headers=headers,
        json={"name": "Attempt 1", "ingredients": ["120g chocolate"], "rating": 5},
    )
    assert attempt.status_code == 201
    assert client.post(
        f"/recipes/{recipe_id}/finalize",
        headers=headers,
        json={"instance_id": attempt.json()["id"]},
    ).json()["status"] == "FINALIZED"
    variant = client.post(f"/recipes/{recipe_id}/variants", headers=headers)
    assert variant.status_code == 201
    assert variant.json()["parent_recipe_id"] == recipe_id

    denied = client.get(f"/recipes/{recipe_id}", headers=other_user_headers())
    assert denied.status_code == 404


def test_upc_reuse_step_order_clone_and_finalized_protection():
    headers = authenticated_headers()
    ingredient_type = client.post("/ingredient-types", headers=headers, json={"name": "Flour"}).json()
    product = client.post("/products", headers=headers, json={"name": "Bread flour", "upc": "12345", "ingredient_type_id": ingredient_type["id"]})
    assert product.status_code == 201
    assert client.post("/products", headers=headers, json={"name": "Other name", "upc": "12345"}).json()["id"] == product.json()["id"]
    recipe = client.post("/recipes", headers=headers, json={"name": "Loaf"}).json()
    attempt = client.post(f"/recipes/{recipe['id']}/instances", headers=headers, json={}).json()
    client.post(f"/instances/{attempt['id']}/ingredients", headers=headers, json={"line": "500g flour", "product_id": product.json()["id"]})
    client.post(f"/instances/{attempt['id']}/steps", headers=headers, json={"position": 1, "instruction": "Bake"})
    cloned = client.post(f"/recipes/{recipe['id']}/instances/clone", headers=headers)
    assert cloned.status_code == 201
    assert client.get(f"/recipes/{recipe['id']}/compare", headers=headers).status_code == 200
    client.post(f"/recipes/{recipe['id']}/finalize", headers=headers, json={"instance_id": attempt["id"]})
    assert client.post(f"/instances/{attempt['id']}/steps", headers=headers, json={"position": 2, "instruction": "Cool"}).status_code == 409
    assert client.put(f"/recipes/{recipe['id']}", headers=headers, json={"name": "Changed"}).status_code == 409


def test_requests_require_a_bearer_token_and_ignore_client_user_headers():
    assert client.get("/recipes").status_code == 401
    assert client.get("/recipes", headers={"X-User-Id": "1"}).status_code == 401


def test_development_login_bypass_is_disabled_without_its_explicit_flag(monkeypatch):
    monkeypatch.setenv("ENABLE_DEV_LOGIN_BYPASS", "false")
    assert client.post("/auth/dev-login").status_code == 404


def test_matching_legacy_email_keeps_recipe_ownership():
    supabase_user_id = str(uuid.uuid4())
    db = SessionLocal()
    legacy_user = User(email="legacy@example.com", username="legacy")
    db.add(legacy_user)
    db.commit()
    try:
        token = jwt.encode(
            {
                "sub": supabase_user_id,
                "email": "legacy@example.com",
                "role": "authenticated",
                "iss": "recipe-lab-dev-login",
            },
            os.environ["DEV_LOGIN_BYPASS_SECRET"],
            algorithm="HS256",
        )
        created = client.post(
            "/recipes",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Migrated recipe"},
        )
        assert created.status_code == 201
        db.refresh(legacy_user)
        assert legacy_user.supabase_user_id == supabase_user_id
        assert created.json()["id"]
    finally:
        db.close()
