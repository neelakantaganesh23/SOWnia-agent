# SOWnia — Project Documentation

**Last updated:** August 2026
**Status:** Auth + Postgres + Vivid UI redesign complete and verified on `dev`; pending merge to `main` (prod)

---

## 1. What is SOWnia?

SOWnia is an AI-powered, multi-agent Statement of Work (SOW) review system. Users upload a PDF/DOCX SOW document; five specialized AI agents (Legal, Financial, Technical, Risk, Delivery) analyze it in parallel via a LangGraph orchestrator and produce structured findings, risk scores, and downloadable reports.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Next.js Frontend (Vivid UI)               │
│   Login/Signup → Upload → Review Results → Dashboard      │
└──────────────────────┬──────────────────────────────────┘
                       │ same-origin, proxied via next.config.js
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                          │
│  Auth (JWT cookie, email/password + Google OAuth)         │
│  ┌─────────────────────────────────────────────────┐     │
│  │            LangGraph Orchestrator                 │    │
│  │   Legal │ Financial │ Technical │ Risk │ Delivery  │    │
│  │              ↓ parallel execution ↓                │    │
│  │                  Synthesizer                       │    │
│  └─────────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  In-cluster      │
              │  Postgres        │  ← users, uploaded_files, reviews
              │  (per namespace) │     (all rows scoped by user_id)
              └──────────────────┘
```

All three components (frontend, backend, Postgres) run as pods inside a single **Azure Kubernetes Service (AKS)** cluster.

---

## 3. Infrastructure (Azure)

| Resource | Purpose |
|---|---|
| **AKS cluster** (`aks-sownia-prod`) | Runs all workloads. 2 nodes, `Standard_D2as_v7` (2 vCPU each = 4 vCPU total, the free-trial ceiling). Free control-plane tier. |
| **Azure Container Registry** (`acrsowniaaksprod`) | Stores `sownia-backend` / `sownia-frontend` Docker images. |
| **Azure Load Balancer** (via AKS) | Public IP for each environment's frontend `LoadBalancer` Service. |
| **Azure Storage Account** (`stsowniatfstate01`) | Holds Terraform's remote state (persists across pipeline runs). |
| ~~Azure Database for PostgreSQL~~ | **Not used** — this free-trial subscription has zero Flexible Server capacity in every region tried. Postgres runs in-cluster instead (see §6). |

Provisioned via **Terraform** (`terraform/`), applied only by the prod pipeline.

---

## 4. Environments

Two fully isolated environments share the one AKS cluster, separated by Kubernetes **namespace**:

| | Prod | Dev |
|---|---|---|
| Git branch | `main` | `develop` |
| Pipeline | `azure-pipelines.yml` | `azure-pipelines-dev.yml` |
| K8s namespace | `default` | `dev` |
| Helm release | `sownia` | `sownia-dev` |
| Frontend URL | `http://4.157.55.31:3000` *(pre-auth app; not yet updated)* | `http://48.195.200.241:3000` *(current, tested)* |
| Postgres | own in-cluster pod | own in-cluster pod |
| Google OAuth | works (once domain configured) | **not supported** — bare IP fails Google's redirect-URI validation; email/password only |

Workflow: build/test on `develop` → verify on dev URL → merge `develop` → `main` → prod pipeline auto-deploys.

---

## 5. CI/CD

Two independent Azure DevOps pipelines, both auto-triggered on push:

- **Prod** (`main`): Terraform apply → Docker build/push → Helm deploy. Only this pipeline touches cloud infrastructure.
- **Dev** (`develop`): Docker build/push → Helm deploy (no Terraform stage — dev never touches infra, only app code).

Required pipeline secrets: `GOOGLE_API_KEY`, `HF_TOKEN`, `JWT_SECRET_KEY` (both pipelines); `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` (prod only, for OAuth).

---

## 6. Authentication & Multi-tenancy (new)

Previously the app had **no authentication at all** — every API endpoint was open, and all uploads/reviews were visible to every caller (stored in per-process memory + a single shared file on Hugging Face Datasets).

