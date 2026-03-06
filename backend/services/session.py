"""
Persistent session store using SQLite or PostgreSQL for production-grade reliability.
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

# DB Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to older env var or default SQLite
    DATABASE_URL = os.environ.get("DATABASE_PATH", "storage/credence.db")

IS_POSTGRES = DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")

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
    # Nashee analytical module outputs
    gst_reconciliation: Dict[str, Any] = field(default_factory=dict)
    bank_intelligence: Dict[str, Any] = field(default_factory=dict)
    graph_analysis: Dict[str, Any] = field(default_factory=dict)
    stress_test_results: List[Dict[str, Any]] = field(default_factory=list)
    advanced_credit: Dict[str, Any] = field(default_factory=dict)
    qualitative_scores: Dict[str, Any] = field(default_factory=dict)
    local_risk_decision: Dict[str, Any] = field(default_factory=dict)
    z_score_anomalies: Dict[str, Any] = field(default_factory=dict)
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

def _get_db():
    if IS_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        # Fix for some providers that give postgres:// instead of postgresql://
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
        return conn
    else:
        os.makedirs(os.path.dirname(DATABASE_URL), exist_ok=True)
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn

def _get_placeholder():
    return "%s" if IS_POSTGRES else "?"

def init_db():
    conn = _get_db()
    cursor = conn.cursor()
    
    text_type = "TEXT" if not IS_POSTGRES else "TEXT" # Both use TEXT
    
    query = f"""
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
            gst_reconciliation TEXT,
            bank_intelligence TEXT,
            graph_analysis TEXT,
            stress_test_results TEXT,
            advanced_credit TEXT,
            qualitative_scores TEXT,
            local_risk_decision TEXT,
            z_score_anomalies TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """
    cursor.execute(query)

    # Migrations for existing DBs — add new columns if missing
    new_columns = [
        "gst_reconciliation", "bank_intelligence", "graph_analysis",
        "stress_test_results", "advanced_credit", "qualitative_scores",
        "local_risk_decision", "z_score_anomalies",
    ]
    for col in new_columns:
        try:
            cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col} TEXT")
        except Exception:
            pass  # Column already exists

    conn.commit()
    conn.close()
    logger.info(f"Initialized {'PostgreSQL' if IS_POSTGRES else 'SQLite'} database")

# Call init on module load
init_db()

def _safe_json_load(val, default=None):
    """Safely load JSON from a DB column, returning default on None/empty."""
    if default is None:
        default = {}
    if val is None or val == '':
        return default
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default

def _row_to_session(row) -> Session:
    # sqlite3.Row or psycopg2 RealDictCursor row behave like dicts
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
        gst_reconciliation=_safe_json_load(row.get('gst_reconciliation') if hasattr(row, 'get') else (row['gst_reconciliation'] if 'gst_reconciliation' in row.keys() else None)),
        bank_intelligence=_safe_json_load(row.get('bank_intelligence') if hasattr(row, 'get') else (row['bank_intelligence'] if 'bank_intelligence' in row.keys() else None)),
        graph_analysis=_safe_json_load(row.get('graph_analysis') if hasattr(row, 'get') else (row['graph_analysis'] if 'graph_analysis' in row.keys() else None)),
        stress_test_results=_safe_json_load(row.get('stress_test_results') if hasattr(row, 'get') else (row['stress_test_results'] if 'stress_test_results' in row.keys() else None), []),
        advanced_credit=_safe_json_load(row.get('advanced_credit') if hasattr(row, 'get') else (row['advanced_credit'] if 'advanced_credit' in row.keys() else None)),
        qualitative_scores=_safe_json_load(row.get('qualitative_scores') if hasattr(row, 'get') else (row['qualitative_scores'] if 'qualitative_scores' in row.keys() else None)),
        local_risk_decision=_safe_json_load(row.get('local_risk_decision') if hasattr(row, 'get') else (row['local_risk_decision'] if 'local_risk_decision' in row.keys() else None)),
        z_score_anomalies=_safe_json_load(row.get('z_score_anomalies') if hasattr(row, 'get') else (row['z_score_anomalies'] if 'z_score_anomalies' in row.keys() else None)),
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )

def create_session(entity_name: str = "", **kwargs) -> Session:
    session_id = str(uuid.uuid4())[:8]
    session = Session(id=session_id, entity_name=entity_name, **kwargs)
    
    p = _get_placeholder()
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO sessions (
            id, entity_name, cin_gstin, sector, facility_type, requested_loan_amount,
            ingested_docs, financials, rich_gst_data, research_insights,
            primary_notes, five_cs_scores, cam_report, credit_score,
            credit_rating, recommendation, recommended_limit,
            probability_of_default, gst_reconciliation, bank_intelligence,
            graph_analysis, stress_test_results, advanced_credit,
            qualitative_scores, local_risk_decision, z_score_anomalies,
            created_at, updated_at
        ) VALUES ({','.join([p]*28)})
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
        json.dumps(session.gst_reconciliation),
        json.dumps(session.bank_intelligence),
        json.dumps(session.graph_analysis),
        json.dumps(session.stress_test_results),
        json.dumps(session.advanced_credit),
        json.dumps(session.qualitative_scores),
        json.dumps(session.local_risk_decision),
        json.dumps(session.z_score_anomalies),
        session.created_at,
        session.updated_at
    ))
    conn.commit()
    conn.close()
    logger.info(f"Created persistent session {session_id}")
    return session

def get_session(session_id: str) -> Optional[Session]:
    p = _get_placeholder()
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM sessions WHERE id = {p}", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_session(row) if row else None

def get_or_create_default_session() -> Session:
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY created_at ASC LIMIT 1")
    row = cursor.fetchone()
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
    
    p = _get_placeholder()
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute(f"""
        UPDATE sessions SET
            entity_name = {p}, cin_gstin = {p}, sector = {p}, facility_type = {p},
            requested_loan_amount = {p}, ingested_docs = {p}, financials = {p},
            rich_gst_data = {p}, research_insights = {p}, primary_notes = {p},
            five_cs_scores = {p}, cam_report = {p}, credit_score = {p},
            credit_rating = {p}, recommendation = {p}, recommended_limit = {p},
            probability_of_default = {p}, gst_reconciliation = {p},
            bank_intelligence = {p}, graph_analysis = {p},
            stress_test_results = {p}, advanced_credit = {p},
            qualitative_scores = {p}, local_risk_decision = {p},
            z_score_anomalies = {p}, updated_at = {p}
        WHERE id = {p}
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
        json.dumps(session.gst_reconciliation),
        json.dumps(session.bank_intelligence),
        json.dumps(session.graph_analysis),
        json.dumps(session.stress_test_results),
        json.dumps(session.advanced_credit),
        json.dumps(session.qualitative_scores),
        json.dumps(session.local_risk_decision),
        json.dumps(session.z_score_anomalies),
        session.updated_at,
        session.id
    ))
    conn.commit()
    conn.close()
    return session

def list_sessions() -> List[Session]:
    conn = _get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
    rows = cursor.fetchall()
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
        "gst_reconciliation": session.gst_reconciliation,
        "bank_intelligence": session.bank_intelligence,
        "graph_analysis": session.graph_analysis,
        "stress_test_results": session.stress_test_results,
        "advanced_credit": session.advanced_credit,
        "qualitative_scores": session.qualitative_scores,
        "local_risk_decision": session.local_risk_decision,
        "z_score_anomalies": session.z_score_anomalies,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
