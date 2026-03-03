/**
 * Global Application Context
 * Manages session state, loading states, and actions across all views.
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import type { SessionData, ResearchInsight, FiveCsResult, ExtractedData } from './api'
import * as api from './api'

// ── Context Shape ───────────────────────────────────────────────────────────

interface AppState {
    // Session
    sessionId: string | null
    entityName: string
    cinGstin: string
    sector: string
    facilityType: string
    requestedLoanAmount: string

    // Ingested documents
    ingestedDocs: api.IngestedDoc[]
    financials: Record<string, any>
    latestExtraction: ExtractedData | null
    richGstData: Record<string, any>

    // Research
    researchInsights: ResearchInsight[]

    // Primary notes
    primaryNotes: string

    // Five Cs
    fiveCsScores: FiveCsResult | null

    // CAM
    camReport: string

    // Credit decision
    creditScore: number
    creditRating: string
    recommendation: string
    recommendedLimit: string
    probabilityOfDefault: string

    // UI state
    isLoading: Record<string, boolean>
    errors: Record<string, string>
    toastMessage: string | null
}

interface AppActions {
    // Entity
    saveEntity: (name: string, cin: string, sector: string, facility: string, loanAmount: string) => Promise<void>

    // Ingest
    ingestDocument: (file: File) => Promise<ExtractedData | null>

    // Research
    triggerResearch: (companyName?: string, industry?: string) => Promise<void>

    // Primary insights
    savePrimaryInsights: (notes: string) => Promise<void>

    // Five Cs
    computeFiveCs: () => Promise<void>

    // CAM
    generateCAM: () => Promise<void>

    // Utilities
    clearError: (key: string) => void
    clearToast: () => void
    loadSession: (sessionId: string) => Promise<void>
}

type AppContextType = AppState & AppActions

const AppContext = createContext<AppContextType | null>(null)


// ── Provider ────────────────────────────────────────────────────────────────

export function AppProvider({ children }: { children: ReactNode }) {
    // State
    const [sessionId, setSessionId] = useState<string | null>(null)
    const [entityName, setEntityName] = useState('')
    const [cinGstin, setCinGstin] = useState('')
    const [sector, setSector] = useState('Manufacturing & Heavy Industries')
    const [facilityType, setFacilityType] = useState('Term Loan')
    const [requestedLoanAmount, setRequestedLoanAmount] = useState('')
    const [ingestedDocs, setIngestedDocs] = useState<api.IngestedDoc[]>([])
    const [financials, setFinancials] = useState<Record<string, any>>({})
    const [latestExtraction, setLatestExtraction] = useState<ExtractedData | null>(null)
    const [richGstData, setRichGstData] = useState<Record<string, any>>({})
    const [researchInsights, setResearchInsights] = useState<ResearchInsight[]>([])
    const [primaryNotes, setPrimaryNotes] = useState('')
    const [fiveCsScores, setFiveCsScores] = useState<FiveCsResult | null>(null)
    const [camReport, setCamReport] = useState('')
    const [creditScore, setCreditScore] = useState(0)
    const [creditRating, setCreditRating] = useState('')
    const [recommendation, setRecommendation] = useState('')
    const [recommendedLimit, setRecommendedLimit] = useState('')
    const [probabilityOfDefault, setProbabilityOfDefault] = useState('')
    const [isLoading, setIsLoading] = useState<Record<string, boolean>>({})
    const [errors, setErrors] = useState<Record<string, string>>({})
    const [toastMessage, setToastMessage] = useState<string | null>(null)

    // Helpers
    const setLoadingFor = (key: string, val: boolean) =>
        setIsLoading(prev => ({ ...prev, [key]: val }))
    const setErrorFor = (key: string, msg: string) =>
        setErrors(prev => ({ ...prev, [key]: msg }))
    const clearError = useCallback((key: string) =>
        setErrors(prev => { const n = { ...prev }; delete n[key]; return n }), [])
    const clearToast = useCallback(() => setToastMessage(null), [])
    const toast = (msg: string) => {
        setToastMessage(msg)
        setTimeout(() => setToastMessage(null), 4000)
    }

    // Hydrate state from a session response
    const hydrateFromSession = (s: SessionData) => {
        setSessionId(s.id)
        setEntityName(s.entity_name)
        setCinGstin(s.cin_gstin)
        setSector(s.sector)
        setFacilityType(s.facility_type)
        setRequestedLoanAmount(s.requested_loan_amount || '')
        setIngestedDocs(s.ingested_docs)
        setFinancials(s.financials)
        if (s.rich_gst_data && Object.keys(s.rich_gst_data).length > 0) {
            setRichGstData(s.rich_gst_data)
        }
        setResearchInsights(s.research_insights)
        setPrimaryNotes(s.primary_notes)
        if (s.five_cs_scores && 'overall_score' in s.five_cs_scores) {
            setFiveCsScores(s.five_cs_scores as FiveCsResult)
        }
        setCamReport(s.cam_report)
        setCreditScore(s.credit_score)
        setCreditRating(s.credit_rating)
        setRecommendation(s.recommendation)
        setRecommendedLimit(s.recommended_limit)
        setProbabilityOfDefault(s.probability_of_default)
    }

    // ── Actions ─────────────────────────────────────────────────────────────

    const saveEntity = useCallback(async (name: string, cin: string, sec: string, fac: string, loanAmt: string) => {
        setLoadingFor('entity', true)
        try {
            const res = await api.saveEntity(name, cin, sec, fac, loanAmt, sessionId || undefined)
            hydrateFromSession(res.session)
            toast(`Entity "${name}" saved — session ${res.session.id}`)
        } catch (e: any) {
            setErrorFor('entity', e.message)
        } finally {
            setLoadingFor('entity', false)
        }
    }, [sessionId])

    const ingestDocumentAction = useCallback(async (file: File): Promise<ExtractedData | null> => {
        setLoadingFor('ingest', true)
        try {
            const res = await api.ingestDocument(file, sessionId || undefined)
            setLatestExtraction(res.extracted_data)
            // Refresh docs from session
            if (sessionId) {
                const sessionRes = await api.getSession(sessionId)
                hydrateFromSession(sessionRes.session)
            }
            toast(`"${file.name}" ingested successfully`)
            return res.extracted_data
        } catch (e: any) {
            setErrorFor('ingest', e.message)
            return null
        } finally {
            setLoadingFor('ingest', false)
        }
    }, [sessionId])

    const triggerResearch = useCallback(async (companyName?: string, industry?: string) => {
        setLoadingFor('research', true)
        try {
            const name = companyName || entityName || 'Demo Company'
            const res = await api.researchEntity(name, industry || sector, sessionId || undefined)
            setResearchInsights(res.insights)
            toast(`Research complete — ${res.insights.length} insights found`)
        } catch (e: any) {
            setErrorFor('research', e.message)
        } finally {
            setLoadingFor('research', false)
        }
    }, [sessionId, entityName, sector])

    const savePrimaryInsightsAction = useCallback(async (notes: string) => {
        if (!sessionId) { setErrorFor('primary', 'No active session'); return }
        setLoadingFor('primary', true)
        try {
            await api.savePrimaryInsights(sessionId, notes)
            setPrimaryNotes(notes)
            toast('Primary insights saved')
        } catch (e: any) {
            setErrorFor('primary', e.message)
        } finally {
            setLoadingFor('primary', false)
        }
    }, [sessionId])

    const computeFiveCs = useCallback(async () => {
        if (!sessionId) { setErrorFor('fivecs', 'No active session — save entity first'); return }
        setLoadingFor('fivecs', true)
        try {
            const res = await api.getFiveCsScores(sessionId)
            setFiveCsScores(res.scores)
            setCreditScore(res.scores.overall_score)
            setCreditRating(res.scores.credit_rating)
            setRecommendation(res.scores.recommendation)
            setRecommendedLimit(res.scores.recommended_limit)
            setProbabilityOfDefault(res.scores.probability_of_default)
            toast('Five Cs scoring complete')
        } catch (e: any) {
            setErrorFor('fivecs', e.message)
        } finally {
            setLoadingFor('fivecs', false)
        }
    }, [sessionId])

    const generateCAMAction = useCallback(async () => {
        setLoadingFor('cam', true)
        try {
            const insightTexts = researchInsights.map(i => i.content)
            const res = await api.generateCAM(
                entityName || 'Demo Entity',
                financials,
                insightTexts,
                primaryNotes,
                sessionId || undefined
            )
            setCamReport(res.cam_report)
            toast('Credit Appraisal Memo generated')
        } catch (e: any) {
            setErrorFor('cam', e.message)
        } finally {
            setLoadingFor('cam', false)
        }
    }, [sessionId, entityName, financials, researchInsights, primaryNotes])

    const loadSession = useCallback(async (sid: string) => {
        setLoadingFor('session', true)
        try {
            const res = await api.getSession(sid)
            hydrateFromSession(res.session)
        } catch (e: any) {
            setErrorFor('session', e.message)
        } finally {
            setLoadingFor('session', false)
        }
    }, [])

    // ── Value ───────────────────────────────────────────────────────────────

    const value: AppContextType = {
        sessionId, entityName, cinGstin, sector, facilityType, requestedLoanAmount,
        ingestedDocs, financials, latestExtraction, richGstData,
        researchInsights, primaryNotes,
        fiveCsScores, camReport,
        creditScore, creditRating, recommendation, recommendedLimit, probabilityOfDefault,
        isLoading, errors, toastMessage,
        saveEntity, ingestDocument: ingestDocumentAction,
        triggerResearch, savePrimaryInsights: savePrimaryInsightsAction,
        computeFiveCs, generateCAM: generateCAMAction,
        clearError, clearToast, loadSession,
    }

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}


// ── Hook ────────────────────────────────────────────────────────────────────

export function useApp(): AppContextType {
    const ctx = useContext(AppContext)
    if (!ctx) throw new Error('useApp must be used within AppProvider')
    return ctx
}
