# CHAOS Test Repository Project Prompt
## Recipe Development Tracker MVP

Build a small full-stack web application for **developing, testing, importing, iterating on, and preserving recipes**.

This project is intended to serve as a realistic but bounded test repository for **CHAOS**, so the implementation should favor:

- clear domain boundaries
- understandable architecture
- explicit data models
- incremental implementation
- meaningful Git history
- testable backend behavior
- simple but functional UI
- opportunities for multiple features to interact without unnecessary complexity

The application should remain an **MVP**. Do not expand it into a social network, nutrition platform, grocery service, meal planner, AI assistant, or production-scale recipe marketplace.

---

# 1. Product Goal

The application helps someone answer:

> "How did I make this recipe last time, what did I change, and which version did I actually like?"

A user should be able to:

1. Save or import a recipe.
2. Normalize it into a reusable **Recipe Profile**.
3. Record individual cooking/baking attempts as dated **Recipe Instances**.
4. Track exactly what ingredients, quantities, techniques, timings, and notes were used in each attempt.
5. Attach photos or videos documenting an attempt.
6. Compare the history of attempts.
7. Decide that a particular version is the finalized recipe.
8. Preserve that finalized version while optionally creating a new editable variant derived from it.

The central distinction in the data model is:

**Recipe Profile != Recipe Instance**

The profile represents the recipe as a continuing project.

An instance represents one actual attempt/batch/version of making it.

---

# 2. Suggested MVP Stack

Use a conventional, understandable stack.

## Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite for local development
- Alembic if migrations are introduced
- pytest

## Frontend

- React
- TypeScript
- Vite or another minimal React build setup
- simple CSS or a lightweight styling solution

Avoid adding a large UI framework unless there is a strong implementation reason.

## General

The frontend and backend should remain clearly separated.

Suggested structure:

```text
recipe-dev/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── db/
│   │   └── main.py
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── types/
│       └── App.tsx
├── docs/
└── README.md
```

Do not over-engineer the repository structure before the domain requires it.

---

# 3. Authentication / Welcome Screen

The application should open on a simple welcome screen.

Display:

- application name
- brief description
- Log In
- Create Account

Authentication can be intentionally simple for this test repository.

The important requirement is that recipe data belongs to a user.

Do not implement:

- OAuth
- social login
- password recovery
- MFA
- complicated session management

A straightforward local username/email + password flow is sufficient.

After login, route the user to the recipe dashboard.

---

# 4. Recipe Dashboard

The authenticated home page should show:

## Existing Recipes

Each recipe card/list entry should show:

- recipe name
- optional thumbnail
- status
  - Developing
  - Finalized
- number of recorded attempts
- most recent attempt date

Selecting a recipe opens its Recipe Profile.

## Primary actions

Provide two obvious actions:

### Create New Recipe

Start an empty recipe manually.

### Import Recipe

Allow the user to begin from an existing recipe found online.

---

# 5. Recipe Import

A user should be able to enter a recipe URL.

Example:

```text
https://example.com/chocolate-chip-cookies
```

The backend should attempt to extract recipe information.

Prefer structured recipe metadata such as:

- JSON-LD
- schema.org Recipe markup

When available, parse:

- recipe title
- ingredient lines
- instructions
- prep time
- cook time
- total time
- servings/yield
- source URL

The imported result must **never be assumed correct**.

After importing, display a review/edit screen where the user can correct the parsed information before saving the Recipe Profile.

If parsing fails, preserve the source URL and allow the recipe to be entered manually.

Do not attempt to build a universal web scraper in the MVP.

---

# 6. Recipe Profile

A Recipe Profile is the persistent container for a recipe and its development history.

Suggested fields:

```text
RecipeProfile
- id
- user_id
- name
- description
- source_url
- status
- created_at
- updated_at
- finalized_at
- finalized_instance_id
- parent_recipe_id / parent_variant_id (optional)
```

Possible statuses:

```text
DEVELOPING
FINALIZED
```

A Recipe Profile contains:

- general recipe information
- recipe-level media
- an ordered history of Recipe Instances
- optional relationship to another recipe from which it was derived

---

# 7. Recipe Instances

Every time the user makes or modifies the recipe, they should create a new **Recipe Instance**.

Example:

```text
Chocolate Chip Cookies

Attempt 1 — August 20
Attempt 2 — August 22
Attempt 3 — August 24
Final Recipe — August 25
```

Each instance represents one specific recipe configuration.

Suggested fields:

```text
RecipeInstance
- id
- recipe_profile_id
- instance_number
- title / label
- made_at
- created_at
- overall_notes
- result_notes
- rating (optional)
```

