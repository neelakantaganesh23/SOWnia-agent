# SOWnia — Azure AKS Deployment Guide

Deploys SOWnia to **Azure Kubernetes Service (AKS)** via **Azure DevOps → Terraform → Docker/ACR → Helm**.

> **Why this guide exists:** The pipeline's Terraform stage was failing with **403** errors.
> That is a *permissions* problem, not a Terraform bug. The service principal behind the
> Azure DevOps service connection only has rights inside the resource group, so it cannot
> register resource providers or do subscription-level lookups. The one-time steps below —
> run by YOU as the subscription **Owner** — fix that at the root.

---

## 0. Prerequisites (once)

- Azure **free trial** subscription (you are the Owner).
- Azure DevOps organization + project.
- GitHub repo connected (or code pushed to Azure Repos).
- Azure CLI installed locally, or use the Azure Cloud Shell (portal → `>_` icon).

---

## 1. One-time Azure setup (run as the Owner)

Run these **once**, locally or in Cloud Shell. This is what makes the 403s disappear.

```bash
# --- Login and select the subscription ---
az login
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
SUB=$(az account show --query id -o tsv)

# --- (a) Register the resource providers ONCE (owner has the rights; the SP does not) ---
az provider register --namespace Microsoft.ContainerService --wait
az provider register --namespace Microsoft.ContainerRegistry --wait
az provider register --namespace Microsoft.Network --wait
az provider register --namespace Microsoft.Compute --wait
# Verify (should print "Registered" for each):
az provider show -n Microsoft.ContainerService --query registrationState -o tsv

# --- (b) Pre-create the resource group (Terraform references it, does not create it) ---
az group create --name rg-sownia-aks-prod --location eastus

# --- (b2) Create the remote Terraform STATE storage (once). This persists state
#          across pipeline runs so Terraform stops re-creating existing resources.
#          Storage account names are GLOBALLY unique + 3-24 lowercase alphanumeric.
#          If "stsowniatfstate01" is taken, pick another and update the backend
#          block in terraform/main.tf to match.
az storage account create \
  --name stsowniatfstate01 \
  --resource-group rg-sownia-aks-prod \
  --location eastus \
  --sku Standard_LRS \
  --min-tls-version TLS1_2
az storage container create \
  --name tfstate \
  --account-name stsowniatfstate01 \
  --auth-mode login

# --- (c) Create the service principal used by the Azure DevOps service connection,
#         scoped to the whole SUBSCRIPTION as Contributor (fixes the GroupsClient 403) ---
az ad sp create-for-rbac \
  --name "sp-sownia-devops" \
  --role Contributor \
  --scopes "/subscriptions/$SUB" \
  --sdk-auth
```

The last command prints a JSON credential block. **Copy it** — you need it in step 2.

> If your org policy forbids subscription-scope Contributor, scope it to the RG instead:
> `--scopes "/subscriptions/$SUB/resourceGroups/rg-sownia-aks-prod"`. The RG and providers
> are already pre-created in (a)/(b), so RG-scope is enough for the rest of the pipeline.

---

### 1d. Clear the orphaned resources from earlier runs (one-time)

Earlier pipeline runs already created the ACR and AKS, but their state was lost
(no backend then). Now that remote state exists but is empty, Terraform would say
`already exists - needs to be imported`. Simplest fix — **delete them** and let the
next pipeline run recreate them under tracked state:

```bash
az aks delete --name aks-sownia-prod --resource-group rg-sownia-aks-prod --yes
az acr delete --name acrsowniaaksprod --resource-group rg-sownia-aks-prod --yes
```

> **Alternative (keeps the existing cluster):** instead of deleting, import them into
> the new remote state by running Terraform locally with the ARM_* env vars set:
> `terraform init` then
> `terraform import azurerm_container_registry.sownia_acr /subscriptions/<SUB>/resourceGroups/rg-sownia-aks-prod/providers/Microsoft.ContainerRegistry/registries/acrsowniaaksprod`
> and the same for `azurerm_kubernetes_cluster.sownia_aks`. Delete is easier for a test.

