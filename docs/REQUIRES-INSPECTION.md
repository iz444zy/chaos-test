# Requires inspection

Record questions, decisions, and findings that need product-owner attention here as they arise.

## Open items

- The MVP stores media as user-provided URLs rather than handling binary uploads. Confirm whether local file uploads are required before the next iteration.
- Supabase project URL and publishable key must be placed in local/deployment environment variables
  (`VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, and backend `SUPABASE_URL`); no values
  are committed.
- Before deployment, set the exact production Site URL and all approved frontend redirect URLs in
  Supabase Auth. Confirm the email provider, sender/domain, rate limits, and magic-link template.
- Review pre-Supabase production users for duplicate, changed, or unverified email addresses. The
  SQLite migration preserves recipe rows and adds a nullable UUID mapping; the backend links an
  unmapped legacy account only when the Supabase token has its exact email.
- Confirm that `ENABLE_DEV_LOGIN_BYPASS`, `VITE_ENABLE_DEV_LOGIN_BYPASS`, and
  `DEV_LOGIN_BYPASS_SECRET` are absent from deployed environments.
