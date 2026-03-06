# CredenceAI

**AI-Powered Credit Decisioning Engine for Indian Corporate Lending**

CredenceAI automates the end-to-end Credit Appraisal Memo (CAM) pipeline — ingesting multi-format financial documents, running autonomous research agents for market and legal intelligence, performing deep analytical scoring with ML models, and producing explainable credit recommendations using the Five Cs of Credit framework.

Built for the **"Intelli-Credit" Hackathon Challenge**: *Next-Gen Corporate Credit Appraisal — Bridging the Intelligence Gap*.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite + Tailwind)               │
│  Dashboard │ Entity Ingestion │ Risk Intelligence │ Five Cs      │
│  Appraisal Memo │ GST Reconciliation │ Graph Analysis           │
└──────────────────────────┬───────────────────────────────────────┘
                           │ REST API (v1)
┌──────────────────────────┴───────────────────────────────────────┐
│                     FastAPI Backend (Python)                      │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Document AI      │  │ Research Agent   │  │ Scoring Engine │ │
│  │  Gemini 1.5 Flash │  │ Tavily + MCA    │  │ Five Cs + PD   │ │
│  │  + Table          │  │ + e-Courts      │  │ Risk Tiers     │ │
│  │    Transformer    │  │   Simulation    │  │                │ │
│  │  + EasyOCR        │  │                 │  │                │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Graph Analysis   │  │ CAM Generator   │  │ Anomaly        │ │
│  │ NetworkX + GNN   │  │ GPT-4 Turbo    │  │ Detector       │ │
│  │ (GraphSAGE)      │  │                 │  │ Isolation      │ │
│  │                   │  │                 │  │ Forest +       │ │
│  │                   │  │                 │  │ Z-Score        │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ GST              │  │ Bank            │  │ Stress Test    │ │
│  │ Reconciliation   │  │ Intelligence    │  │ Engine         │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Advanced Credit  │  │ Qualitative     │  │ Local Risk     │ │
│  │ (CIBIL Scoring)  │  │ Inputs          │  │ Policy Engine  │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                   │
│                     SQLite Persistence Layer                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Core Capabilities

### Pillar 1: The Data Ingestor (Multi-Format Document AI)

| Document Type | Extraction Method | Key Outputs |
|---|---|---|
| **GST Returns** (GSTR-1/2A/3B) | Gemini 1.5 Flash | Turnover, ITC variance, cash tax ratios, circular trading flags |
| **CIBIL Commercial Reports** | Gemini 1.5 Flash | CCR Rank, DPD history, suit filed status, wilful default flags |
| **Bank Statements** | Gemini + Table Transformer | Cash flows, transaction patterns, opening/closing balances |
| **Annual Reports** | Table Transformer + EasyOCR | Revenue growth, EBITDA, debt-to-equity, auditor flags |
| **ITR Filings** | Gemini 1.5 Flash | Income breakdowns, tax compliance status |
| **Sanction Letters** | Gemini 1.5 Flash | Existing debt, interest rates, tenure, guarantee types |

**Advanced Document AI**: For table-heavy PDFs (Annual Reports, Bank Statements, ITRs), the system uses Microsoft's **Table Transformer** for table detection and **EasyOCR** for layout-preserving text extraction, with automatic fallback to PyMuPDF.

**Behavioral Risk Math**: Post-extraction, the system computes deterministic risk indicators locally (ITC utilization ratio, cash-to-ITC ratio, mismatch flags) to avoid LLM math hallucinations. An **Isolation Forest** anomaly detector flags statistical outliers in GST-vs-Bank cross-reconciliation.

---

### Pillar 2: The Research Agent (Digital Credit Manager)

| Source | Method | Output |
|---|---|---|
| **Web News** | Tavily API (live search) | Sector headwinds, promoter news, litigation alerts |
| **MCA Registry** | Simulated fetch | CIN, incorporation date, compliance status, director count, paid-up capital |
| **e-Courts Portal** | Simulated fetch | NCLT insolvency petitions, commercial suit recovery cases |
| **Primary Insights** | Credit Officer UI input | Qualitative field notes integrated into risk scoring |

---

### Pillar 3: The Recommendation Engine

#### Five Cs Scoring (Hybrid AI + Deterministic)

The LLM evaluates the entity across five dimensions:

| Dimension | Key Metrics |
|---|---|
| **Character** | Promoter track record, governance, litigation history |
| **Capacity** | DSCR, interest coverage, EBITDA margin, cash flows |
| **Capital** | Debt-to-equity, net worth, capital adequacy |
| **Collateral** | Security coverage, asset quality, marketability |
| **Conditions** | Sector outlook, regulatory environment, macro headwinds |

#### Risk Tier Assignment

| PD Range | Rating | Recommendation | Risk Premium |
|---|---|---|---|
| 0–2% | AAA | Approved | 0.75% |
| 2–5% | AA+ | Approved | 1.25% |
| 5–8% | AA | Approved | 1.75% |
| 8–12% | A+ | Approved | 2.25% |
| 12–18% | A | Conditional | 2.75% |
| 18–25% | BBB+ | Conditional | 3.50% |
| 25–35% | BBB | Conditional | 4.50% |
| 35–50% | BB | Rejected | 6.00% |
| 50–100% | B/CCC | Rejected | 8.00% |

#### CAM Generation (GPT-4 Turbo)

Produces a professional Credit Appraisal Memo following Indian banking standards — structured by the Five Cs, with executive summary, risk assessment, sanction amount recommendation, risk-adjusted pricing (MCLR + spread), and covenants.