---

## 2. Azure DevOps service connection

1. Azure DevOps → **Project Settings → Service connections → New → Azure Resource Manager**.
2. Choose **Service principal (manual)** and paste the values from the `--sdk-auth` JSON:
   - Subscription ID / Name, Tenant ID (`tenantId`), Client ID (`clientId`), Client secret (`clientSecret`).
3. Name it **exactly** `Azure-DevOps-Service-Connection` (this matches `azureSubscription` in `azure-pipelines.yml`).
4. **Verify** the connection.

---

## 3. Pipeline secrets

The Helm stage injects app secrets. Add these as **pipeline variables** (mark as secret 🔒):

Azure DevOps → **Pipelines → <your pipeline> → Edit → Variables**:

| Variable | Value | Secret |
|---|---|---|
| `GOOGLE_API_KEY` | your Gemini key | 🔒 |
| `HF_TOKEN` | your Hugging Face token | 🔒 |

(These map to `$(GOOGLE_API_KEY)` / `$(HF_TOKEN)` at the bottom of `azure-pipelines.yml`.)

---

## 4. Create & run the pipeline

1. Azure DevOps → **Pipelines → New pipeline** → point at the repo → **Existing YAML** → `/azure-pipelines.yml`.
2. **Run**. The three stages execute in order:
   - **1. Terraform** — creates ACR + AKS (Free tier, 1 node) in the pre-created RG.
   - **2. Build** — builds & pushes `sownia-backend` / `sownia-frontend` images to ACR.
   - **3. Deploy** — `helm upgrade --install` onto AKS.

---

## 5. Free-trial sizing (already applied)

To stay under the **4-vCPU free-trial quota** and conserve the $200 credit:

| Setting | Value | Where |
|---|---|---|
| AKS control plane | `Free` tier | `terraform/main.tf` |
| Node count | **1** × `Standard_B2s` (2 vCPU) | `terraform/variables.tf` |
| OS disk | 32 GB | `terraform/main.tf` |
| Backend / Frontend replicas | **1** each | `helm/sownia/values.yaml` |

> Even at 1 node, an AKS node + Standard Load Balancer + public IP + ACR Standard still
> draws on the credit. **Run `terraform destroy` (or delete the resource group) when you're
> done testing** to avoid burning the trial.

---

## 6. Access the app

```bash
az aks get-credentials --resource-group rg-sownia-aks-prod --name aks-sownia-prod --overwrite-existing
kubectl get pods            # all should be Running
kubectl get svc             # find EXTERNAL-IP of the frontend/ingress
```

The Helm chart defines an nginx **ingress** with a `sownia.yourdomain.com` host and
cert-manager TLS. For a quick free-trial test you don't need a domain — either:
- patch the frontend service to `type: LoadBalancer` and hit its external IP, or
- `kubectl port-forward svc/<frontend-svc> 3000:3000` and open `http://localhost:3000`.

---

## 7. Tear down (stop the credit burn)

```bash
cd terraform && terraform destroy -auto-approve
# or nuke everything:
az group delete --name rg-sownia-aks-prod --yes --no-wait
```

---

## Troubleshooting the 403s (recap)

| Symptom | Cause | Fix |
|---|---|---|
| `Registering ... 403` during `terraform apply` | SP can't register providers (needs subscription scope) | Step 1(a): owner pre-registers; `skip_provider_registration = true` already set |
| `GroupsClient ... 403` | SP can't do subscription-level RG lookup | RG is pre-created (1b) and referenced directly by `var.resource_group_name` |
| `AuthorizationFailed` on create | SP lacks Contributor on the target scope | Step 1(c): grant Contributor at subscription (or RG) scope |
| Node pool fails: quota exceeded | >4 vCPU on free trial | Already fixed: 1 × Standard_B2s |