The first instance should normally represent:

> Base Recipe / Attempt 1

When creating a later instance, the application should allow the user to:

### Start from previous attempt

Copy the previous instance's ingredients and steps.

or

### Start from base recipe

Copy Attempt 1.

The copied data must become independent data belonging to the new instance.

Editing Attempt 3 must never mutate Attempt 2.

Historical recipe instances are records of what happened at that point in time.

---

# 8. Ingredients

Ingredients should be semi-normalized.

Each ingredient entry needs to distinguish between:

1. the conceptual ingredient
2. the specific product used
3. the measured amount used in this recipe instance

Example:

```text
Ingredient Type:
Milk

Product:
Organic Valley Whole Milk

UPC:
093966000147

Amount:
240

Unit:
mL
```

Another instance could use:

```text
Ingredient Type:
Milk

Product:
Horizon 2% Milk

UPC:
...

Amount:
1

Unit:
cup
```

---

# 9. Ingredient Types

Provide basic normalized ingredient categories such as:

- flour
- sugar
- brown sugar
- milk
- cream
- butter
- eggs
- oil
- salt
- baking soda
- baking powder
- chocolate
- vanilla
- water
- cheese
- custom

These values should be extensible.

Users must be able to create a custom ingredient type when necessary.

Avoid attempting to model every possible ingredient in existence.

---

# 10. Ingredient Products and UPC Codes

Support recording the specific product used.

Suggested model:

```text
IngredientProduct
- id
- ingredient_type_id
- name
- brand
- upc
- notes
```

A product can optionally have a UPC barcode.

Example:

```text
Ingredient Type:
Butter

Brand:
Kerrygold

Product:
Unsalted Butter

UPC:
...
```

Once a UPC/product association has been saved, scanning the same UPC later should retrieve the existing product.

---

# 11. Barcode Scanning

The frontend should support barcode entry.

For the MVP:

- allow manual UPC entry
- optionally support camera-based barcode scanning if it can be implemented without major complexity
- treat scanning as an input mechanism, not a separate subsystem

Workflow:

```text
Scan UPC
    ↓
Existing product?
    ↓
Yes → select product
No → create product
    ↓
Associate product with Ingredient Type
```

A third-party UPC/product database is **not required**.

The user may manually identify the scanned item.

Example:

```text
UPC: 123456789
Brand: King Arthur
Product: All-Purpose Flour
Ingredient Type: Flour
```

Future scans can reuse the saved association.

---

# 12. Ingredient Measurements

An ingredient used in a Recipe Instance must record an amount and unit.

Support several common unit families.

## Weight

- g
- kg
- oz
- lb

## Volume

- mL
- L
- tsp
- tbsp
- cup
- fl oz

## Quantity

- item
- piece
- egg
- package

The data model should store:

```text
amount
unit
```

Example:

```text
250 g flour
2 eggs
1.5 cups milk
1 tsp salt
```

Do not implement automatic unit conversion unless needed for basic UI behavior.

The application should faithfully record what the user actually measured.

---

# 13. Recipe Procedure

Ingredients alone are insufficient for recipe development.

Each Recipe Instance must also contain an ordered sequence of execution steps.

Example:

```text
1. Cream butter and sugar
2. Add eggs
3. Mix dry ingredients separately
4. Combine wet and dry ingredients
5. Chill dough for 45 minutes
6. Bake at 350°F for 12 minutes
7. Cool for 15 minutes
```

Steps should be stored in an explicitly ordered structure.

Suggested model:

```text
RecipeStep
- id
- recipe_instance_id
- position
- action_type
- instruction
- duration
- duration_unit
- temperature
- temperature_unit
- equipment_setting
- notes
```

Not every field needs to be populated.

---

# 14. Normalized Step / Technique Types

Provide several reusable action types.

Examples:

- prep
- measure
- mix
- stir
- whisk
- beat
- fold
- knead
- blend
- rest
- chill
- freeze
- thaw
- preheat
- bake
- roast
- boil
- simmer
- fry
- cook
- cool
- assemble
- serve
- custom

Users should be allowed to choose **Custom** and write their own action.

Do not create a complicated cooking ontology.

The purpose of normalization is primarily to make changes between attempts easier to understand.

---

# 15. Technique Attributes

Recipe steps may optionally include structured information.

Examples:

### Mixing

```text
Action: Mix
Duration: 3 minutes
Setting: Medium
```

### Baking

```text
Action: Bake
Temperature: 350
Temperature Unit: °F
Duration: 12 minutes
```

