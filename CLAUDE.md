# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CredenceAI is an AI-powered corporate credit appraisal engine for institutional banking in India. It automates Credit Appraisal Memo (CAM) preparation by ingesting financial documents, running research agents, and computing credit scores using the Five Cs of Credit framework (Character, Capacity, Capital, Collateral, Conditions).

## Build & Run Commands

### Backend (FastAPI + Python 3.9+)
```bash
cd backend
cp .env.example .env   # Configure API keys
pip install -r requirements.txt
uvicorn main:app --port 8080 --reload
```

### Frontend (React 19 + Vite + TypeScript)
```bash
cd frontend
npm install
npm run dev       # Dev server on http://localhost:5173
npm run build     # Production build
npm run preview   # Preview production build
```

### Tests
```bash
cd backend
pytest test_scoring.py        # Risk tier & sanction limit tests
pytest test_persistence.py    # SQLite session tests
pytest test_scoring.py -k "test_name"  # Run single test
```

### Environment Variables (backend/.env)
Required: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `GOOGLE_API_KEY`
Optional: `ANTHROPIC_API_KEY` (for Claude scoring), `DATABASE_PATH` (default: `storage/credence.db`), `ALLOWED_ORIGINS` (CORS, default: `*`)

### Deployment
- Backend: Railway (`railway.toml`) — `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Frontend: Vercel (`vercel.json`)

## Architecture

**Two-service architecture**: FastAPI backend (port 8080) + React SPA frontend (port 5173).

### Backend Services (`backend/services/`)

| Service | File | Role |
|---------|------|------|
| Session | `session.py` | SQLite persistence layer. Sessions identified by 8-char UUID prefixes. |
| Ingestor | `ingestor.py` | Document parsing pipeline: PyMuPDF text extraction → doc type detection → LLM extraction (Gemini 1.5 Flash primary, GPT-3.5 fallback) → local math validation |
| Scoring | `scoring.py` | Two-stage scoring: (1) AI evaluation via Claude Opus 4.6 or GPT-4 for Five Cs scores, (2) deterministic risk tier assignment with PD→score logit transform (300-900 scale) |
| Research Agent | `agent.py` | Tavily API web intelligence — litigation, sector risks, regulatory changes |
| CAM Generator | `cam_generator.py` | GPT-4-turbo synthesizes full Credit Appraisal Memo in Indian banking format |
| Anomaly Detector | `anomaly_detector.py` | Isolation Forest ML model for fraud detection on GST/bank statement data |

### API Endpoints (`backend/main.py`)

All under `/api/v1/`: `POST /entity` (create session), `GET /session/{id}`, `GET /sessions`, `POST /ingest` (upload docs), `POST /research`, `POST /primary-insights`, `GET /five-cs/{id}` (compute scores), `POST /generate-cam`.

### Frontend (`frontend/src/`)

- **AppContext.tsx** — React Context for global state (session, documents, scores, CAM). All state mutations via useCallback actions.
- **App.tsx** — Main shell with sidebar navigation and view routing (~1600 lines).
- **api.ts** — Typed API client with error handling for all backend endpoints.
- **Views**: `EntityIngestionView.tsx` (entity + doc upload), `RiskIntelligenceView.tsx` (research insights), `FiveCsAnalysisView.tsx` (radar chart + scores).

## Key Patterns

- **LLM fallback chains**: Gemini → GPT-3.5 for parsing; Claude Opus 4.6 → GPT-4 for scoring. Always handle provider failures gracefully.
- **Local math validation**: Critical financial calculations (GST ratios, behavioral risk metrics, anomaly detection) are computed locally, not delegated to LLMs.
- **Structured LLM output**: All LLM responses are parsed as JSON and validated. Extraction prompts specify exact output schemas.
- **Persistence-first**: All state persisted in SQLite (`storage/credence.db`), schema auto-created on module load. No in-memory-only state.
- **Document types supported**: GST returns, CIBIL reports, bank statements, annual reports, ITR filings. Format: PDF, CSV, JSON, XLSX.
- **Risk framework**: 9 tiers (AAA to B/CCC), each mapping to PD ranges, sanction percentages, and recovery ratings.
