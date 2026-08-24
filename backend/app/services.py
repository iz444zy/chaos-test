import json
import re
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen

from .schemas import ImportPreview


class JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json_ld = False
        self.parts: list[str] = []
        self.objects: list[object] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
            self.in_json_ld = True
            self.parts = []

    def handle_data(self, data):
        if self.in_json_ld:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_json_ld:
            self.in_json_ld = False
            try:
                self.objects.append(json.loads("".join(self.parts)))
            except json.JSONDecodeError:
                pass


def _find_recipe(data: object) -> dict | None:
    if isinstance(data, list):
        for item in data:
            recipe = _find_recipe(item)
            if recipe:
                return recipe
    elif isinstance(data, dict):
        types = data.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if "Recipe" in types:
            return data
        for key in ("@graph", "mainEntity"):
            if key in data:
                recipe = _find_recipe(data[key])
                if recipe:
                    return recipe
    return None


def _as_lines(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [line.strip() for line in re.split(r"\n|\r", value) if line.strip()]
    return []


def import_recipe(url: str) -> ImportPreview:
    fallback = ImportPreview(name="Untitled recipe", source_url=url, parse_succeeded=False)
    try:
        request = Request(url, headers={"User-Agent": "RecipeDevelopmentTracker/1.0"})
        with urlopen(request, timeout=8) as response:
            content = response.read().decode(response.headers.get_content_charset() or "utf-8")
    except (URLError, TimeoutError, UnicodeDecodeError, ValueError):
        return fallback

    parser = JsonLdParser()
    parser.feed(content)
    for item in parser.objects:
        recipe = _find_recipe(item)
        if recipe:
            return ImportPreview(
                name=recipe.get("name") or "Untitled recipe",
                description=recipe.get("description"),
                source_url=url,
                ingredients=_as_lines(recipe.get("recipeIngredient")),
                instructions=[
                    step.get("text", str(step)) if isinstance(step, dict) else str(step)
                    for step in recipe.get("recipeInstructions", [])
                ],
                prep_time=recipe.get("prepTime"),
                cook_time=recipe.get("cookTime"),
                total_time=recipe.get("totalTime"),
                yield_text=str(recipe.get("recipeYield")) if recipe.get("recipeYield") else None,
                parse_succeeded=True,
            )
    return fallback