**Now:**
- **Email/password** signup and login (bcrypt-hashed passwords).
- **Google OAuth** (authorization-code flow), prod-only (needs a real HTTPS domain).
- Session is a JWT in an **httpOnly cookie** — Next.js `middleware.ts` gates protected routes by cookie presence; the backend validates the signature per-request.
- **Postgres** replaces the in-memory dicts and shared HF file: `users`, `uploaded_files`, `reviews` tables, all foreign-keyed to `user_id`. Every route now requires auth and filters by the current user — **one user can no longer see another user's documents or reviews.**
- **Postgres runs in-cluster** (a `postgres:16` StatefulSet per namespace) rather than as an Azure managed database, because Azure Database for PostgreSQL Flexible Server has no capacity on this subscription in any region tested. This required zero backend code changes — it's still real Postgres, just self-hosted inside the cluster.
- DB schema is managed by **Alembic**; migrations run automatically via an init container on every backend rollout.

---

## 7. UI Redesign — "Vivid"

The frontend was restyled from a purple/glassmorphic look to the **Vivid** design system from the project's design-handoff spec:

- **Palette**: dark background (`#0a0a11`), signature gradient (blue → purple → pink → orange), risk colors (HIGH `#FB4E6D`, MEDIUM `#FBBF24`, LOW `#34D399`).
- **Typography**: Plus Jakarta Sans (headings) + Inter (body), via `next/font`.
- **Glass cards**: translucent fill + hairline border + heavy blur, matching the handoff spec exactly.
- **Icons**: all emoji/inline-SVG replaced with `lucide-react` components.
- Applied to all existing pages/components (Upload, Dashboard, Review Results) plus two new pages (Login, Signup) — restyled in place rather than rebuilt from scratch, so some prototype-only flourishes (animated onboarding loader, hero illustration card) aren't present.

---

## 8. Key fixes made along the way

A running list of real issues hit and resolved during this build (useful troubleshooting history):

- Terraform 403s → free-trial service principal needed provider pre-registration + role grants (owner-only actions).
- AKS node SKU restrictions → `Standard_B2s` not allowed; moved to `Standard_D2as_v7`.
- No Terraform remote state → added Azure Storage backend so state persists across pipeline runs.
- OIDC issuer / node-pool rotation → provider-required config additions.
- Backend `ModuleNotFoundError` → Docker image layout mismatch with `backend.*` imports.
- Frontend "Network Error" on upload → browser was calling a build-time-baked wrong host instead of the same-origin proxy.
- Disk-pressure pod evictions → backend image bloat (unused `sentence-transformers`/`faiss-cpu` pulling in torch+CUDA, ~3GB) + too-small node disk; removed unused deps and bumped disk/node count.
- Dev signup 500s → (a) dev's backend Service name didn't match the frontend's build-time-baked proxy target — fixed by giving the backend Service a constant name across namespaces; (b) `passlib`/`bcrypt` version incompatibility — pinned `bcrypt==4.0.1`.

---

## 9. Cost management

AKS can be stopped without losing any configuration or data:
```bash
az aks stop  --name aks-sownia-prod --resource-group rg-sownia-aks-prod   # pause
az aks start --name aks-sownia-prod --resource-group rg-sownia-aks-prod   # resume
```
This deallocates the VM nodes (the dominant cost) while keeping disks, images, and IPs — a few minutes to resume, no redeploy needed.

---

## 10. Open items / next steps

1. **Merge `develop` → `main`** to bring auth + Postgres + Vivid UI to prod (currently prod still runs the old, pre-auth app).
2. **Google OAuth for prod**: register a Google Cloud Console OAuth client with a real HTTPS domain (bare IPs aren't accepted); wire `GOOGLE_CLIENT_ID`/`SECRET` into the prod pipeline.
3. Optional: tighten the Postgres firewall/security posture now that it's in-cluster (currently ClusterIP-only, not exposed — already reasonably locked down).
4. Optional: further close the visual gap with the original Vivid prototype (animated loaders, hero illustration) if desired.

---

## 11. Repo reference

| Path | Purpose |
|---|---|
| `terraform/` | AKS + ACR infra (prod pipeline only) |
| `helm/sownia/` | Helm chart — `values.yaml` (prod), `values-dev.yaml` (dev overrides), `templates/` |
| `azure-pipelines.yml` | Prod CI/CD (main branch) |
| `azure-pipelines-dev.yml` | Dev CI/CD (develop branch) |
| `backend/` | FastAPI app — `auth/`, `models/`, `alembic/`, `api/routes/` |
| `frontend/` | Next.js 14 app — `app/`, `components/`, `store/`, `lib/` |
| `DEPLOYMENT.md` | Detailed Azure setup/troubleshooting notes |