### Cooling

```text
Action: Cool
Duration: 15 minutes
```

### Freezing

```text
Action: Freeze
Duration: 2 hours
```

### Preparation

```text
Action: Chop
Instruction: Finely chop chocolate
```

The user should always retain a free-text instruction field even when structured attributes are available.

---

# 16. Miscellaneous Notes

Every Recipe Instance should contain a general notes section.

Possible uses:

```text
Dough seemed too wet.

Cookies spread less than last time.

Try another 15 g flour next batch.

Used a dark baking tray instead of aluminum.

Everyone preferred this batch.
```

Provide at least:

### Attempt Notes

Things intentionally changed or worth remembering.

### Result Notes

Observations after making/eating the recipe.

Do not force these notes into normalized structures.

---

# 17. Media

Users should be able to attach media.

Supported MVP media:

- images
- video files

Media can belong to:

### Recipe Profile

Example:

- finished recipe hero image
- general reference photo

### Recipe Instance

Example:

- dough consistency
- progress photo
- final batch
- short technique video

Suggested model:

```text
MediaAttachment
- id
- recipe_profile_id
- recipe_instance_id
- media_type
- file_path / URL
- caption
- created_at
```

Only one parent relationship should generally be populated.

For local development, storing uploaded files locally is acceptable.

Do not introduce cloud object storage into the MVP.

---

# 18. Instance History

The Recipe Profile should display its attempts chronologically.

Example:

```text
Chocolate Chip Cookies

Development History

Attempt 1
August 14
Base imported recipe

↓

Attempt 2
August 17
+20g flour
Chilled 30 minutes

↓

Attempt 3
August 20
Used brown butter
Reduced sugar

↓

Attempt 4
August 23
Baked 2 minutes longer
★★★★★

↓

Finalized Recipe
August 24
```

The MVP does not require an advanced automatic diff engine.

However, the architecture should make it possible to compare instances later.

A basic comparison screen may simply display two instances side-by-side.

---

# 19. Finalizing a Recipe

A user can decide that one Recipe Instance represents the recipe they want to preserve.

Provide:

```text
Finalize This Recipe
```

When selected:

1. the Recipe Profile status becomes `FINALIZED`
2. the selected Recipe Instance becomes the finalized instance
3. `finalized_at` is recorded
4. the finalized recipe remains readable
5. existing historical instances remain unchanged

The finalized instance represents the canonical recipe.

---

# 20. Finalized Recipe Locking

Finalization must protect the canonical recipe from accidental mutation.

The finalized Recipe Instance should be effectively immutable through normal application workflows.

The user should **not** continue editing that same instance.

Instead provide:

```text
Create New Variant
```

---

# 21. Recipe Variants

A finalized recipe may become the basis for additional experimentation.

Example:

```text
Chocolate Chip Cookies
FINALIZED

├── Original Final Recipe
├── Dark Chocolate Variant
└── Gluten-Free Experiment
```

Selecting:

```text
Create New Variant
```

should:

1. create a new Recipe Profile
2. record the original recipe as its parent
3. copy the finalized recipe into the new profile's initial instance
4. mark the new Recipe Profile as `DEVELOPING`
5. allow future experimentation without modifying the original

The relationship between recipes should be preserved.

---

# 22. Core Domain Relationships

Conceptually:

```text
User
 └── RecipeProfile
      ├── RecipeInstance
      │    ├── RecipeIngredient
      │    │    ├── IngredientType
      │    │    └── IngredientProduct
      │    ├── RecipeStep
      │    └── MediaAttachment
      │
      ├── MediaAttachment
      │
      └── Variant RecipeProfile
```

A Recipe Profile has many Recipe Instances.

A Recipe Instance has many Recipe Ingredients.

A Recipe Instance has many ordered Recipe Steps.

A product belongs to an Ingredient Type.

A UPC may identify an Ingredient Product.

A Recipe Profile may descend from another Recipe Profile.

---

# 23. Primary Screens

Keep the UI limited to the screens necessary for the core workflow.

## Screen 1 — Welcome / Authentication

```text
BatchBook

Develop recipes.
Record every attempt.
Keep the version that works.

[ Log In ]
[ Create Account ]
```

---

## Screen 2 — Recipe Dashboard

```text
My Recipes

[ + New Recipe ]
[ Import Recipe ]

Developing
- Chocolate Chip Cookies — 4 attempts
- Pizza Dough — 2 attempts

Finalized
- Brownies — Finalized Aug 15
```

---

## Screen 3 — Import Recipe

