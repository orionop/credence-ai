"""
In-memory session store for the hackathon demo.
Tracks entity data, ingested documents, research results, and CAM state.
"""

import uuid
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class IngestedDoc:
    filename: str
    doc_type: str
    status: str  # "processing", "verified", "failed"
    timestamp: str
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    integrity_hash: str = ""


@dataclass
class Session:
    id: str
    # Entity profile
    entity_name: str = ""
    cin_gstin: str = ""
    sector: str = "Manufacturing & Heavy Industries"
    facility_type: str = "Term Loan"
    requested_loan_amount: str = ""
    # Ingested documents
    ingested_docs: List[IngestedDoc] = field(default_factory=list)
    # Aggregated financials from all ingested docs
    financials: Dict[str, Any] = field(default_factory=dict)
    # Rich GST data (full schema from Gemini extraction)
    rich_gst_data: Dict[str, Any] = field(default_factory=dict)
    # Research agent results
    research_insights: List[Dict[str, str]] = field(default_factory=list)
    # Primary/qualitative notes from the credit officer
    primary_notes: str = ""
    # Five Cs scoring
    five_cs_scores: Dict[str, Any] = field(default_factory=dict)
    # Generated CAM report (markdown)
    cam_report: str = ""
    # Overall credit metrics
    credit_score: int = 0
    credit_rating: str = ""
    recommendation: str = ""  # "approved", "conditional", "rejected"
    recommended_limit: str = ""
    probability_of_default: str = ""
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# --- In-Memory Store ---
_sessions: Dict[str, Session] = {}


def create_session(entity_name: str = "", **kwargs) -> Session:
    """Create a new session and return it."""
    session_id = str(uuid.uuid4())[:8]
    session = Session(id=session_id, entity_name=entity_name, **kwargs)
    _sessions[session_id] = session
    logger.info(f"Created session {session_id} for entity '{entity_name}'")
    return session


def get_session(session_id: str) -> Optional[Session]:
    """Retrieve a session by ID."""
    return _sessions.get(session_id)


def get_or_create_default_session() -> Session:
    """Get the first session or create a default one."""
    if _sessions:
        return next(iter(_sessions.values()))
    return create_session(entity_name="Demo Entity")


def update_session(session_id: str, **kwargs) -> Optional[Session]:
    """Update fields on a session."""
    session = _sessions.get(session_id)
    if not session:
        return None
    for key, value in kwargs.items():
        if hasattr(session, key):
            setattr(session, key, value)
    session.updated_at = datetime.now().isoformat()
    return session


def list_sessions() -> List[Session]:
    """List all sessions."""
    return list(_sessions.values())


def session_to_dict(session: Session) -> dict:
    """Convert session to a JSON-serializable dict."""
    return {
        "id": session.id,
        "entity_name": session.entity_name,
        "cin_gstin": session.cin_gstin,
        "sector": session.sector,
        "facility_type": session.facility_type,
        "requested_loan_amount": session.requested_loan_amount,
        "ingested_docs": [
            {
                "filename": d.filename,
                "doc_type": d.doc_type,
                "status": d.status,
                "timestamp": d.timestamp,
                "integrity_hash": d.integrity_hash,
            }
            for d in session.ingested_docs
        ],
        "financials": session.financials,
        "rich_gst_data": session.rich_gst_data,
        "research_insights": session.research_insights,
        "primary_notes": session.primary_notes,
        "five_cs_scores": session.five_cs_scores,
        "cam_report": session.cam_report,
        "credit_score": session.credit_score,
        "credit_rating": session.credit_rating,
        "recommendation": session.recommendation,
        "recommended_limit": session.recommended_limit,
        "probability_of_default": session.probability_of_default,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
