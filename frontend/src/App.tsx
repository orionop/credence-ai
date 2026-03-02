import { useState } from 'react'
import './index.css'
import { useApp } from './AppContext'
import EntityIngestionView from './EntityIngestionView'
import RiskIntelligenceView from './RiskIntelligenceView'
import FiveCsAnalysisView from './FiveCsAnalysisView'

type ViewType = 'dashboard' | 'appraisal' | 'gst' | 'entity' | 'risk' | 'fivecs'

function App() {
    const [currentView, setCurrentView] = useState<ViewType>('dashboard')
    const [activeSidebarItem, setActiveSidebarItem] = useState('dashboard')
    const app = useApp()

    return (
        <div className="bg-background-light dark:bg-background-dark font-display text-slate-900 dark:text-slate-100">
            <div className="flex min-h-screen">

                {/* ═══════════════════════════════════════════════════════════════ */}
                {/* SIDEBAR                                                       */}
                {/* ═══════════════════════════════════════════════════════════════ */}
                <aside className="w-64 border-r border-primary/10 bg-background-light dark:bg-background-dark flex flex-col shrink-0">
                    <div className="p-6 flex items-center gap-3">
                        <div className="size-10 bg-primary rounded-lg flex items-center justify-center text-background-dark">
                            <span className="material-symbols-outlined">account_balance</span>
                        </div>
                        <div>
                            <h1 className="serif-heading text-xl font-bold tracking-tight text-primary">CredenceAI</h1>
                            <p className="text-[10px] text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-widest">Institutional Banking</p>
                        </div>
                    </div>

                    <nav className="flex-1 px-4 py-4 space-y-1">
                        {[
                            { id: 'dashboard', icon: 'dashboard', label: 'Dashboard', view: 'dashboard' as ViewType },
                            { id: 'entity', icon: 'settings_input_component', label: 'Entity & Ingestion', view: 'entity' as ViewType },
                            { id: 'risk', icon: 'account_tree', label: 'Risk Intelligence', view: 'risk' as ViewType },
                            { id: 'appraisal', icon: 'article', label: 'Appraisal Memo', view: 'appraisal' as ViewType },
                            { id: 'gst', icon: 'receipt_long', label: 'GST Reconciliation', view: 'gst' as ViewType },
                            { id: 'fivecs', icon: 'analytics', label: 'Five Cs Analysis', view: 'fivecs' as ViewType },
                        ].map((item) => (
                            <button
                                key={item.id}
                                onClick={() => { setActiveSidebarItem(item.id); setCurrentView(item.view); }}
                                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors font-medium text-left ${activeSidebarItem === item.id
                                    ? 'bg-primary/10 text-primary font-semibold border border-primary/20'
                                    : 'text-slate-500 dark:text-slate-400 hover:bg-primary/5 hover:text-primary'
                                    }`}
                            >
                                <span className="material-symbols-outlined">{item.icon}</span>
                                <span className="text-sm">{item.label}</span>
                            </button>
                        ))}
                    </nav>

                    {/* Session Info */}
                    <div className="px-4 py-3 border-t border-primary/10">
                        {app.sessionId ? (
                            <div className="p-2 bg-primary/5 rounded-lg">
                                <p className="text-[10px] text-primary font-bold uppercase tracking-widest">Active Session</p>
                                <p className="text-xs font-bold truncate mt-0.5">{app.entityName || 'Unnamed'}</p>
                                <p className="text-[10px] text-slate-500 font-mono">{app.sessionId}</p>
                            </div>
                        ) : (
                            <p className="text-[10px] text-slate-500 italic text-center">No active session</p>
                        )}
                    </div>

                    <div className="p-4 border-t border-primary/10">
                        <div className="flex items-center gap-3 p-2 rounded-lg bg-primary/5">
                            <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">MS</div>
                            <div className="overflow-hidden">
                                <p className="text-xs font-bold truncate">Marcus Sterling</p>
                                <p className="text-[10px] text-slate-500 uppercase tracking-widest truncate">Lead Credit Analyst</p>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* ═══════════════════════════════════════════════════════════════ */}
                {/* MAIN CONTENT                                                   */}
                {/* ═══════════════════════════════════════════════════════════════ */}
                <main className="flex-1 flex flex-col min-w-0">

                    {/* Header */}
                    <header className="h-16 border-b border-primary/10 bg-background-light/50 dark:bg-background-dark/50 backdrop-blur-md flex items-center justify-between px-8 shrink-0">
                        <div className="flex items-center flex-1 max-w-xl">
                            <div className="relative w-full">
                                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">search</span>
                                <input
                                    className="w-full bg-primary/5 border border-primary/10 rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-1 focus:ring-primary focus:border-primary focus:outline-none"
                                    placeholder="Search entities, GSTIN, or PAN..."
                                    type="text"
                                />
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <button className="p-2 text-slate-400 hover:text-primary transition-colors relative">
                                <span className="material-symbols-outlined">notifications</span>
                                {app.ingestedDocs.length > 0 && <span className="absolute top-2 right-2 flex h-2 w-2 rounded-full bg-risk-high"></span>}
                            </button>
                            <button className="p-2 text-slate-400 hover:text-primary transition-colors">
                                <span className="material-symbols-outlined">settings</span>
                            </button>
                            <div className="h-6 w-px bg-primary/20"></div>
                            <button
                                onClick={() => { setActiveSidebarItem('risk'); setCurrentView('risk'); }}
                                className="flex h-9 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-bold text-background-dark hover:bg-primary/90 transition-colors"
                            >
                                <span className="material-symbols-outlined text-lg">psychology</span>
                                Research Agent
                            </button>
                        </div>
                    </header>

                    {/* View Switcher */}
                    {currentView === 'dashboard' && <DashboardView onNavigate={(v: ViewType) => { setCurrentView(v); setActiveSidebarItem(v); }} />}
                    {currentView === 'appraisal' && <AppraisalMemoView />}
                    {currentView === 'gst' && <GSTReconciliationView />}
                    {currentView === 'entity' && <EntityIngestionView />}
                    {currentView === 'risk' && <RiskIntelligenceView />}
                    {currentView === 'fivecs' && <FiveCsAnalysisView />}
                </main>
            </div>
        </div>
    )
}


/* ─────────────────────────────────────────────────────────────────────────── */
/* VIEW: Dashboard                                                             */
/* ─────────────────────────────────────────────────────────────────────────── */
function DashboardView({ onNavigate }: { onNavigate: (v: ViewType) => void }) {
    const app = useApp()

    const creditScoreDisplay = app.creditScore || 0
    const docsCount = app.ingestedDocs.length
    const insightsCount = app.researchInsights.length
    const hasCam = app.camReport.length > 0

    return (
        <div className="p-8 overflow-y-auto flex-1">
            {/* Toast */}
            {app.toastMessage && (
                <div className="fixed top-4 right-4 z-50 bg-primary text-background-dark px-6 py-3 rounded-lg shadow-2xl text-sm font-bold animate-pulse">
                    {app.toastMessage}
                </div>
            )}

            {/* Title Section */}
            <div className="flex justify-between items-end mb-8">
                <div>
                    <div className="flex items-center gap-2 text-primary font-semibold text-sm mb-1 uppercase tracking-wider">
                        <span className="material-symbols-outlined text-sm">corporate_fare</span>
                        {app.sessionId ? 'Active Appraisal' : 'Getting Started'}
                    </div>
                    <h2 className="text-3xl font-black tracking-tight">
                        {app.entityName || 'Welcome to CredenceAI'}
                    </h2>
                    <p className="text-slate-500 mt-1">
                        {app.sessionId
                            ? `Session ${app.sessionId} • ${app.sector}`
                            : 'Start by configuring an entity in the Entity & Ingestion tab'}
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => onNavigate('entity')}
                        className="px-4 py-2 bg-primary/5 border border-primary/20 rounded-lg text-sm font-bold hover:bg-primary/10 transition-colors text-primary"
                    >
                        {app.sessionId ? 'Edit Entity' : 'New Entity'}
                    </button>
                    <button
                        onClick={async () => { if (app.sessionId) { await app.generateCAM(); onNavigate('appraisal'); } else { onNavigate('entity'); } }}
                        disabled={app.isLoading.cam}
                        className="px-4 py-2 bg-primary text-background-dark rounded-lg text-sm font-bold hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                        {app.isLoading.cam ? 'Generating...' : hasCam ? 'View CAM' : 'Generate CAM'}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6">
                {/* Left Column */}
                <div className="col-span-8 space-y-6">

                    {/* Scorecard Grid */}
                    <div className="grid grid-cols-2 gap-6">
                        {/* AI Credit Scorecard */}
                        <div className="bg-white dark:bg-surface-dark p-6 rounded-xl border border-primary/10 shadow-sm">
                            <p className="text-sm font-medium text-slate-500 mb-4">AI Credit Scorecard</p>
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="text-4xl font-black text-slate-900 dark:text-white">
                                        {creditScoreDisplay || '—'}<span className="text-slate-400 text-xl font-normal">/100</span>
                                    </div>
                                    <div className="flex items-center gap-1 text-primary text-sm font-bold mt-1">
                                        <span className="material-symbols-outlined text-sm">
                                            {app.creditRating ? 'verified' : 'pending'}
                                        </span>
                                        {app.creditRating || 'Not scored yet'}
                                    </div>
                                </div>
                                <div className="size-20 rounded-full border-8 border-primary/10 flex items-center justify-center relative">
                                    <svg className="absolute inset-0 size-full -rotate-90">
                                        <circle className="text-primary" cx="40" cy="40" fill="transparent" r="36"
                                            stroke="currentColor" strokeDasharray="226"
                                            strokeDashoffset={226 - (226 * creditScoreDisplay / 100)}
                                            strokeWidth="8" />
                                    </svg>
                                    <span className="material-symbols-outlined text-primary text-3xl">verified</span>
                                </div>
                            </div>
                        </div>

                        {/* Risk Level */}
                        <div className="bg-white dark:bg-surface-dark p-6 rounded-xl border border-primary/10 shadow-sm">
                            <p className="text-sm font-medium text-slate-500 mb-4">Risk Level Assessment</p>
                            <div className="flex flex-col gap-2">
                                <div className="flex items-center gap-2">
                                    <span className={`px-3 py-1 rounded-full text-sm font-bold border uppercase ${app.recommendation === 'approved' ? 'bg-green-500/10 text-green-500 border-green-500/20' :
                                        app.recommendation === 'rejected' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                                            app.recommendation === 'conditional' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' :
                                                'bg-primary/10 text-primary border-primary/20'
                                        }`}>
                                        {app.recommendation || 'Pending'}
                                    </span>
                                </div>
                                <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                                    {app.probabilityOfDefault
                                        ? `Probability of default: ${app.probabilityOfDefault}`
                                        : 'Run Five Cs Analysis to compute risk profile'}
                                </p>
                                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full mt-2 overflow-hidden">
                                    <div className={`h-full rounded-full transition-all duration-700 ${app.recommendation === 'approved' ? 'bg-green-500' :
                                        app.recommendation === 'rejected' ? 'bg-red-500' :
                                            'bg-amber-500'
                                        }`} style={{ width: `${creditScoreDisplay}%` }}></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Data Ingestion Status */}
                    <div className="bg-white dark:bg-surface-dark p-6 rounded-xl border border-primary/10 shadow-sm">
                        <h3 className="font-bold text-lg mb-6 flex items-center gap-2">
                            <span className="material-symbols-outlined text-primary">cloud_sync</span>
                            Data Ingestion Status
                        </h3>
                        <div className="space-y-6">
                            {[
                                { label: 'Documents Ingested', pct: Math.min(docsCount * 33, 100), status: `${docsCount} files processed` },
                                { label: 'Research Insights', pct: insightsCount > 0 ? 100 : 0, status: `${insightsCount} insights gathered` },
                                { label: 'CAM Report', pct: hasCam ? 100 : 0, status: hasCam ? 'Generated' : 'Pending Generation' },
                            ].map((item) => (
                                <div key={item.label}>
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="font-medium">{item.label}</span>
                                        <span className="text-primary font-bold">{item.status}</span>
                                    </div>
                                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full">
                                        <div className="bg-primary h-full rounded-full transition-all duration-700" style={{ width: `${item.pct}%` }}></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* AI Insights */}
                    <div className="bg-white dark:bg-surface-dark p-6 rounded-xl border border-primary/10 shadow-sm">
                        <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                            <span className="material-symbols-outlined text-primary">psychology</span>
                            AI Insights &amp; Signals
                        </h3>
                        <div className="space-y-4">
                            {app.researchInsights.length > 0 ? (
                                app.researchInsights.slice(0, 3).map((insight, i) => (
                                    <div key={i} className="flex gap-4 p-4 rounded-lg bg-primary/5 border border-primary/10">
                                        <span className="material-symbols-outlined text-primary mt-0.5">lightbulb</span>
                                        <div>
                                            <p className="font-bold text-sm">{insight.title}</p>
                                            <p className="text-xs text-slate-500 mt-1 line-clamp-2">{insight.content}</p>
                                        </div>
                                    </div>
                                ))
                            ) : app.financials.flags?.length > 0 ? (
                                app.financials.flags.map((flag: string, i: number) => (
                                    <div key={i} className="flex gap-4 p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                        <span className="material-symbols-outlined text-amber-500 mt-0.5">warning</span>
                                        <div>
                                            <p className="font-bold text-amber-900 dark:text-amber-400">{flag}</p>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="p-4 rounded-lg bg-primary/5 border border-primary/10 text-center">
                                    <span className="material-symbols-outlined text-slate-400 text-2xl mb-2">info</span>
                                    <p className="text-sm text-slate-500">Upload documents and run research to see AI insights here.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column */}
                <div className="col-span-4 space-y-6">
                    {/* Quick Actions */}
                    <div className="bg-white dark:bg-surface-dark p-6 rounded-xl border border-primary/10 shadow-sm">
                        <h3 className="font-bold text-lg mb-6">Quick Actions</h3>
                        <div className="flex flex-col gap-3">
                            {[
                                { icon: 'upload_file', label: 'Upload Documents', action: () => onNavigate('entity'), primary: !app.sessionId },
                                { icon: 'search', label: 'Run Research Agent', action: () => onNavigate('risk'), primary: docsCount > 0 && insightsCount === 0 },
                                { icon: 'analytics', label: 'Compute Five Cs', action: () => onNavigate('fivecs'), primary: false },
                                { icon: 'picture_as_pdf', label: 'Generate CAM PDF', action: async () => { await app.generateCAM(); onNavigate('appraisal'); }, primary: insightsCount > 0 && !hasCam },
                            ].map((action) => (
                                <button
                                    key={action.label}
                                    onClick={action.action}
                                    className={`w-full flex items-center justify-between p-4 rounded-lg transition-colors group ${action.primary
                                        ? 'border-2 border-primary bg-primary/5 text-primary hover:bg-primary/10'
                                        : 'border border-primary/10 hover:bg-primary/5'
                                        }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="material-symbols-outlined">{action.icon}</span>
                                        <span className="font-bold text-sm">{action.label}</span>
                                    </div>
                                    <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Application Details */}
                    <div className="bg-white dark:bg-surface-dark p-6 rounded-xl border border-primary/10 shadow-sm">
                        <h3 className="font-bold text-lg mb-4">Application Details</h3>
                        <div className="space-y-4">
                            {[
                                { label: 'Entity', value: app.entityName || '—' },
                                { label: 'Sector', value: app.sector || '—' },
                                { label: 'Facility Type', value: app.facilityType || '—' },
                                { label: 'Recommended Limit', value: app.recommendedLimit || '—', highlight: true },
                            ].map((item, i) => (
                                <div key={item.label} className={`flex justify-between py-2 ${i < 3 ? 'border-b border-primary/10' : ''}`}>
                                    <span className="text-slate-500 text-sm">{item.label}</span>
                                    <span className={`font-bold text-sm ${item.highlight ? 'text-primary' : ''}`}>{item.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Recent Documents */}
                    <div className="bg-white dark:bg-surface-dark p-6 rounded-xl border border-primary/10 shadow-sm">
                        <h3 className="font-bold text-lg mb-4">Ingested Documents</h3>
                        <div className="space-y-3">
                            {app.ingestedDocs.length > 0 ? (
                                app.ingestedDocs.slice(0, 4).map((doc, i) => (
                                    <div key={i} className="flex items-center gap-3 p-2 hover:bg-primary/5 rounded-lg transition-colors">
                                        <div className="size-10 flex items-center justify-center bg-primary/10 text-primary rounded">
                                            <span className="material-symbols-outlined">{doc.filename.endsWith('.pdf') ? 'picture_as_pdf' : 'table_chart'}</span>
                                        </div>
                                        <div className="overflow-hidden">
                                            <p className="text-sm font-bold truncate">{doc.filename}</p>
                                            <p className="text-xs text-slate-400">{doc.doc_type} • {doc.status}</p>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="text-sm text-slate-500 italic text-center py-4">No documents yet</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}


/* ─────────────────────────────────────────────────────────────────────────── */
/* VIEW: Appraisal Synthesis Memo                                              */
/* ─────────────────────────────────────────────────────────────────────────── */
function AppraisalMemoView() {
    const app = useApp()
    const [localNotes, setLocalNotes] = useState(app.primaryNotes || '')

    const handleGenerateCAM = async () => {
        await app.generateCAM()
    }

    const handleSaveNotes = async () => {
        await app.savePrimaryInsights(localNotes)
    }

    // Parse cam_report markdown into sections (simple renderer)
    const renderCAM = (md: string) => {
        return md.split('\n').map((line, i) => {
            if (line.startsWith('# ')) return <h3 key={i} className="text-xl font-bold border-b border-zinc-300 pb-2 mb-4 mt-8">{line.slice(2)}</h3>
            if (line.startsWith('## ')) return <h4 key={i} className="text-lg font-bold border-b border-zinc-300 pb-1 mb-3 mt-6 uppercase tracking-wide">{line.slice(3)}</h4>
            if (line.startsWith('### ')) return <h5 key={i} className="text-md font-bold mb-2 mt-4">{line.slice(4)}</h5>
            if (line.startsWith('**') && line.endsWith('**')) return <p key={i} className="font-bold text-sm mt-2">{line.slice(2, -2)}</p>
            if (line.startsWith('- ')) return <li key={i} className="ml-5 text-base leading-relaxed list-disc">{line.slice(2)}</li>
            if (line.trim() === '') return <br key={i} />
            return <p key={i} className="text-base leading-relaxed">{line}</p>
        })
    }

    return (
        <div className="flex flex-col flex-1 overflow-hidden">
            {/* Toast */}
            {app.toastMessage && (
                <div className="fixed top-4 right-4 z-50 bg-primary text-background-dark px-6 py-3 rounded-lg shadow-2xl text-sm font-bold animate-pulse">
                    {app.toastMessage}
                </div>
            )}

            {/* Top bar with entity context */}
            <div className="flex items-center justify-between px-8 py-4 border-b border-primary/10 bg-primary/5 shrink-0">
                <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                        <span className="material-symbols-outlined">description</span>
                    </div>
                    <div>
                        <h2 className="text-lg font-bold">{app.entityName || 'No Entity Configured'}</h2>
                        <p className="text-xs text-slate-500">{app.sector} {app.sessionId ? `• Session ${app.sessionId}` : ''}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleGenerateCAM}
                        disabled={app.isLoading.cam}
                        className="bg-primary text-background-dark px-5 py-2 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-primary/90 transition-colors disabled:opacity-50 shadow-lg"
                    >
                        <span className="material-symbols-outlined text-lg">
                            {app.isLoading.cam ? 'hourglass_empty' : 'article'}
                        </span>
                        {app.isLoading.cam ? 'Generating...' : app.camReport ? 'Regenerate CAM' : 'Generate CAM'}
                    </button>
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">

                <div className="flex-1 overflow-y-auto bg-zinc-900/50 p-8 scroll-smooth">
                    <div className="max-w-4xl mx-auto flex flex-col gap-6">
                        <div className="flex flex-col gap-2">
                            <div className="flex items-center gap-2 text-xs text-primary/60 uppercase font-bold tracking-widest">
                                <span>Credit Engine</span>
                                <span className="material-symbols-outlined text-[10px]">arrow_forward_ios</span>
                                <span>Institutional</span>
                                <span className="material-symbols-outlined text-[10px]">arrow_forward_ios</span>
                                <span className="text-primary">Appraisal Synthesis</span>
                            </div>
                            <h2 className="text-3xl font-black">Credit Appraisal Memo (CAM)</h2>
                        </div>

                        {/* Generate Button */}
                        {!app.camReport && (
                            <div className="bg-primary/5 border border-primary/20 rounded-xl p-8 text-center">
                                <span className="material-symbols-outlined text-5xl text-primary mb-4">description</span>
                                <h3 className="text-lg font-bold mb-2">Generate Credit Appraisal Memo</h3>
                                <p className="text-sm text-slate-500 mb-6">
                                    The AI will synthesize all ingested data, research insights, and field notes
                                    into a professional Five Cs analysis memo.
                                </p>
                                <button
                                    onClick={handleGenerateCAM}
                                    disabled={app.isLoading.cam}
                                    className="bg-primary text-background-dark px-8 py-3 rounded-lg font-bold hover:bg-primary/90 transition-colors disabled:opacity-50"
                                >
                                    {app.isLoading.cam ? 'Generating CAM (this may take 30s)...' : 'Generate CAM Report'}
                                </button>
                            </div>
                        )}

                        {/* Memo Paper */}
                        {app.camReport && (
                            <div className="bg-memo-paper text-zinc-900 p-12 rounded-sm memo-shadow font-serif border border-zinc-200">
                                <div className="flex justify-between items-start border-b-2 border-zinc-800 pb-6 mb-8">
                                    <div>
                                        <h3 className="text-xl font-bold uppercase tracking-tighter">CredenceAI Synthesis Report</h3>
                                        <p className="text-sm italic">Automated Underwriting Summary • Internal Use Only</p>
                                    </div>
                                    <div className="text-right text-sm">
                                        <p>Entity: {app.entityName}</p>
                                        <p>Session: {app.sessionId}</p>
                                    </div>
                                </div>
                                <div className="prose prose-sm max-w-none">
                                    {renderCAM(app.camReport)}
                                </div>

                                {/* Decision Block */}
                                {app.recommendation && (
                                    <section className="mt-12 bg-zinc-100 p-8 border-l-4 border-primary">
                                        <h4 className="text-sm font-bold uppercase tracking-widest text-zinc-500 mb-6 text-center">Final Underwriting Decision</h4>
                                        <div className="flex flex-col items-center justify-center gap-6">
                                            <div className="flex gap-4">
                                                {['approved', 'conditional', 'rejected'].map(r => (
                                                    <span key={r} className={`px-6 py-2 border-2 font-bold rounded flex items-center gap-2 uppercase ${app.recommendation === r
                                                        ? r === 'approved' ? 'border-green-600 bg-green-50 text-green-700' :
                                                            r === 'rejected' ? 'border-red-600 bg-red-50 text-red-700' :
                                                                'border-amber-600 bg-amber-50 text-amber-700'
                                                        : 'border-zinc-300 text-zinc-400'
                                                        }`}>
                                                        {app.recommendation === r && <span className="material-symbols-outlined text-sm">check_circle</span>}
                                                        {r}
                                                    </span>
                                                ))}
                                            </div>
                                            {app.recommendedLimit && (
                                                <div className="text-center">
                                                    <p className="text-xs uppercase font-bold text-zinc-500 mb-1">Recommended Credit Limit</p>
                                                    <p className="text-4xl font-bold tracking-tight text-zinc-900">{app.recommendedLimit}</p>
                                                </div>
                                            )}
                                        </div>
                                    </section>
                                )}
                            </div>
                        )}

                        {/* Regenerate */}
                        {app.camReport && (
                            <div className="flex justify-center">
                                <button
                                    onClick={handleGenerateCAM}
                                    disabled={app.isLoading.cam}
                                    className="bg-primary/10 text-primary border border-primary/20 px-6 py-2 rounded-lg text-sm font-bold hover:bg-primary/20 transition-colors disabled:opacity-50"
                                >
                                    {app.isLoading.cam ? 'Regenerating...' : 'Regenerate CAM'}
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Sidebar: Risk Model */}
                <aside className="w-72 border-l border-primary/10 bg-primary/5 p-6 overflow-y-auto shrink-0 custom-scrollbar">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-primary/60 mb-6 flex items-center gap-2">
                        <span className="material-symbols-outlined text-lg">psychology</span> Risk Model
                    </h3>
                    <div className="space-y-8">
                        <div className="flex flex-col items-center justify-center p-6 bg-white dark:bg-primary/5 rounded-2xl border border-primary/20">
                            <div className="relative size-32 mb-4">
                                <svg className="size-full -rotate-90" viewBox="0 0 36 36">
                                    <circle className="stroke-primary/10" cx="18" cy="18" fill="none" r="16" strokeWidth="3" />
                                    <circle className="stroke-primary" cx="18" cy="18" fill="none" r="16"
                                        strokeDasharray={`${app.creditScore}, 100`} strokeWidth="3" />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-3xl font-black text-primary">{app.creditScore || '—'}</span>
                                    <span className="text-[10px] uppercase font-bold text-slate-400">Score</span>
                                </div>
                            </div>
                            <p className="text-sm font-semibold italic">
                                {app.creditRating ? `"${app.creditRating} — ${app.recommendation}"` : '"Awaiting Analysis"'}
                            </p>
                        </div>

                        {app.fiveCsScores && (
                            <div className="space-y-4">
                                <h4 className="text-xs font-bold uppercase text-slate-400">Weighted Breakdown</h4>
                                <div className="space-y-3">
                                    {(['character', 'capacity', 'capital', 'collateral', 'conditions'] as const).map((key) => {
                                        const cs = app.fiveCsScores?.[key]
                                        const score = typeof cs === 'object' && cs && 'score' in cs ? (cs as any).score : 0
                                        return (
                                            <div key={key}>
                                                <div className="flex justify-between text-xs mb-1">
                                                    <span className="text-slate-500 capitalize">{key}</span>
                                                    <span className="font-bold">{score}/100</span>
                                                </div>
                                                <div className="w-full bg-primary/10 h-1.5 rounded-full overflow-hidden">
                                                    <div className="bg-primary h-full transition-all duration-700" style={{ width: `${score}%` }} />
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )}

                        <button
                            onClick={handleGenerateCAM}
                            disabled={app.isLoading.cam}
                            className="w-full py-3 bg-primary text-background-dark font-bold rounded-lg hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {app.isLoading.cam ? 'Generating...' : 'Finalize & E-Sign Memo'}
                            <span className="material-symbols-outlined text-lg">ink_pen</span>
                        </button>

                        {/* Field Notes (moved from old left sidebar) */}
                        <div className="mt-4 pt-4 border-t border-primary/10">
                            <h4 className="text-xs font-bold text-primary uppercase tracking-widest mb-2">Field Notes</h4>
                            <textarea
                                value={localNotes}
                                onChange={e => setLocalNotes(e.target.value)}
                                placeholder="e.g. Factory found operating at 40% capacity..."
                                className="w-full bg-background-dark/50 border border-primary/10 rounded-lg p-3 text-xs text-slate-300 focus:ring-1 focus:ring-primary outline-none resize-none h-24"
                            />
                            <button
                                onClick={handleSaveNotes}
                                disabled={app.isLoading.primary || !localNotes.trim()}
                                className="w-full mt-2 bg-primary/10 text-primary border border-primary/20 py-1.5 rounded-lg text-xs font-bold hover:bg-primary/20 transition-colors disabled:opacity-50"
                            >
                                {app.isLoading.primary ? 'Saving...' : 'Save Notes'}
                            </button>
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    )
}


/* ─────────────────────────────────────────────────────────────────────────── */
/* VIEW: GST vs Bank Reconciliation Hub                                        */
/* ─────────────────────────────────────────────────────────────────────────── */
function GSTReconciliationView() {
    const app = useApp()
    const hasRealData = Object.keys(app.financials).length > 0 && app.financials.revenue_yoy_growth !== undefined

    const transactions = [
        { entity: app.entityName || 'Apex Logistics Pvt Ltd', gstin: app.cinGstin || '27AABCA1234F1Z5', gstSales: '₹8,45,20,000', bankCredit: '₹2,10,00,000', variance: '-75.15%', varianceColor: 'rose', icon: 'report', iconColor: 'rose', highlight: false },
        { entity: 'Stellar Infrastructure', gstin: '07AQWPM9901L2ZA', gstSales: '₹4,12,00,000', bankCredit: '₹4,12,05,000', variance: '+0.01%', varianceColor: 'emerald', icon: 'cycle', iconColor: 'amber', highlight: true },
        { entity: 'Blue Horizon Imports', gstin: '29MMNNB1231D1X9', gstSales: '₹1,80,00,000', bankCredit: '₹1,78,50,000', variance: '-0.83%', varianceColor: 'slate', icon: 'check_circle', iconColor: 'slate', highlight: false },
        { entity: 'Zenith Tech Solutions', gstin: '19KKLJJ8811K3Z0', gstSales: '₹5,90,00,000', bankCredit: '₹0', variance: '-100%', varianceColor: 'rose', icon: 'error', iconColor: 'rose', highlight: false },
        { entity: 'Orbit Trading Co.', gstin: '33FFGGG4455H1Z3', gstSales: '₹2,45,00,000', bankCredit: '₹2,45,00,000', variance: '0.00%', varianceColor: 'emerald', icon: 'autorenew', iconColor: 'amber', highlight: false },
    ]

    return (
        <div className="flex flex-col flex-1 overflow-hidden">
            {/* Toast */}
            {app.toastMessage && (
                <div className="fixed top-4 right-4 z-50 bg-primary text-background-dark px-6 py-3 rounded-lg shadow-2xl text-sm font-bold animate-pulse">
                    {app.toastMessage}
                </div>
            )}

            {/* Top bar */}
            <div className="flex items-center justify-between px-8 py-4 border-b border-primary/10 bg-primary/5 shrink-0">
                <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                        <span className="material-symbols-outlined">receipt_long</span>
                    </div>
                    <div>
                        <h2 className="text-lg font-bold">GST vs Bank Reconciliation</h2>
                        <p className="text-xs text-slate-500">{app.entityName || 'No Entity'} • {app.ingestedDocs.length} documents • {app.financials.flags?.length || 0} flags</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => alert('Filter functionality coming soon')}
                        className="px-4 py-2 bg-primary/10 border border-primary/20 rounded-lg text-xs font-bold flex items-center gap-2"
                    >
                        <span className="material-symbols-outlined text-[18px]">filter_list</span> Filter
                    </button>
                    <button
                        onClick={() => alert('Export report functionality coming soon')}
                        className="px-4 py-2 bg-primary text-background-dark rounded-lg text-xs font-bold flex items-center gap-2"
                    >
                        <span className="material-symbols-outlined text-[18px]">download</span> Export Report
                    </button>
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* Main: Transaction Ledger */}
                <main className="flex-1 overflow-hidden flex flex-col bg-background-light dark:bg-background-dark">
                    {/* Summary Cards */}
                    <div className="p-6 flex flex-wrap gap-4 border-b border-primary/20">
                        <div className="flex-1 min-w-[220px] bg-primary/5 border border-primary/10 p-5 rounded-xl">
                            <p className="text-sm text-primary/60 font-medium">Revenue Integrity Score</p>
                            <h3 className="text-3xl font-black mt-1">{app.creditScore || '—'}/100</h3>
                        </div>
                        <div className="flex-1 min-w-[220px] bg-primary/5 border border-primary/10 p-5 rounded-xl">
                            <p className="text-sm text-primary/60 font-medium">Documents Ingested</p>
                            <h3 className="text-3xl font-black mt-1">{app.ingestedDocs.length}</h3>
                            <div className="mt-4"><span className="text-[10px] font-bold py-0.5 px-2 bg-primary/10 text-primary rounded border border-primary/20">
                                {hasRealData ? 'Verified' : 'Awaiting Data'}
                            </span></div>
                        </div>
                        <div className="flex-1 min-w-[220px] bg-primary/5 border border-primary/10 p-5 rounded-xl">
                            <p className="text-sm text-primary/60 font-medium">Flagged Items</p>
                            <h3 className="text-3xl font-black mt-1">{app.financials.flags?.length || 0}</h3>
                            <p className="text-xs text-rose-500 flex items-center gap-1 mt-2">
                                {app.financials.flags?.length > 0 ? 'Requires Review' : 'Clean'}
                            </p>
                        </div>
                    </div>

                    {/* Table */}
                    <div className="flex-1 overflow-hidden flex flex-col p-6">
                        <h2 className="text-xl font-bold mb-6">Transaction Reconciliation Ledger</h2>
                        <div className="flex-1 overflow-auto border border-primary/20 rounded-xl bg-white dark:bg-background-dark/20">
                            <table className="w-full text-left border-collapse min-w-[900px]">
                                <thead className="sticky top-0 bg-background-dark z-20 shadow-sm">
                                    <tr>
                                        <th className="p-4 text-[10px] uppercase font-bold text-primary/50 tracking-widest border-b border-primary/20">Entity / Vendor</th>
                                        <th className="p-4 text-[10px] uppercase font-bold text-primary/50 tracking-widest border-b border-primary/20">GSTR-1/3B Sales</th>
                                        <th className="p-4 text-[10px] uppercase font-bold text-primary/50 tracking-widest border-b border-primary/20">Bank Credit (Actual)</th>
                                        <th className="p-4 text-[10px] uppercase font-bold text-primary/50 tracking-widest border-b border-primary/20">Variance %</th>
                                        <th className="p-4 text-[10px] uppercase font-bold text-primary/50 tracking-widest border-b border-primary/20 text-center">AI Flag</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-primary/10">
                                    {transactions.map((tx) => (
                                        <tr key={tx.entity} className={`group hover:bg-primary/5 transition-colors ${tx.highlight ? 'bg-rose-500/5' : ''}`}>
                                            <td className="p-4">
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-bold">{tx.entity}</span>
                                                    <span className="text-[10px] text-primary/40">GSTIN: {tx.gstin}</span>
                                                </div>
                                            </td>
                                            <td className="p-4 text-sm font-medium">{tx.gstSales}</td>
                                            <td className="p-4 text-sm font-medium">{tx.bankCredit}</td>
                                            <td className="p-4">
                                                <span className={`text-sm font-black ${tx.varianceColor === 'rose' ? 'text-rose-500' : tx.varianceColor === 'emerald' ? 'text-emerald-500' : 'text-slate-500'}`}>{tx.variance}</span>
                                            </td>
                                            <td className="p-4 text-center">
                                                <span className={`material-symbols-outlined ${tx.iconColor === 'rose' ? 'text-rose-500' : tx.iconColor === 'amber' ? 'text-amber-500' : 'text-slate-500'}`}>{tx.icon}</span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </main>

                {/* Right Panel: Anomaly Inspector */}
                <aside className="w-80 border-l border-primary/20 flex flex-col bg-primary/5 shrink-0">
                    <div className="p-6 border-b border-primary/20">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-primary/60 mb-1">AI Inspector</h3>
                        <p className="text-lg font-bold">Anomaly Details</p>
                    </div>

                    {/* Network Graph Mini */}
                    <div className="p-4 border-b border-primary/20">
                        <p className="text-xs font-bold text-primary uppercase tracking-widest mb-3">Circular Loop Detection</p>
                        <div className="w-full h-40 border border-primary/20 rounded-xl bg-background-dark/80 relative overflow-hidden">
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32">
                                <svg className="w-full h-full" viewBox="0 0 100 100">
                                    <circle className="animate-pulse" cx="50" cy="20" fill="#c5a981" r="5" />
                                    <circle cx="80" cy="70" fill="#c5a981" r="5" />
                                    <circle cx="20" cy="70" fill="#c5a981" r="5" />
                                    <path className="opacity-40" d="M50 20 L80 70 L20 70 Z" fill="none" stroke="#c5a981" strokeDasharray="4" strokeWidth="0.5" />
                                </svg>
                            </div>
                        </div>
                    </div>

                    <div className="flex-1 overflow-auto p-4 custom-scrollbar">
                        <div className="space-y-4">
                            {app.financials.flags?.length > 0 ? (
                                app.financials.flags.map((flag: string, i: number) => (
                                    <div key={i} className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="material-symbols-outlined text-amber-500 text-[20px]">warning_amber</span>
                                            <span className="text-xs font-bold text-amber-500 uppercase tracking-tight">AI Flag</span>
                                        </div>
                                        <p className="text-sm font-bold mb-1">{flag}</p>
                                        <p className="text-[11px] text-slate-400 leading-normal">Detected during document ingestion. Review recommended.</p>
                                    </div>
                                ))
                            ) : (
                                <div className="p-4 rounded-lg bg-primary/5 border border-primary/10 text-center">
                                    <span className="material-symbols-outlined text-primary text-2xl mb-2">search</span>
                                    <p className="text-xs text-slate-500">Upload GST and Bank Statement data to enable anomaly detection.</p>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="p-4 border-t border-primary/20 bg-background-dark/80">
                        <button
                            onClick={() => alert('Enforcement notice generation coming soon')}
                            className="w-full py-3 bg-primary/20 text-primary border border-primary/30 rounded-lg text-xs font-bold hover:bg-primary/30 transition-all uppercase tracking-widest"
                        >
                            Generate Enforcement Notice
                        </button>
                    </div>
                </aside>
            </div>
        </div>
    )
}

export default App

