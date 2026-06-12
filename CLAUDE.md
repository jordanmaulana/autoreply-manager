# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Backend uses `uv`, frontend uses `pnpm`. Most tasks are in the Makefile:

```bash
make dev        # Django dev server on :8000 (uv run manage.py runserver)
make lint       # ruff format . && ruff check . --fix
make mmg        # makemigrations
make migrate    # migrate
make web        # React dev server (cd frontend && pnpm run dev, port 5173)
make tw-run     # Tailwind watcher for Django templates (static/input.css → static/output.css)
make dock       # docker compose down/build/up using .env.docker
make upgrade    # uv sync + lock upgrade
```

Frontend (run inside `frontend/`): `pnpm dev`, `pnpm build` (tsc -b + vite build), `pnpm lint` (eslint).

There is no test suite configured. Ruff config lives in `pyproject.toml` (line length 100, py310, rules E/F/I/B/UP).

API smoke-test `.http` files live in `_rest/` (committed) and `.rest.local/` (local only).

## Environment

Copy `.env.example` to `.env` (loaded by `core/settings.py` via python-dotenv). The database is **always Postgres with pgvector** (image `pgvector/pgvector:pg16`; pgvector is required for RAG). Host dev: `make db` starts the container matching the `.env.example` defaults (app/app/app on localhost). Docker compose uses `.env.docker` and sets `POSTGRES_HOST=postgres`. Frontend reads `VITE_API_URL` and `VITE_GOOGLE_CLIENT_ID`.

Feature env: `OPENAI_API_KEY` (embeddings + replies), `INSTAGRAM_APP_ID/SECRET`, `THREADS_APP_ID/SECRET`, `WHATSAPP_APP_SECRET`, `META_WEBHOOK_VERIFY_TOKEN`. `SITE_URL` must be a public HTTPS URL for Meta webhooks/OAuth callbacks (ngrok in dev).

## Architecture

Two separate frontends share one Django backend:

1. **React SPA** (`frontend/`) — the user-facing app. React 19, Vite, TanStack Router (file-based routes in `src/routes/`, route tree auto-generated), TanStack Query, jotai for state, shadcn/radix + Tailwind v4. Talks to the backend over `/api/v1/` with DRF token auth.
2. **Django templates** (`templates/` + `static/`) — superuser-only admin dashboard at `/dashboard/` (session auth, `SuperuserRequiredMixin` in `core/views.py`). Styled with its own Tailwind build (`make tw-run`), independent of the SPA's Tailwind.

### Backend layout

- `core/` is both the Django project (settings, urls, wsgi) and the single app (models, views, payments). `api/` holds only DRF endpoint modules.
- API endpoints are function-based DRF views in `api/v1/<domain>_api.py`, wired in `api/v1/urls.py` under `/api/v1/`. Default DRF policy is TokenAuthentication + IsAuthenticated; open endpoints opt out with `@permission_classes([AllowAny])`.
- **Auth flow**: SPA gets a Google ID token → `POST /api/v1/auth/google/` → `GoogleAuthSerializer` verifies it (google-auth) → user is get-or-created by email → DRF token returned. Frontend stores the token in localStorage and sends `Authorization: Token <key>` (`frontend/src/lib/api.ts`); auth feature code lives in `frontend/src/features/auth/`.
- **Models**: subclass `core.models.BaseModel` — string primary key from `bson.ObjectId`, `created_on`/`updated_on`/`actor` fields. `AppSetting` is a typed key-value store (`AppSetting.get(key, "str"|"int"|"float"|"bool", default)`).
- **Payments**: Mayar client in `core/payments/mayar.py` (payment links, webhook token verification, `PAID_STATUSES`). Webhook endpoint at `/api/v1/payments/mayar/webhook/` is a stub — subscription activation on paid status is intentionally left to be implemented per domain.
- **Auto-reply / RAG**: `core/rag/` — chunking (tiktoken) → OpenAI embeddings → pgvector cosine retrieval → gpt-4o-mini reply. Embedding runs in a daemon thread (`core/rag/runner.py`) with a pending/processing/ready/failed status machine on `Knowledge` (atomic claim + 15-min stale-claim recovery; no celery). `core/social/` holds per-platform clients: Instagram DMs and WhatsApp Cloud API arrive via signed Meta webhooks (`/api/v1/webhooks/<platform>/`, X-Hub-Signature-256); Threads replies are discovered by the `poll_threads` management command (no Threads webhooks at MVP). One `SocialAccount` links to one `Knowledge` (knowledge shared by many accounts). `ReplyLog`'s unique `(account, platform_message_id)` is the idempotency guard — never dedupe in memory. IG/Threads OAuth callbacks recover the user from a signed `state` (TimestampSigner, AllowAny); WhatsApp connects via pasted WABA credentials (Embedded Signup deliberately skipped). `manage.py refresh_tokens` must run daily in production (IG/Threads tokens last ~60 days). Access tokens are stored plaintext — never expose them in serializers.

### Deployment

Single backend image (`Dockerfile.backend`): a node stage builds the template Tailwind CSS, then a python/uv stage runs gunicorn with whitenoise serving static files. `docker/backend-entrypoint.sh` waits for Postgres and runs migrate + collectstatic when `ROLE=web`. `update.sh` is the pull-build-migrate deploy script. The React SPA is not part of this image.
