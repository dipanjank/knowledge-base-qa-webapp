# Frontend — Knowledge Base QA

SvelteKit SPA for authentication, document management, admin user management, and RAG-based question answering.

## Tech Stack

- SvelteKit 2, Svelte 5 (runes), TypeScript
- Vite 8, adapter-node
- SPA mode (SSR disabled)

## Architecture

```
src/
├── lib/
│   ├── api.ts                  Fetch wrapper with auth and auto-refresh
│   ├── stores/
│   │   └── auth.ts             Auth state store (token, role, isAuthenticated)
│   └── components/
│       └── Navbar.svelte       Navigation bar with role-based links
├── routes/
│   ├── +layout.svelte          Auth guard + conditional navbar
│   ├── +layout.ts              Disables SSR (SPA mode)
│   ├── +page.svelte            Root redirect → /qa or /login
│   ├── login/+page.svelte      Login form
│   ├── qa/+page.svelte         Question answering (placeholder)
│   ├── documents/+page.svelte  Document list (placeholder)
│   └── admin/users/+page.svelte  Admin user management
├── app.css                     Global styles and CSS variables
└── app.html                    HTML template
```

### Key Modules

**`lib/api.ts`** — `api<T>(path, options)` fetch wrapper that:
- Attaches Bearer token from auth store
- Auto-retries on 401 by calling `/api/auth/refresh`
- Logs out on failed refresh
- Throws `ApiError` with status and detail

**`lib/stores/auth.ts`** — Svelte writable store with:
- `setToken(token, expiresIn)` — parses JWT claims, sets authenticated state
- `logout()` — clears all auth state
- Stores access token in memory (not localStorage)

**`lib/components/Navbar.svelte`** — Links to Documents, QA, and Admin (visible to admins only). Logout button calls `/api/auth/logout` and redirects to `/login`.

### Pages

| Route | Auth | Description |
|-------|------|-------------|
| `/login` | Public | Username/password form, redirects to `/qa` on success |
| `/qa` | Required | Question answering interface (placeholder) |
| `/documents` | Required | Document list (placeholder) |
| `/admin/users` | Admin | Create users (shows generated password once), list users, delete non-admin users |

### Auth Flow

1. User submits credentials on `/login`
2. Backend returns access token + sets httpOnly refresh cookie
3. Access token stored in memory via auth store
4. `api()` wrapper attaches token to all requests
5. On 401, wrapper attempts silent refresh via cookie
6. On failed refresh, user is logged out and redirected to `/login`
7. Layout guard redirects unauthenticated users to `/login`

## Development

```bash
cd frontend
npm run dev       # Dev server on :5173, proxies /api → localhost:8000
npm run build     # Production build
npm run check     # Type check
```

The Vite dev server proxies `/api` requests to the backend at `http://localhost:8000`.

## Production

Built with `adapter-node`, runs on port 3000. In production, the ALB routes `/api/*` to the backend and `/*` to the frontend (same domain, no CORS needed).

## Styling

Global CSS variables defined in `app.css`:

| Variable | Value |
|----------|-------|
| `--color-bg` | `#ffffff` |
| `--color-text` | `#1a1a1a` |
| `--color-primary` | `#3b82f6` |
| `--color-primary-hover` | `#2563eb` |
| `--color-border` | `#e5e7eb` |
| `--color-muted` | `#6b7280` |

Components use scoped `<style>` blocks referencing these variables.
