# SOWnia — Free Stack Deployment (Vercel + Render + Neon)

Deploys SOWnia end-to-end on free tiers, no cloud VM cost:

| Component | Service | Cost |
|---|---|---|
| Frontend (Next.js) | **Vercel** | Free |
| Backend (FastAPI) | **Render** | Free |
| Postgres | **Neon** | Free (persistent) |
| LLM | Google Gemini API | Free tier |

**How auth stays working across two hosts:** the browser only ever calls
same-origin `/api/...` on the Vercel domain; Vercel's Next.js rewrite proxies
that server-side to Render (`BACKEND_INTERNAL_URL`). So the JWT cookie is
first-party to the Vercel domain and nothing is cross-origin. No backend code
changes were needed for the move.

Do the steps in order — each produces a value the next step needs.

---

## 1. Neon — Postgres (5 min)

1. Sign up at <https://neon.tech> (GitHub login).
2. Create a project (any name, any region). It creates a database automatically.
3. Copy the **connection string** — looks like:
   `postgresql://<user>:<password>@<host>.neon.tech/<db>?sslmode=require`
4. Keep it for step 2 (`DATABASE_URL`).

Migrations run automatically on the backend's first boot (`start.sh` runs
`alembic upgrade head`), so you don't create tables by hand.

---

## 2. Render — backend (10 min)

1. Sign up at <https://render.com> (GitHub login) and connect the
   `neelakantaganesh23/SOWnia-agent` repo.
2. **New → Blueprint** → pick the repo. Render reads `render.yaml` and proposes
   a `sownia-backend` web service (free, Docker). Apply it.
3. In the service's **Environment** tab, set these (marked `sync:false`):

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the Neon string from step 1 |
   | `SECRET_KEY` | `openssl rand -hex 32` (any 32-byte hex) |
   | `GOOGLE_API_KEY` | your Gemini key |
   | `HF_TOKEN` | your Hugging Face token (if used) |
   | `FRONTEND_BASE_URL` | *(fill after step 3 — the Vercel URL)* |
   | `ALLOWED_ORIGINS` | *(same Vercel URL)* |
   | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` | *(only if enabling Google login — step 4)* |

4. Deploy. When it's live, copy the backend URL, e.g.
   `https://sownia-backend.onrender.com`. Keep it for step 3.

> ⚠️ Render free tier **sleeps after ~15 min idle** → first request after
> waking takes ~50s (cold start). Fine for a demo. Also 512 MB RAM: if the
> backend OOMs on heavy reviews, the fallback is **Hugging Face Spaces**
> (Docker SDK, 16 GB RAM free) — the app was originally designed for it.

---

## 3. Vercel — frontend (5 min)

1. Sign up at <https://vercel.com> (GitHub login) and import the same repo.
2. **Root Directory: `frontend`** (important — the Next.js app is in a subfolder).
3. Framework preset auto-detects **Next.js**. Leave build settings default.
4. **Environment Variables** → add:

   | Key | Value |
   |---|---|
   | `BACKEND_INTERNAL_URL` | the Render URL from step 2 (e.g. `https://sownia-backend.onrender.com`) |

   > Note: **no** `NEXT_PUBLIC_API_URL` — the browser must use relative `/api`.
   > `BACKEND_INTERNAL_URL` has no `NEXT_PUBLIC_` prefix so it stays server-only.

5. Deploy. Copy the Vercel URL, e.g. `https://sownia.vercel.app`.
6. **Go back to Render** and fill `FRONTEND_BASE_URL` and `ALLOWED_ORIGINS`
   with this Vercel URL, then redeploy the backend.

Open the Vercel URL → sign up / log in / upload / review. Done.

---

## 4. Google OAuth (optional — now works, thanks to the real HTTPS domain)

1. <https://console.cloud.google.com> → APIs & Services → Credentials →
   **Create OAuth client ID** → type **Web application**.
2. **Authorized redirect URI:**
   `https://<your-vercel-domain>/api/v1/auth/google/callback`
3. Copy the Client ID + Secret into Render env vars:
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` = the same redirect URI above
   Redeploy the backend. "Continue with Google" now works.

---

## Auto-deploy

Both platforms redeploy on every push to the connected branch — Vercel builds
the frontend, Render rebuilds the backend. No CI/CD to manage. (The old Azure
DevOps pipelines are archived under `azure-legacy/`.)

## Cost

Everything above is $0 on free tiers. Neon persists; Render/Vercel free web
apps stay up (Render just sleeps when idle). No VMs, no Azure bill.
