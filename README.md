# SOWnia — AI-Powered Multi-Agent SOW Review System

[![CI](https://github.com/neelakantaganesh23/sownia/actions/workflows/ci.yml/badge.svg)](https://github.com/neelakantaganesh23/sownia/actions/workflows/ci.yml)
[![Deploy](https://github.com/neelakantaganesh23/sownia/actions/workflows/deploy.yml/badge.svg)](https://github.com/neelakantaganesh23/sownia/actions/workflows/deploy.yml)

> **Speed + Accuracy + Traceability** — Replace multi-expert, multi-day SOW review cycles with an automated, AI-powered pipeline completed in minutes.

## 🧠 What is SOWnia?

SOWnia is an AI-powered, multi-agent Statement of Work (SOW) review system. It uses five specialized AI agents across legal, financial, technical, risk, and delivery domains, coordinated by a LangGraph orchestrator.

### Key Features

- **5 Specialized Agents**: Legal, Financial, Technical, Risk, and Delivery review agents
- **Parallel Execution**: All agents run concurrently via LangGraph's Send API
- **Multi-Format Support**: PDF and DOCX document parsing
- **Structured Output**: JSON findings with risk levels, confidence scores, and page references
- **PDF Reports**: Professional WeasyPrint-generated reports
- **Dashboard**: Historical review tracking and risk analytics
- **PII Protection**: Automatic PII redaction before sending to external models

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│         Upload → Review Results → Dashboard              │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │            LangGraph Orchestrator                │    │
│  │  ┌────────┬────────┬────────┬────────┬───────┐  │    │
│  │  │ Legal  │Finance │  Tech  │  Risk  │Delivery│  │    │
│  │  │(Gemini)│(Gemini)│(Mixtral│(LLaMA) │(Gemini)│  │    │
│  │  │ Flash  │ Flash  │ 8x7B) │  3-8B) │ Flash  │  │    │
│  │  └────────┴────────┴────────┴────────┴───────┘  │    │
│  │          ↓ Parallel Execution ↓                  │    │
│  │              Synthesizer                         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### 1. Clone and Setup

```bash
git clone https://github.com/neelakantaganesh23/sownia.git
cd sownia
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Docker (Alternative)

```bash
docker-compose up --build
```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI Pro API key (Gemini) | ✅ |
| `HF_TOKEN` | Hugging Face token | ✅ |
| `LANGCHAIN_API_KEY` | LangSmith API key | Optional |
| `HF_DATASET_REPO` | HF dataset repo for storage | ✅ |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend | ✅ |

See [.env.example](.env.example) for the full list.

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload PDF/DOCX file |
| POST | `/api/v1/review` | Start multi-agent review |
| GET | `/api/v1/results/{review_id}` | Get review results (JSON) |
| GET | `/api/v1/results/{review_id}/pdf` | Download PDF report |
| GET | `/api/v1/reviews` | List all past reviews |
| DELETE | `/api/v1/reviews/{review_id}` | Delete a review |
| GET | `/health` | Health check |

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Lint
ruff check backend/
black --check backend/
mypy backend/ --ignore-missing-imports
```

## 🚢 Deployment Options

### Option A: Azure Container Apps & ACR (Recommended Production Deployment)

SOWnia is packaged as production Docker containers for deployment on **Azure Container Apps (ACA)** with **Azure Container Registry (ACR)**.

1. **Local Multi-Container Test**:
   ```bash
   docker-compose -f docker-compose.prod.yml up --build
   ```

2. **Azure Deployment Workflow**:
   - Push code to GitHub repository.
   - Configure GitHub Secrets: `AZURE_CREDENTIALS`, `AZURE_ACR_NAME`, `AZURE_RESOURCE_GROUP`.
   - GitHub Actions workflow `.github/workflows/azure-deploy.yml` builds and deploys updated backend and frontend containers automatically.

### Option B: Local Docker Setup

```bash
docker-compose up --build
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
