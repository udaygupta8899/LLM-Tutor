# Deploying DL Tutor RAG to Azure

## Prerequisites

1. **Azure CLI** installed → [Install guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Docker** installed and running
3. An **Azure account** with an active subscription

---

## Step 1 — Login to Azure

```bash
az login
```

This opens a browser for authentication. Once done, set your subscription:

```bash
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
```

---

## Step 2 — Create a Resource Group

```bash
az group create --name dl-tutor-rg --location centralindia
```

> [!TIP]
> Use `az account list-locations -o table` to find a region closer to you. `centralindia` is used here since you're in IST.

---

## Step 3 — Create an Azure Container Registry (ACR)

```bash
az acr create --resource-group dl-tutor-rg --name dltutoracr --sku Basic --admin-enabled true
```

> [!NOTE]
> The registry name (`dltutoracr`) must be globally unique and alphanumeric only. Change it if it's taken.

Get the login credentials:

```bash
az acr credential show --name dltutoracr
```

Login to ACR from Docker:

```bash
az acr login --name dltutoracr
```

---

## Step 4 — Build & Tag the Docker Image

From your project root (`/home/uday/DL/dl-tutor-rag`):

```bash
# Build the image
docker build -t dl-tutor-rag .

# Tag it for ACR
docker tag dl-tutor-rag dltutoracr.azurecr.io/dl-tutor-rag:latest
```

### Test locally first (optional but recommended)

```bash
docker run -p 8000:8000 --env-file .env dl-tutor-rag
```

Visit `http://localhost:8000/health` to verify it works.

---

## Step 5 — Push to ACR

```bash
docker push dltutoracr.azurecr.io/dl-tutor-rag:latest
```

Verify the image is in your registry:

```bash
az acr repository list --name dltutoracr --output table
```

---

## Step 6 — Deploy to Azure Container Apps

### 6a. Install the Container Apps extension (if not already installed)

```bash
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights
```

### 6b. Create a Container Apps Environment

```bash
az containerapp env create \
  --name dl-tutor-env \
  --resource-group dl-tutor-rg \
  --location centralindia
```

### 6c. Deploy the Container App

```bash
az containerapp create \
  --name dl-tutor-api \
  --resource-group dl-tutor-rg \
  --environment dl-tutor-env \
  --image dltutoracr.azurecr.io/dl-tutor-rag:latest \
  --registry-server dltutoracr.azurecr.io \
  --registry-username dltutoracr \
  --registry-password "<ACR_PASSWORD_FROM_STEP_3>" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars "OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>"
```

> [!CAUTION]
> Don't commit your API key to git. Use the `--env-vars` flag above or configure secrets (see below).

### Using Secrets (recommended over plain env vars)

```bash
# Create a secret
az containerapp secret set \
  --name dl-tutor-api \
  --resource-group dl-tutor-rg \
  --secrets openai-key="<YOUR_OPENAI_API_KEY>"

# Reference the secret in env vars
az containerapp update \
  --name dl-tutor-api \
  --resource-group dl-tutor-rg \
  --set-env-vars "OPENAI_API_KEY=secretref:openai-key"
```

---

## Step 7 — Get Your App URL

```bash
az containerapp show \
  --name dl-tutor-api \
  --resource-group dl-tutor-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

This gives you something like: `dl-tutor-api.<random>.centralindia.azurecontainerapps.io`

Test it:

```bash
curl https://dl-tutor-api.<random>.centralindia.azurecontainerapps.io/health
```

---

## Step 8 — Update Your Frontend CORS

Add your new Azure URL to the `ALLOWED_ORIGINS` list in [main.py](file:///home/uday/DL/dl-tutor-rag/main.py#L17-L21):

```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://dl-tutor.novaric.in",
    "https://heroic-cobbler-7548b3.netlify.app",
    "https://dl-tutor-api.<random>.centralindia.azurecontainerapps.io",  # Azure
]
```

---

## Quick Reference — Redeployment

When you make code changes and want to redeploy:

```bash
# Rebuild & push
docker build -t dl-tutor-rag .
docker tag dl-tutor-rag dltutoracr.azurecr.io/dl-tutor-rag:latest
docker push dltutoracr.azurecr.io/dl-tutor-rag:latest

# Update the container app to pull the new image
az containerapp update \
  --name dl-tutor-api \
  --resource-group dl-tutor-rg \
  --image dltutoracr.azurecr.io/dl-tutor-rag:latest
```

---

## Important Notes

> [!WARNING]
> Your `.dockerignore` excludes `.env` — this is correct! Never bake secrets into the image. Always pass `OPENAI_API_KEY` via Azure Container App environment variables or secrets.

> [!IMPORTANT]
> The Chroma DB is ephemeral inside the container. Every time the container restarts, it will re-download the PDF and rebuild the vector store. For production, consider:
> - Mounting an **Azure Files** volume for persistent Chroma DB storage
> - Or switching to a managed vector DB (e.g., Azure AI Search, Pinecone)

| Resource | What it does | Azure Cost |
|----------|-------------|------------|
| Resource Group | Logical container for all resources | Free |
| Container Registry (Basic) | Stores your Docker image | ~$5/month |
| Container Apps | Runs your container | Pay-per-use (can scale to 0) |