```text
Import Recipe

Recipe URL:
[ __________________________ ]

[ Import ]

Parsed Recipe Preview
...
```

Allow editing before saving.

---

## Screen 4 — Recipe Profile

```text
Chocolate Chip Cookies

Status: Developing
Source: example.com

[ New Attempt ]

Attempts

#4 — Aug 24
#3 — Aug 22
#2 — Aug 19
#1 — Base Recipe
```

---

## Screen 5 — Recipe Instance Editor

Sections:

```text
Attempt Information

Ingredients

Procedure

Photos & Videos

Attempt Notes

Result Notes

[ Save Attempt ]
```

Ingredients and steps should be reorderable if reasonably simple to implement.

---

## Screen 6 — Recipe Instance Detail

Read-only summary of one attempt.

Display:

- ingredients
- products used
- measurements
- procedure
- structured timings/settings
- notes
- media
- date

Actions:

```text
[ Create Next Attempt ]
[ Finalize This Recipe ]
```

---

## Screen 7 — Finalized Recipe

Display the canonical recipe clearly.

Actions:

```text
[ Create New Variant ]
```

Do not expose ordinary editing controls for the finalized instance.

---

# 24. Example Workflow

Use this workflow when validating the application.

## Create recipe

User creates:

```text
Chocolate Chip Cookies
```

Attempt 1 contains:

```text
250 g flour
170 g butter
150 g sugar
2 eggs
200 g chocolate

Mix
Chill 30 min
Bake 350°F for 10 min
Cool 10 min
```

Result note:

```text
Too much spreading.
Centers slightly underdone.
```

---

## Attempt 2

User selects:

```text
Create Next Attempt
```

The app copies Attempt 1.

User changes:

```text
Flour:
250 g → 275 g

Chill:
30 min → 1 hour

Bake:
10 min → 12 min
```

Result:

```text
Much better structure.
Slightly too crispy.
```

---

## Attempt 3

User changes:

```text
Bake:
12 min → 11 min
```

Result:

```text
Best version.
```

User selects:

```text
Finalize This Recipe
```

Attempt 3 becomes the canonical recipe.

---

## Variant

Later the user wants to test dark chocolate.

They select:

```text
Create New Variant
```

New Recipe Profile:

```text
Chocolate Chip Cookies — Dark Chocolate
```

Its first attempt starts with the finalized recipe but remains editable.

The original finalized Chocolate Chip Cookies recipe remains unchanged.

---

# 25. MVP API Surface

A reasonable REST API might include:

```text
/auth/register
/auth/login

/recipes
/recipes/{recipe_id}
/recipes/{recipe_id}/instances
/recipes/{recipe_id}/finalize
/recipes/{recipe_id}/variants

/instances/{instance_id}
/instances/{instance_id}/ingredients
/instances/{instance_id}/steps
/instances/{instance_id}/media

/ingredient-types
/products
/products/upc/{upc}

/imports/recipe

/media
```

Exact endpoint structure can evolve if the implementation provides a cleaner design.

Avoid creating endpoints before they are needed.

---

# 26. Minimum Backend Behaviors to Test

Include automated tests covering important domain invariants.

At minimum test:

### Recipe creation

A user can create a Recipe Profile.

### Instance creation

A recipe can contain multiple Recipe Instances.

### Instance isolation

Changing a later instance does not mutate previous instances.

### Clone previous attempt

A new attempt can copy ingredients and steps from another instance.

### Ingredient product reuse

A known UPC resolves to its saved Ingredient Product.

### Ordered procedure

Recipe Steps retain their execution order.

### Finalization

A Recipe Instance can become the finalized instance.

### Final recipe immutability

Normal update operations cannot mutate the finalized canonical instance.

### Variant creation

A variant can be created from a finalized recipe without altering its parent.

### Ownership

One user cannot access another user's recipes.

---

# 27. Seed Data

Provide optional development seed data.

Include at least:

```text
User:
demo@example.com
```

Recipe:

```text
Chocolate Chip Cookies
```

with three Recipe Instances showing meaningful changes.

Include several Ingredient Types and Ingredient Products.

This makes the repository easier to inspect and exercise without manually constructing every state.

---

# 28. MVP Definition of Done

The MVP is complete when a user can:

