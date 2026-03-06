from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import hashlib
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from services.ingestor import process_document
from services.agent import research_entity
from services.cam_generator import generate_cam
import os
from services.session import (
    create_session, get_session, get_or_create_default_session,
    update_session, list_sessions, session_to_dict, IngestedDoc
)
from services.scoring import compute_five_cs, compute_local_risk_decision
from services.gst_reconciliation import run_gst_reconciliation
from services.bank_intelligence import run_bank_intelligence
from services.graph_analysis import build_graph_from_session
from services.stress_test import run_stress_tests
from services.advanced_credit import analyze_cibil_from_extracted, analyze_related_party
from services.qualitative_inputs import score_qualitative_notes
from services.anomaly_detector import compute_gst_z_score_anomalies, compute_bank_z_score_anomalies

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CredenceAI Backend",
    description="AI-powered Credit Decisioning Engine API",
    version="0.2.0"
)

# CORS setup
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ──────────────────────────────────────────────────────────

class EntityRequest(BaseModel):
    entity_name: str
    cin_gstin: Optional[str] = ""
    sector: Optional[str] = "Manufacturing & Heavy Industries"
    facility_type: Optional[str] = "Term Loan"
    requested_loan_amount: Optional[str] = ""
    session_id: Optional[str] = None  # If updating existing session

class EntityResearchRequest(BaseModel):
    company_name: str
    industry: Optional[str] = None
    session_id: Optional[str] = None

class PrimaryInsightsRequest(BaseModel):
    session_id: str
    notes: str

class CAMGenerationRequest(BaseModel):
    company_name: str
    parsed_financials: Dict[str, Any]
    research_insights: List[str]
    primary_insights: Optional[str] = ""
    session_id: Optional[str] = None


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "ok", "service": "CredenceAI API", "version": "0.2.0"}


# ── Entity & Session Management ─────────────────────────────────────────────

@app.post("/api/v1/entity")
async def save_entity(request: EntityRequest):
    """Create or update an entity profile and its associated session."""
    try:
        if request.session_id:
            session = get_session(request.session_id)
            if session:
                update_session(
                    request.session_id,
                    entity_name=request.entity_name,
                    cin_gstin=request.cin_gstin,
                    sector=request.sector,
                    facility_type=request.facility_type,
                    requested_loan_amount=request.requested_loan_amount
                )
                return {"status": "updated", "session": session_to_dict(session)}

        # Create new session
        session = create_session(
            entity_name=request.entity_name,
            cin_gstin=request.cin_gstin,
            sector=request.sector,
            facility_type=request.facility_type,
            requested_loan_amount=request.requested_loan_amount
        )
        return {"status": "created", "session": session_to_dict(session)}

    except Exception as e:
        logger.error(f"Error saving entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/session/{session_id}")
