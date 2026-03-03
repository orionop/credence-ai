"""
Persistent session store using SQLite for production-grade reliability.
Tracks entity data, ingested documents, research results, and CAM state.
"""

import uuid
import logging
import sqlite3
import json
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# DB Location - should be in a persistent volume for Railway/Render
DB_PATH = os.environ.get("DATABASE_PATH", "storage/credence.db")

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

def _get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            entity_name TEXT,
            cin_gstin TEXT,
            sector TEXT,
            facility_type TEXT,
            requested_loan_amount TEXT,
            ingested_docs TEXT,
            financials TEXT,
            rich_gst_data TEXT,
            research_insights TEXT,
            primary_notes TEXT,
            five_cs_scores TEXT,
            cam_report TEXT,
            credit_score INTEGER,
            credit_rating TEXT,
            recommendation TEXT,
            recommended_limit TEXT,
            probability_of_default TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Initialized SQLite database at {DB_PATH}")

# Call init on module load
init_db()

def _row_to_session(row) -> Session:
    return Session(
        id=row['id'],
        entity_name=row['entity_name'],
        cin_gstin=row['cin_gstin'],
        sector=row['sector'],
        facility_type=row['facility_type'],
        requested_loan_amount=row['requested_loan_amount'],
        ingested_docs=[IngestedDoc(**d) for d in json.loads(row['ingested_docs'])],
        financials=json.loads(row['financials']),
        rich_gst_data=json.loads(row['rich_gst_data']),
        research_insights=json.loads(row['research_insights']),
        primary_notes=row['primary_notes'],
        five_cs_scores=json.loads(row['five_cs_scores']),
        cam_report=row['cam_report'],
        credit_score=row['credit_score'],
        credit_rating=row['credit_rating'],
        recommendation=row['recommendation'],
        recommended_limit=row['recommended_limit'],
        probability_of_default=row['probability_of_default'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )

def create_session(entity_name: str = "", **kwargs) -> Session:
    session_id = str(uuid.uuid4())[:8]
    session = Session(id=session_id, entity_name=entity_name, **kwargs)
    
    conn = _get_db()
    conn.execute("""
        INSERT INTO sessions (
            id, entity_name, cin_gstin, sector, facility_type, requested_loan_amount,
            ingested_docs, financials, rich_gst_data, research_insights,
            primary_notes, five_cs_scores, cam_report, credit_score,
            credit_rating, recommendation, recommended_limit,
            probability_of_default, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session.id, session.entity_name, session.cin_gstin, session.sector,
        session.facility_type, session.requested_loan_amount,
        json.dumps([vars(d) for d in session.ingested_docs]),
        json.dumps(session.financials),
        json.dumps(session.rich_gst_data),
        json.dumps(session.research_insights),
        session.primary_notes,
        json.dumps(session.five_cs_scores),
        session.cam_report,
        session.credit_score,
        session.credit_rating,
        session.recommendation,
        session.recommended_limit,
        session.probability_of_default,
        session.created_at,
        session.updated_at
    ))
    conn.commit()
    conn.close()
    logger.info(f"Created persistent session {session_id}")
    return session

def get_session(session_id: str) -> Optional[Session]:
    conn = _get_db()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return _row_to_session(row) if row else None

def get_or_create_default_session() -> Session:
    conn = _get_db()
    row = conn.execute("SELECT * FROM sessions ORDER BY created_at ASC LIMIT 1").fetchone()
    conn.close()
    if row:
        return _row_to_session(row)
    return create_session(entity_name="Demo Entity")

def update_session(session_id: str, **kwargs) -> Optional[Session]:
    session = get_session(session_id)
    if not session:
        return None
    
    for key, value in kwargs.items():
        if hasattr(session, key):
            setattr(session, key, value)
    
    session.updated_at = datetime.now().isoformat()
    
    conn = _get_db()
    conn.execute("""
        UPDATE sessions SET
            entity_name = ?, cin_gstin = ?, sector = ?, facility_type = ?,
            requested_loan_amount = ?, ingested_docs = ?, financials = ?,
            rich_gst_data = ?, research_insights = ?, primary_notes = ?,
            five_cs_scores = ?, cam_report = ?, credit_score = ?,
            credit_rating = ?, recommendation = ?, recommended_limit = ?,
            probability_of_default = ?, updated_at = ?
        WHERE id = ?
    """, (
        session.entity_name, session.cin_gstin, session.sector,
        session.facility_type, session.requested_loan_amount,
        json.dumps([vars(d) for d in session.ingested_docs]),
        json.dumps(session.financials),
        json.dumps(session.rich_gst_data),
        json.dumps(session.research_insights),
        session.primary_notes,
        json.dumps(session.five_cs_scores),
        session.cam_report,
        session.credit_score,
        session.credit_rating,
        session.recommendation,
        session.recommended_limit,
        session.probability_of_default,
        session.updated_at,
        session.id
    ))
    conn.commit()
    conn.close()
    return session

def list_sessions() -> List[Session]:
    conn = _get_db()
    rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [_row_to_session(row) for row in rows]

def session_to_dict(session: Session) -> dict:
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

