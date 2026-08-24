# Recipe Lab

Recipe Lab is an MVP for developing recipes through dated, preservable attempts. A **Recipe Profile** is the continuing project; a **Recipe Instance** is a specific batch or version made on a date.

## Supabase authentication setup

Recipe Lab uses Supabase Auth email magic links. It does not store application passwords or accept a
client-provided user ID.

1. Create a Supabase project.
2. In **Authentication > URL Configuration**, set the **Site URL** to your deployed frontend URL
   (use `http://localhost:5173` locally) and add every local and deployed frontend origin to
   **Redirect URLs**.
3. In **Authentication > Providers > Email**, enable email sign-ins. Configure the email template
   and delivery provider appropriate for your environment; the template must preserve Supabase's
   confirmation link.
4. The repository includes ignored local placeholders at `frontend/.env.local` and `backend/.env`.
   Fill them with your project values. Vite loads the frontend file, and the backend loads its file
   automatically when it starts. The committed `.env.example` files make the setup reproducible.
   Use the project's
   publishable/anon key only; never put a Supabase service-role key in the frontend or this repo.

## Run locally

1. Start the API:
   ```powershell
   cd backend
   python -m pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
2. In a second terminal, start the UI:
   ```powershell
   cd frontend
   npm install
   # Replace VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in .env.local.
   npm run dev
   ```

Open the Vite URL shown in the terminal and request a sign-in link. Supabase restores the session
after the redirect, and the frontend sends its access token as `Authorization: Bearer <token>`.

### Development login bypass

For isolated local testing only, set both `VITE_ENABLE_DEV_LOGIN_BYPASS=true` and
`ENABLE_DEV_LOGIN_BYPASS=true`, plus a long random `DEV_LOGIN_BYPASS_SECRET` in the backend
environment. This exposes a **Development login bypass** button that receives a server-issued,
short-scope development token. Keep all three settings disabled or unset in deployed environments.

The backend automatically adds a nullable Supabase UUID mapping to an existing SQLite `users` table,
so existing recipe ownership rows are preserved. When a Supabase token carries the exact email of an
unmapped legacy account, the backend links that account to the Supabase UUID. Review duplicate,
changed, or unverified legacy email addresses before migrating a production database.

## Key behavior

- Import favors JSON-LD/schema.org Recipe metadata and always opens an editable review step.
- Recipe profiles organize the history; individual attempts capture a concrete version.
- Finalizing preserves one attempt. Create an editable variant to continue experimentation.
- Product UPCs are reusable, and structured ingredient/step API endpoints support richer attempt capture.
