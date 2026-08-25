# BatchBook

BatchBook is an MVP for developing recipes through dated, preservable attempts. A **Recipe Profile** is the continuing project; a **Recipe Instance** is a specific batch or version made on a date.

## Supabase authentication setup

BatchBook uses Supabase Auth email magic links. It does not store application passwords or accept a
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

## Mobile testing

BatchBook is an installable Progressive Web App (PWA). This is the fastest mobile workflow because
the web and mobile experiences use the same frontend codebase.

For day-to-day phone testing, run the frontend on your LAN:

```powershell
cd frontend
npm run dev -- --host 0.0.0.0
```

Set `VITE_API_URL` in `frontend/.env.local` to the API's LAN address (for example,
`http://192.168.1.25:8000`), then run the API on the LAN:

```powershell
$env:CORS_ALLOW_ORIGINS = "http://192.168.1.25:5173"
uvicorn app.main:app --reload --host 0.0.0.0
```

On the phone, open the Vite LAN URL shown by the terminal. Both devices must be on the same network.

For install testing, deploy the frontend over HTTPS, open it in Chrome on Android or Safari on iOS,
and choose **Install app** or **Add to Home Screen**. Add the deployed frontend URL to Supabase's
redirect URLs and to `CORS_ALLOW_ORIGINS`.

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
