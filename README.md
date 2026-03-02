# CredenceAI

**AI-Powered Credit Appraisal Engine for Indian Corporate Lending**

CredenceAI automates the Credit Appraisal Memo (CAM) preparation pipeline — ingesting structured and unstructured financial documents, running autonomous research agents for market intelligence, and producing explainable credit recommendations using the Five Cs of Credit framework.

Built for the "Intelli-Credit" hackathon challenge: *Next-Gen Corporate Credit Appraisal — Bridging the Intelligence Gap*.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                  │
│  Dashboard │ Entity Ingestion │ Risk Intel │ Five Cs     │
│  Appraisal Memo │ GST Reconciliation Hub                 │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────┴──────────────────────────────────┐
│                  FastAPI Backend (Python)                 │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Ingestor   │  │ Research     │  │ Scoring Engine │  │
│  │  (PyMuPDF + │  │ Agent        │  │ (Five Cs +     │  │
│  │   GPT-3.5)  │  │ (Tavily API) │  │  Risk Tiers)   │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Session    │  │ CAM          │  │ PD → Score     │  │
│  │  Manager    │  │ Generator    │  │ Converter      │  │
│  │  (In-Memory)│  │ (GPT-4)     │  │ (Logit → 900)  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## API Documentation

Base URL: `http://localhost:8080`

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check — returns service status and version |
| `POST` | `/api/v1/entity` | Create entity profile and initialize a new appraisal session |
| `GET` | `/api/v1/session/{id}` | Retrieve full session state by ID |
| `GET` | `/api/v1/sessions` | List all active sessions |
| `POST` | `/api/v1/ingest` | Upload and parse financial documents (PDF/CSV) |
| `POST` | `/api/v1/research` | Trigger the autonomous research agent for market/legal intelligence |
| `POST` | `/api/v1/primary-insights` | Save credit officer field notes and due diligence observations |
| `GET` | `/api/v1/five-cs/{id}` | Compute Five Cs credit scores with AI-generated explanations |
| `POST` | `/api/v1/generate-cam` | Generate the full Credit Appraisal Memo (Markdown) |

### Request/Response Examples

#### Create Entity
```bash
curl -X POST http://localhost:8080/api/v1/entity \
  -H 'Content-Type: application/json' \
  -d '{
    "entity_name": "Acme Corp India Pvt Ltd",
    "cin_gstin": "U12345MH2024PTC123456",
    "sector": "Manufacturing & Heavy Industries",
    "facility_type": "Term Loan"
  }'
```

#### Ingest Document
```bash
curl -X POST http://localhost:8080/api/v1/ingest \
  -F "file=@financial_statement.pdf" \
  -F "session_id=abc123"
```

#### Run Research Agent
```bash
curl -X POST http://localhost:8080/api/v1/research \
  -H 'Content-Type: application/json' \
  -d '{"session_id": "abc123", "company_name": "Acme Corp", "industry": "Manufacturing"}'
```

#### Compute Five Cs
```bash
curl http://localhost:8080/api/v1/five-cs/abc123
```

---

## Algorithm Documentation

### 1. Document Ingestion Pipeline

**Input**: PDF/CSV financial filings (GST returns, ITRs, bank statements, annual reports)

**Process**:
1. **Text Extraction** — PyMuPDF extracts raw text from uploaded PDFs
2. **LLM Parsing** — GPT-3.5 structures the raw text into typed JSON: revenue figures, EBITDA, debt ratios, flags, and key financial indicators
3. **Session Enrichment** — Parsed financials are merged into the active session state

**Output**: Structured `financials` object with numeric fields and risk flags

---

### 2. Autonomous Research Agent

**Input**: Entity name and industry sector

**Process**:
1. **Query Construction** — Builds targeted search queries for: litigation risk, sector headwinds, regulatory changes, promoter track record, and MCA filings
2. **Web Intelligence** — Tavily API performs real-time web search and returns summarized results
3. **Result Structuring** — Raw search results are parsed into titled insight cards with source attribution, timestamps, and sentiment tags

**Output**: Array of `ResearchInsight` objects (title, content, source, sentiment, timestamp)

---

### 3. Five Cs Scoring Engine

A hybrid AI + deterministic scoring system that evaluates corporate creditworthiness.

#### Stage 1: AI-Powered Five Cs Evaluation (GPT-3.5)

The LLM evaluates the entity across five dimensions using all available data:

| Dimension | Key Metrics Assessed |
|-----------|---------------------|
| **Character** | Promoter track record, governance quality, litigation history |
| **Capacity** | DSCR, interest coverage ratio, EBITDA margin, cash flow trends |
| **Capital** | Debt-to-equity ratio, net worth, capital adequacy |
| **Collateral** | Security coverage, asset quality, collateral marketability |
| **Conditions** | Sector outlook, regulatory environment, macro headwinds |

Each dimension receives a **score (0-100)**, summary, detailed explanation, and key driving factors.

#### Stage 2: Deterministic Risk Framework

The AI-estimated Probability of Default (PD) feeds into a rule-based tier assignment:

| PD Range | Rating | Recommendation | Risk Premium |
|----------|--------|----------------|--------------|
| 0-2% | AAA | Approved | 0.75% |
| 2-5% | AA+ | Approved | 1.25% |
| 5-8% | AA | Approved | 1.75% |
| 8-12% | A+ | Approved | 2.25% |
| 12-18% | A | Conditional | 2.75% |
| 18-25% | BBB+ | Conditional | 3.50% |
| 25-35% | BBB | Conditional | 4.50% |
| 35-50% | BB | Rejected | 6.00% |
| 50-100% | B/CCC | Rejected | 8.00% |

#### PD → Commercial Score Conversion

```
score = 300 + 600 × clip((−log(PD / (1−PD)) + 6) / 12, 0, 1)
```

Maps PD to a **300-900 CIBIL-like commercial score** via logit transform.

#### Sanction Limit Calculation

```
recommended_limit = requested_amount × sanction_pct[rating]
```

Where `sanction_pct` ranges from 100% (AAA) to 0% (BB and below).

---

### 4. CAM Generator

**Input**: Structured financials + research insights + field notes + Five Cs scores

**Process**: GPT-4 synthesizes all data into a professional Credit Appraisal Memo following Indian banking standards, structured by the Five Cs framework.

**Output**: Markdown-formatted CAM with executive summary, Five Cs analysis, risk assessment, and final underwriting recommendation.

---

## Quick Start

```bash
# Backend
cd backend
cp .env.example .env  # Add your API keys
pip install -r requirements.txt
uvicorn main:app --port 8080 --reload

# Frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.9+, Uvicorn |
| AI/LLM | OpenAI GPT-3.5/4, LangChain |
| Research | Tavily API (web intelligence) |
| Document Parsing | PyMuPDF, Pandas |

---

## License

MIT — see [LICENSE](LICENSE)

## Author

**Anurag Shetye** — [@orionop](https://github.com/orionop)