---

## Advanced Analytical Modules

| Module | Technology | Purpose |
|---|---|---|
| **GST Reconciliation** | Deterministic math | GSTR-2A vs 3B variance, ITC dependency ratios, supplier concentration |
| **Bank Intelligence** | Heuristic analysis | Cash flow patterns, related party detection, velocity analysis |
| **Transaction Graph** | NetworkX + GraphSAGE (PyTorch Geometric) | Entity relationship mapping, cycle detection, GNN-based anomaly scoring |
| **Stress Testing** | Scenario engine | Revenue/EBITDA shock scenarios (10%, 20%, 30% decline) with DSCR impact |
| **Advanced Credit** | CIBIL proxy scoring | Weighted composite from repayment history, utilization, account age |
| **Qualitative Scoring** | Weighted rubric | Management quality, governance, industry position |
| **Local Risk Policy** | JSON-configurable `risk_policy.json` | Policy-driven rule engine with threshold-based overrides |
| **Z-Score Anomaly Detection** | Statistical analysis | Flags outliers across financial metrics using z-score thresholds |

---

## API Reference

Base URL: `http://localhost:8000`

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/api/v1/entity` | Create entity profile and initialize session |
| `GET` | `/api/v1/session/{id}` | Retrieve full session state |
| `GET` | `/api/v1/sessions` | List all sessions |
| `POST` | `/api/v1/ingest` | Upload and parse documents (PDF/CSV) |
| `POST` | `/api/v1/research` | Run autonomous research agent |
| `POST` | `/api/v1/primary-insights` | Save credit officer field notes |
| `GET` | `/api/v1/five-cs/{id}` | Compute Five Cs credit scores |
| `POST` | `/api/v1/generate-cam` | Generate Credit Appraisal Memo |
| `GET` | `/api/v1/gst-reconciliation/{id}` | GST variance analysis |
| `GET` | `/api/v1/bank-intelligence/{id}` | Bank flow intelligence |
| `GET` | `/api/v1/graph-analysis/{id}` | Transaction graph + GNN scoring |
| `GET` | `/api/v1/stress-test/{id}` | Stress test scenarios |
| `GET` | `/api/v1/advanced-credit/{id}` | CIBIL proxy credit scoring |
| `GET` | `/api/v1/qualitative-scoring/{id}` | Management quality assessment |
| `GET` | `/api/v1/local-risk-decision/{id}` | Policy-driven risk decision |

---

## Quick Start

```bash
# Backend
cd backend
cp .env.example .env   # Add: GOOGLE_API_KEY, OPENAI_API_KEY, TAVILY_API_KEY
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload

# Frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini 1.5 Flash (primary document parser) |
| `OPENAI_API_KEY` | Yes | GPT-4 Turbo (CAM generation), GPT-3.5 (scoring fallback) |
| `TAVILY_API_KEY` | Recommended | Live web search for research agent |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS |
| **Backend** | FastAPI, Python 3.9+, Uvicorn, SQLite |
| **Document AI** | Google Gemini 1.5 Flash, Microsoft Table Transformer, EasyOCR, PyMuPDF |
| **CAM Generation** | OpenAI GPT-4 Turbo, LangChain |
| **Research** | Tavily API, MCA simulation, e-Courts simulation |
| **ML Models** | PyTorch, PyTorch Geometric (GraphSAGE), scikit-learn (Isolation Forest) |
| **Graph Analysis** | NetworkX, Matplotlib |

---

## Project Structure

```
credence-ai/
├── backend/
│   ├── main.py                     # FastAPI app + all API endpoints
│   ├── services/
│   │   ├── ingestor.py             # Document AI pipeline (Gemini + Table Transformer)
│   │   ├── agent.py                # Research agent (Tavily + MCA + e-Courts)
│   │   ├── scoring.py              # Five Cs + PD scoring engine
│   │   ├── cam_generator.py        # GPT-4 CAM generation
│   │   ├── session.py              # SQLite persistence layer
│   │   ├── anomaly_detector.py     # Isolation Forest + Z-score detection
│   │   ├── graph_analysis.py       # NetworkX graph + GNN integration
│   │   ├── gnn_model.py            # PyTorch Geometric GraphSAGE
│   │   ├── gst_reconciliation.py   # GST variance analysis
│   │   ├── bank_intelligence.py    # Bank flow analysis
│   │   ├── stress_test.py          # Revenue/EBITDA stress scenarios
│   │   ├── advanced_credit.py      # CIBIL proxy scoring
│   │   ├── qualitative_inputs.py   # Management quality scoring
│   │   └── document_ai/
│   │       └── layout_parser.py    # Table Transformer + EasyOCR
│   └── data/
│       └── risk_policy.json        # Configurable risk policy thresholds
├── frontend/
│   └── src/
│       ├── App.tsx                  # Main app shell with all views
│       ├── AppContext.tsx           # Global state management
│       ├── api.ts                  # Backend API client
│       ├── RiskIntelligenceView.tsx # Graph + research visualization
│       ├── FiveCsAnalysisView.tsx   # Radar chart + score breakdown
│       └── EntityIngestionView.tsx  # Document upload interface
└── reference/
    ├── intelli-credit-engine/       # Original upstream prototype source
    └── anomaly-models/              # Pre-trained Isolation Forest model
```

---

## License

MIT — see [LICENSE](LICENSE)

## Authors

**Yash Patil** · **Anurag Shetye** — Team Godspeed
