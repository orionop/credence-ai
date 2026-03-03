/**
 * CredenceAI API Client
 * All backend communication goes through these typed helpers.
 */

const API_BASE = "http://localhost:8080/api/v1"

// ── Types ─────────────────────────────────────────────────────────────────

export interface IngestedDoc {
    filename: string
    doc_type: string
    status: string
    timestamp: string
    integrity_hash: string
}

export interface ResearchInsight {
    id: string
    title: string
    content: string
    source: string
    timestamp: string
    sentiment: string
}

export interface FiveCsScore {
    score: number
    summary: string
    detail: string
}

export interface FiveCsResult {
    character: FiveCsScore
    capacity: FiveCsScore
    capital: FiveCsScore
    collateral: FiveCsScore
    conditions: FiveCsScore
    overall_score: number
    credit_rating: string
    probability_of_default: string
    loss_given_default: string
    recovery_rating: string
    recommendation: string
    recommended_limit: string
    risk_premium: string
    appraisal_summary: string
}

export interface SessionData {
    id: string
    entity_name: string
    cin_gstin: string
    sector: string
    facility_type: string
    requested_loan_amount: string
    ingested_docs: IngestedDoc[]
    financials: Record<string, any>
    rich_gst_data: Record<string, any>
    research_insights: ResearchInsight[]
    primary_notes: string
    five_cs_scores: FiveCsResult | Record<string, never>
    cam_report: string
    credit_score: number
    credit_rating: string
    recommendation: string
    recommended_limit: string
    probability_of_default: string
    created_at: string
    updated_at: string
}

export interface ExtractedData {
    metadata: { doc_type: string; pages: number }
    financials: Record<string, string>
    flags: string[]
}


// ── API Functions ─────────────────────────────────────────────────────────

/** Save or update entity profile */
export async function saveEntity(
    entityName: string,
    cinGstin: string,
    sector: string,
    facilityType: string,
    requestedLoanAmount: string,
    sessionId?: string
): Promise<{ status: string; session: SessionData }> {
    const res = await fetch(`${API_BASE}/entity`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            entity_name: entityName,
            cin_gstin: cinGstin,
            sector: sector,
            facility_type: facilityType,
            requested_loan_amount: requestedLoanAmount,
            session_id: sessionId,
        }),
    })
    if (!res.ok) throw new Error(`Entity save failed: ${res.statusText}`)
    return res.json()
}


/** Upload and ingest a document */
export async function ingestDocument(
    file: File,
    sessionId?: string
): Promise<{ status: string; filename: string; extracted_data: ExtractedData; session_id: string }> {
    const formData = new FormData()
    formData.append("file", file)
    if (sessionId) formData.append("session_id", sessionId)

    const res = await fetch(`${API_BASE}/ingest?session_id=${sessionId || ""}`, {
        method: "POST",
        body: formData,
    })
    if (!res.ok) throw new Error(`Ingest failed: ${res.statusText}`)
    return res.json()
}


/** Trigger research agent */
export async function researchEntity(
    companyName: string,
    industry?: string,
    sessionId?: string
): Promise<{ status: string; company: string; insights: ResearchInsight[]; session_id: string }> {
    const res = await fetch(`${API_BASE}/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            company_name: companyName,
            industry: industry,
            session_id: sessionId,
        }),
    })
    if (!res.ok) throw new Error(`Research failed: ${res.statusText}`)
    return res.json()
}


/** Save primary insights / qualitative notes */
export async function savePrimaryInsights(
    sessionId: string,
    notes: string
): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/primary-insights`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, notes }),
    })
    if (!res.ok) throw new Error(`Primary insights save failed: ${res.statusText}`)
    return res.json()
}


/** Get Five Cs scores */
export async function getFiveCsScores(
    sessionId: string
): Promise<{ status: string; session_id: string; scores: FiveCsResult }> {
    const res = await fetch(`${API_BASE}/five-cs/${sessionId}`)
    if (!res.ok) throw new Error(`Five Cs scoring failed: ${res.statusText}`)
    return res.json()
}


/** Generate Credit Appraisal Memo */
export async function generateCAM(
    companyName: string,
    financials: Record<string, any>,
    insights: string[],
    primaryInsights: string,
    sessionId?: string
): Promise<{ status: string; cam_report: string; session_id: string }> {
    const res = await fetch(`${API_BASE}/generate-cam`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            company_name: companyName,
            parsed_financials: financials,
            research_insights: insights,
            primary_insights: primaryInsights,
            session_id: sessionId,
        }),
    })
    if (!res.ok) throw new Error(`CAM generation failed: ${res.statusText}`)
    return res.json()
}


/** Get session data */
export async function getSession(
    sessionId: string
): Promise<{ status: string; session: SessionData }> {
    const res = await fetch(`${API_BASE}/session/${sessionId}`)
    if (!res.ok) throw new Error(`Session fetch failed: ${res.statusText}`)
    return res.json()
}


/** List all sessions */
export async function listSessions(): Promise<{ status: string; sessions: SessionData[] }> {
    const res = await fetch(`${API_BASE}/sessions`)
    if (!res.ok) throw new Error(`Sessions list failed: ${res.statusText}`)
    return res.json()
}
