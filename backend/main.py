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
from services.session import (
    create_session, get_session, get_or_create_default_session,
    update_session, list_sessions, session_to_dict, IngestedDoc
)
from services.scoring import compute_five_cs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CredenceAI Backend",
    description="AI-powered Credit Decisioning Engine API",
    version="0.2.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
                    facility_type=request.facility_type
                )
                return {"status": "updated", "session": session_to_dict(session)}

        # Create new session
        session = create_session(
            entity_name=request.entity_name,
            cin_gstin=request.cin_gstin,
            sector=request.sector,
            facility_type=request.facility_type
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
        primary_notes=session.primary_notes
    )

    # Persist in session
    session.five_cs_scores = scores
    session.credit_score = scores.get("overall_score", 0)
    session.credit_rating = scores.get("credit_rating", "")
    session.recommendation = scores.get("recommendation", "")
    session.recommended_limit = scores.get("recommended_limit", "")
    session.probability_of_default = scores.get("probability_of_default", "")
    session.updated_at = datetime.now().isoformat()

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
        cam_report = generate_cam(
            request.company_name,
            request.parsed_financials,
            request.research_insights,
            request.primary_insights
        )

        # Update session if provided
        if request.session_id:
            session = get_session(request.session_id)
            if session:
                session.cam_report = cam_report
                session.updated_at = datetime.now().isoformat()

        return {
            "status": "success",
            "cam_report": cam_report,
            "session_id": request.session_id
        }

    except Exception as e:
        logger.error(f"CAM generation error for {request.company_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