async def get_session_data(session_id: str):
    """Get full session state."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "session": session_to_dict(session)}


@app.get("/api/v1/sessions")
async def list_all_sessions():
    """List all active sessions."""
    sessions = list_sessions()
    return {
        "status": "success",
        "sessions": [session_to_dict(s) for s in sessions]
    }


# ── Data Ingestion ───────────────────────────────────────────────────────────

@app.post("/api/v1/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    Ingest a corporate document (Annual Report, GST filing, Bank Statement)
    and extract structured financial data. Optionally attach to a session.
    """
    try:
        if not file.filename.endswith(('.pdf', '.csv', '.json', '.xlsx')):
            raise HTTPException(
                status_code=400,
                detail="Supported formats: PDF, CSV, JSON, XLSX"
            )

        content = await file.read()
        content_hash = hashlib.md5(content).hexdigest()[:8]

        # Extract structured data via LLM
        extracted_data = process_document(file.filename, content)

        # If session exists, attach the doc and update financials
        if session_id:
            session = get_session(session_id)
            if session:
                doc = IngestedDoc(
                    filename=file.filename,
                    doc_type=extracted_data.get("metadata", {}).get("doc_type", "Unknown"),
                    status="verified",
                    timestamp=datetime.now().strftime("%b %d, %Y • %H:%M:%S"),
                    extracted_data=extracted_data,
                    integrity_hash=f"{content_hash}...{content_hash[-4:]}"
                )
                session.ingested_docs.append(doc)

                # Merge financials
                if "financials" in extracted_data:
                    session.financials.update(extracted_data["financials"])
                if "flags" in extracted_data:
                    session.financials.setdefault("flags", []).extend(extracted_data["flags"])

                # Store rich GST data if this is a GST document
                if extracted_data.get("_doc_type") == "GST":
                    session.rich_gst_data = {
                        k: v for k, v in extracted_data.items()
                        if k in ('company_financials', 'gst_behavioral_cash_metrics',
                                 'document_risks', 'gst_risk_features')
                    }

                session.updated_at = datetime.now().isoformat()

        return {
            "status": "success",
            "filename": file.filename,
            "extracted_data": extracted_data,
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Research Agent ───────────────────────────────────────────────────────────

@app.post("/api/v1/research")
async def trigger_research(request: EntityResearchRequest):
    """
    Trigger the research agent to find secondary insights
    (management quality, sector headwinds, legal notices).
    """
    try:
        raw_insights = research_entity(request.company_name, request.industry)

        # Structure insights for the frontend
        structured_insights = []
        for i, insight in enumerate(raw_insights):
            structured_insights.append({
                "id": f"insight-{i}",
                "title": insight[:80] + "..." if len(insight) > 80 else insight,
                "content": insight,
                "source": "Tavily Web Search",
                "timestamp": datetime.now().strftime("%b %d, %Y • %H:%M"),
                "sentiment": "neutral"
            })

        # Update session if provided
        if request.session_id:
            session = get_session(request.session_id)
            if session:
                session.research_insights = structured_insights
                session.updated_at = datetime.now().isoformat()

        return {
            "status": "success",
            "company": request.company_name,
            "insights": structured_insights,
            "session_id": request.session_id
        }

    except Exception as e:
        logger.error(f"Research error for {request.company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Primary Insights ─────────────────────────────────────────────────────────

@app.post("/api/v1/primary-insights")
async def save_primary_insights(request: PrimaryInsightsRequest):
    """Save qualitative notes from credit officer (factory visits, interviews)."""
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.primary_notes = request.notes
    session.updated_at = datetime.now().isoformat()

    return {
        "status": "success",
        "session_id": request.session_id,
        "notes_saved": True
    }


# ── Analytical Modules (Phase 2 & 3 Integration) ─────────────────────────────

@app.get("/api/v1/gst-reconciliation/{session_id}")
async def get_gst_reconciliation(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Just run off rich_gst_data and financials
    rich_gst = session.rich_gst_data or {}
    financials = session.financials or {}
    gst_result = run_gst_reconciliation(rich_gst, financials)
    z_scores = compute_gst_z_score_anomalies(None) # Placeholders without actual time-series Pandas DF
    
    result = {**gst_result, **z_scores}
    update_session(session.id, gst_reconciliation=result)
    
    return {"status": "success", "session_id": session_id, "gst_reconciliation": result}

@app.get("/api/v1/bank-intelligence/{session_id}")
async def get_bank_intelligence(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    bank_result = run_bank_intelligence(session.financials or {}, session.ingested_docs)
    z_scores = compute_bank_z_score_anomalies(None) # Placeholders
    
    result = {**bank_result, **z_scores}
    update_session(session.id, bank_intelligence=result)
    
    return {"status": "success", "session_id": session_id, "bank_intelligence": result}

@app.get("/api/v1/graph-analysis/{session_id}")
async def get_graph_analysis(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = build_graph_from_session(
        session.entity_name or "Entity",
        session.rich_gst_data or {}, 
        session.bank_intelligence or {}, 
        session.financials or {}
    )
    update_session(session.id, graph_analysis=result)
    
    return {"status": "success", "session_id": session_id, "graph_analysis": result}

@app.get("/api/v1/stress-test/{session_id}")
async def get_stress_test(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    base_decision = session.local_risk_decision or {}
    
    try:
        clean_amt = "".join(filter(str.isdigit, str(session.requested_loan_amount)))
        req_limit = float(clean_amt) if clean_amt else 10000000.0
    except ValueError:
        req_limit = 10000000.0

    result = run_stress_tests(
        session.financials, 
        session.rich_gst_data or {}, 
        session.sector or "", 
        req_limit, 
        base_decision
    )
    update_session(session.id, stress_test_results=result)
    
    return {"status": "success", "session_id": session_id, "stress_test_results": result}

@app.get("/api/v1/advanced-credit/{session_id}")
async def get_advanced_credit(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Extract from all docs for cibil
    all_extracted = [d.extracted_data for d in session.ingested_docs if d.doc_type == "CIBIL"]
    cibil_data = all_extracted[0] if all_extracted else {}
    
    cibil_res = analyze_cibil_from_extracted(cibil_data)
    rp_res = analyze_related_party(session.bank_intelligence or {}, session.financials)
    
    result = {**cibil_res, **rp_res}
    update_session(session.id, advanced_credit=result)
    
    return {"status": "success", "session_id": session_id, "advanced_credit": result}

@app.get("/api/v1/qualitative-scoring/{session_id}")
async def get_qualitative_scoring(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    result = score_qualitative_notes(session.primary_notes)
    update_session(session.id, qualitative_scores=result)
    
    return {"status": "success", "session_id": session_id, "qualitative_scores": result}
    
@app.get("/api/v1/local-risk-decision/{session_id}")
async def get_local_risk_decision(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    result = compute_local_risk_decision(
        session.financials, 
        session.rich_gst_data or {}, 
        session.sector or "", 
        session.requested_loan_amount or "",
        session.gst_reconciliation,
        session.bank_intelligence,
        session.graph_analysis,
        session.advanced_credit,
        session.qualitative_scores,
        session.z_score_anomalies
    )
    update_session(session.id, local_risk_decision=result)
    
    return {"status": "success", "session_id": session_id, "local_risk_decision": result}


# ── Five Cs Scoring ──────────────────────────────────────────────────────────

@app.get("/api/v1/five-cs/{session_id}")
async def get_five_cs_scores(session_id: str):
    """Compute Five Cs scores from all available session data."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Compute scores using the scoring engine
    scores = compute_five_cs(
        financials=session.financials,
        research_insights=session.research_insights,
        primary_notes=session.primary_notes,
        loan_amount=session.requested_loan_amount,
        sector=session.sector,
        rich_gst_data=session.rich_gst_data
    )

    # Persist in session
    update_session(
        session.id,
        five_cs_scores=scores,
        credit_score=scores.get("overall_score", 0),
        credit_rating=scores.get("credit_rating", ""),
        recommendation=scores.get("recommendation", ""),
        recommended_limit=scores.get("recommended_limit", ""),
        probability_of_default=scores.get("probability_of_default", "")
    )

    return {
        "status": "success",
        "session_id": session_id,
        "scores": scores
    }


# ── CAM Generator ────────────────────────────────────────────────────────────

@app.post("/api/v1/generate-cam")
async def create_cam(request: CAMGenerationRequest):
    """
    Synthesize structured financials and unstructured agent research into
    the final Credit Appraisal Memo (CAM).
    """
    try:
        loan_amount = "Not Specified"
        sector = "Unknown"
        rich_gst_data = None
        
        # Priority: Pull richer context from session if ID exists
        if request.session_id:
            session = get_session(request.session_id)
            if session:
                loan_amount = session.requested_loan_amount or loan_amount
                sector = session.sector or sector
                rich_gst_data = session.rich_gst_data

        cam_report = generate_cam(
            company_name=request.company_name,
            financials=request.parsed_financials,
            insights=request.research_insights,
            primary_insights=request.primary_insights,
            loan_amount=loan_amount,
            sector=sector,
            rich_gst_data=rich_gst_data
        )

        # Update session if provided
        if request.session_id:
            session = get_session(request.session_id)
            if session:
                update_session(session.id, cam_report=cam_report)

        return {
            "status": "success",
            "cam_report": cam_report,
            "session_id": request.session_id
        }

    except Exception as e:
        logger.error(f"CAM generation error for {request.company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
