# Backend

Install dependencies with `python -m pip install -r requirements.txt`, then run:

```powershell
uvicorn app.main:app --reload
```

The API uses SQLite (`recipe_dev.db`) and validates Supabase access tokens from
`Authorization: Bearer <access_token>`. Set `SUPABASE_URL` to the project URL before running the
server. See the root README for Supabase Auth configuration and the explicitly local-only development
login bypass.
