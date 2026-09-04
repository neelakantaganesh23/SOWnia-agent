# Azure deployment (archived)

These files deployed SOWnia to **Azure Kubernetes Service (AKS)** via Terraform,
Helm, and Azure DevOps pipelines. They are kept for reference/history.

**The project has migrated to a free hosting stack** — see
[`../FREE_STACK_DEPLOYMENT.md`](../FREE_STACK_DEPLOYMENT.md):

- Frontend → Vercel
- Backend → Render
- Postgres → Neon

The Azure stack was retired because AKS runs on billed VMs (recurring cost),
while the free stack costs nothing. Nothing here is wired into the current
deploy; it will not run unless you re-adopt Azure.