- [ ] create an account and log in
- [ ] view their recipe dashboard
- [ ] create a blank recipe
- [ ] import a recipe from a URL when structured recipe metadata is available
- [ ] manually correct imported recipe information
- [ ] create the initial recipe attempt
- [ ] add ingredients
- [ ] associate ingredients with normalized ingredient types
- [ ] record specific ingredient products
- [ ] record/reuse UPC values
- [ ] record ingredient quantities and units
- [ ] create ordered preparation/cooking steps
- [ ] record structured timing, temperature, and technique information
- [ ] add miscellaneous attempt/result notes
- [ ] attach photos or videos
- [ ] create additional attempts by copying a previous attempt
- [ ] view historical attempts
- [ ] verify that editing a new attempt does not alter old attempts
- [ ] finalize one attempt
- [ ] prevent ordinary mutation of the finalized recipe
- [ ] create a new recipe variant from the finalized version
- [ ] preserve the parent/variant relationship

---

# 29. Explicitly Out of Scope

Do **not** implement these unless the core MVP is already complete and the task explicitly requests expansion:

- AI recipe generation
- AI recipe recommendations
- AI ingredient substitution
- nutrition calculations
- calorie tracking
- grocery lists
- meal planning
- shopping integrations
- social feeds
- followers
- public profiles
- recipe ratings from other users
- comments
- restaurant features
- inventory management
- pantry tracking
- automatic ingredient-price tracking
- advanced automatic recipe diffs
- real-time collaboration
- cloud storage infrastructure
- distributed services
- microservices
- Kubernetes
- production payment systems
- production OAuth
- complex permission systems
- comprehensive UPC databases
- universal website scraping
- native mobile applications

Keep the system intentionally boring where possible.

The interesting complexity should come from the **recipe-development domain**, not infrastructure.

---

# 30. Engineering Principles

When implementing this project:

## Preserve history

Recipe Instances are historical records.

Never silently mutate an earlier attempt because a later attempt changed.

## Prefer explicit models

Recipe, instance, ingredient, product, measurement, step, and media concepts should have identifiable boundaries.

## Normalize selectively

Normalize information that benefits from comparison or reuse:

- ingredient type
- product identity
- UPC
- amount
- unit
- step order
- technique
- duration
- temperature

Do not attempt to normalize subjective observations.

Keep things like:

```text
"texture seemed weird"
```

as notes.

## Avoid premature abstraction

Do not build generalized frameworks when straightforward application code is sufficient.

## Maintain domain invariants

The application should make invalid states difficult to create.

Examples:

- finalized instances should not be casually editable
- instance ordering should remain stable
- variants should know their parent
- changing Attempt 4 should never rewrite Attempt 3

## Favor inspectability

The repository exists partly as an orchestration test surface.

Favor:

- readable naming
- predictable module boundaries
- concise documentation
- meaningful tests
- understandable commits
- explicit state transitions

over cleverness.

---

# 31. Development Sequence

Implement the application incrementally.

A sensible order is:

```text
Phase 1
Repository skeleton
Database connection
Recipe/User models

Phase 2
Recipe Profile CRUD
Recipe Instance CRUD

Phase 3
Ingredients
Ingredient Types
Products
Measurements

Phase 4
Ordered Recipe Steps
Structured technique attributes

Phase 5
Attempt cloning/history

Phase 6
Finalization and locking

Phase 7
Variant creation

Phase 8
Recipe import

Phase 9
Media attachments

Phase 10
UI polish and end-to-end validation
```

Later phases should build on existing working behavior rather than replacing previous implementations wholesale.

---

# 32. CHAOS Test-Repo Considerations

This repository is specifically intended to be interacted with by agentic development infrastructure.

Therefore:

1. Keep requirements in the repository.
2. Keep implementation tasks reasonably separable.
3. Avoid giant single-file implementations.
4. Include tests that provide agents with objective feedback.
5. Prefer small commits corresponding to coherent behaviors.
6. Do not perform broad unsolicited refactors while implementing unrelated features.
7. Preserve existing behavior unless a requirement explicitly changes it.
8. Update documentation when architecture or behavior materially changes.
9. Surface ambiguity instead of inventing business requirements.
10. Favor work that can be validated locally.

The application should be complex enough that features touch multiple layers:

```text
UI
→ API
→ validation
→ service/domain behavior
→ persistence
→ tests
```

but small enough that a developer can understand the entire repository.

This makes the project suitable for testing:

- task decomposition
- parallel agent work
- context hydration
- repository inspection
- dependency-aware execution
- Git coordination
- conflicting edits
- test-driven validation
- persistent task state
- integration workflows

---

# 33. Guiding Product Principle

When deciding whether something belongs in the MVP, use this question:

> Does this help the user accurately preserve what they made, understand how one attempt differed from another, or turn a successful attempt into a reusable recipe?

If not, defer it.

The MVP is fundamentally a **recipe development notebook with structured history**, not a general food application.