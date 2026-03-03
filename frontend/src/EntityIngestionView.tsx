/**
 * Entity Configuration & Data Ingestion Dashboard
 * Every button is wired to the backend via AppContext.
 */

import { useState, useRef } from 'react'
import { useApp } from './AppContext'

export default function EntityIngestionView() {
    const app = useApp()

    // Local form state
    const [localName, setLocalName] = useState(app.entityName || '')
    const [localCin, setLocalCin] = useState(app.cinGstin || '')
    const [localSector, setLocalSector] = useState(app.sector || 'Manufacturing & Heavy Industries')
    const [localFacility, setLocalFacility] = useState(app.facilityType || 'Term Loan')
    const [localLoanAmount, setLocalLoanAmount] = useState(app.requestedLoanAmount || '')
    const [activeTab, setActiveTab] = useState<'gst' | 'bank' | 'annual'>('gst')
    const fileInputRef = useRef<HTMLInputElement>(null)

    const handleSaveEntity = async () => {
        await app.saveEntity(localName, localCin, localSector, localFacility, localLoanAmount)
    }

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files
        if (!files) return
        for (let i = 0; i < files.length; i++) {
            await app.ingestDocument(files[i])
        }
    }

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault()
        const files = e.dataTransfer.files
        for (let i = 0; i < files.length; i++) {
            await app.ingestDocument(files[i])
        }
    }

    return (
        <div className="flex-1 overflow-y-auto bg-background-light dark:bg-background-dark">
            {/* Toast */}
            {app.toastMessage && (
                <div className="fixed top-4 right-4 z-50 bg-primary text-background-dark px-6 py-3 rounded-lg shadow-2xl text-sm font-bold animate-pulse">
                    {app.toastMessage}
                </div>
            )}

            {/* Top Header */}
            <header className="h-16 border-b border-primary/10 flex items-center justify-between px-8 bg-background-light/50 dark:bg-background-dark/50 backdrop-blur-md sticky top-0 z-10">
                <h2 className="text-xl font-semibold">Entity Configuration &amp; Data Ingestion</h2>
                <div className="flex items-center gap-4">
                    {app.sessionId && (
                        <span className="text-[10px] text-primary font-bold bg-primary/10 px-3 py-1 rounded-full border border-primary/20">
                            Session: {app.sessionId}
                        </span>
                    )}
                    <button className="p-2 text-slate-400 hover:text-primary transition-colors">
                        <span className="material-symbols-outlined">notifications</span>
                    </button>
                    <div className="h-6 w-px bg-primary/20"></div>
                    <button
                        onClick={handleSaveEntity}
                        disabled={app.isLoading.entity || !localName.trim()}
                        className="bg-primary text-background-dark px-4 py-1.5 rounded-lg text-sm font-bold flex items-center gap-2 disabled:opacity-50 hover:bg-primary/90 transition-colors"
                    >
                        <span className="material-symbols-outlined text-[18px]">
                            {app.isLoading.entity ? 'hourglass_empty' : 'play_arrow'}
                        </span>
                        {app.isLoading.entity ? 'Saving...' : 'Run Engine'}
                    </button>
                </div>
            </header>

            <div className="p-8 space-y-8 max-w-7xl mx-auto">
                {/* Financial Telemetry Cards */}
                <section>
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg text-primary font-semibold">Financial Telemetry</h3>
                        <span className="text-[10px] text-slate-500 uppercase tracking-widest">
                            {app.financials.revenue_yoy_growth ? 'Live Data' : 'Awaiting Ingestion'}
                        </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {[
                            {
                                icon: 'trending_up',
                                label: 'Revenue Growth (YoY)',
                                value: app.financials.revenue_yoy_growth || '—',
                                badge: app.financials.revenue_yoy_growth ? 'Extracted' : 'Pending',
                                badgeColor: app.financials.revenue_yoy_growth ? 'green' : 'slate',
                                pct: app.financials.revenue_yoy_growth ? 74 : 0
                            },
                            {
                                icon: 'account_balance_wallet',
                                label: 'EBITDA Margin',
                                value: app.financials.ebitda_margin || '—',
                                badge: app.financials.ebitda_margin ? 'Extracted' : 'Pending',
                                badgeColor: app.financials.ebitda_margin ? 'green' : 'slate',
                                pct: app.financials.ebitda_margin ? 60 : 0
                            },
                            {
                                icon: 'security',
                                label: 'Debt-to-Equity',
                                value: app.financials.debt_to_equity || '—',
                                badge: app.financials.debt_to_equity ? 'Extracted' : 'Pending',
                                badgeColor: app.financials.debt_to_equity ? 'green' : 'slate',
                                pct: app.financials.debt_to_equity ? 50 : 0
                            },
                        ].map((card) => (
                            <div key={card.label} className="bg-white dark:bg-surface-dark p-6 rounded-xl border border-primary/10 relative overflow-hidden group hover:border-primary/30 transition-colors">
                                <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                                    <span className="material-symbols-outlined text-6xl text-primary">{card.icon}</span>
                                </div>
                                <p className="text-xs text-slate-500 uppercase font-semibold mb-2">{card.label}</p>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-3xl font-black text-primary">{card.value}</span>
                                    <span className={`text-xs font-bold ${card.badgeColor === 'green' ? 'text-green-500' : 'text-slate-400'}`}>{card.badge}</span>
                                </div>
                                <div className="mt-4 h-1 w-full bg-slate-100 dark:bg-slate-800 rounded-full">
                                    <div className="h-1 bg-primary rounded-full transition-all duration-700" style={{ width: `${card.pct}%` }}></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Error display */}
                {app.errors.entity && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-500 flex items-center justify-between">
                        <span>{app.errors.entity}</span>
                        <button onClick={() => app.clearError('entity')} className="material-symbols-outlined text-sm">close</button>
                    </div>
                )}
                {app.errors.ingest && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-500 flex items-center justify-between">
                        <span>{app.errors.ingest}</span>
                        <button onClick={() => app.clearError('ingest')} className="material-symbols-outlined text-sm">close</button>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Entity Configuration */}
                    <section className="bg-white dark:bg-surface-dark rounded-xl border border-primary/10 flex flex-col overflow-hidden">
                        <div className="p-6 border-b border-primary/10">
                            <h3 className="text-lg text-primary font-semibold">Entity Configuration</h3>
                            <p className="text-xs text-slate-500 mt-1">Define core corporate credentials for analysis</p>
                        </div>
                        <div className="p-6 space-y-6">
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-tighter">Entity Legal Name</label>
                                    <input
                                        value={localName}
                                        onChange={e => setLocalName(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-background-dark border border-primary/10 rounded-lg py-3 px-4 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none transition-all"
                                        placeholder="e.g. Acme Corp India Pvt Ltd"
                                        type="text"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-tighter">CIN / GSTIN</label>
                                    <input
                                        value={localCin}
                                        onChange={e => setLocalCin(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-background-dark border border-primary/10 rounded-lg py-3 px-4 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none transition-all"
                                        placeholder="U12345MH2024PTC123456"
                                        type="text"
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-tighter">Sector</label>
                                    <select
                                        value={localSector}
                                        onChange={e => setLocalSector(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-background-dark border border-primary/10 rounded-lg py-3 px-4 text-sm focus:ring-1 focus:ring-primary outline-none appearance-none"
                                    >
                                        <option>Manufacturing &amp; Heavy Industries</option>
                                        <option>Information Technology</option>
                                        <option>Pharmaceuticals</option>
                                        <option>Renewable Energy</option>
                                        <option>Infrastructure &amp; Real Estate</option>
                                        <option>FMCG</option>
                                        <option>Automobile</option>
                                        <option>Financial Services (NBFC)</option>
                                    </select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-tighter">Facility Type</label>
                                    <select
                                        value={localFacility}
                                        onChange={e => setLocalFacility(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-background-dark border border-primary/10 rounded-lg py-3 px-4 text-sm focus:ring-1 focus:ring-primary outline-none appearance-none"
                                    >
                                        <option>Term Loan</option>
                                        <option>Working Capital</option>
                                        <option>Letter of Credit</option>
                                        <option>Project Finance</option>
                                        <option>Bank Guarantee</option>
                                    </select>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 gap-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-400 uppercase tracking-tighter">Requested Loan Amount (INR)</label>
                                    <input
                                        value={localLoanAmount}
                                        onChange={e => setLocalLoanAmount(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-background-dark border border-primary/10 rounded-lg py-3 px-4 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none transition-all"
                                        placeholder="e.g. 50,00,00,000"
                                        type="text"
                                    />
                                </div>
                            </div>
                            <div className="pt-4 flex justify-end">
                                <button
                                    onClick={handleSaveEntity}
                                    disabled={app.isLoading.entity || !localName.trim()}
                                    className="bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 px-6 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
                                >
                                    {app.isLoading.entity ? 'Saving...' : 'Save Entity Profile'}
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* Secure Data Ingestion */}
                    <section className="bg-white dark:bg-surface-dark rounded-xl border border-primary/10 flex flex-col overflow-hidden">
                        <div className="p-6 border-b border-primary/10">
                            <h3 className="text-lg text-primary font-semibold">Secure Data Ingestion</h3>
                            <p className="text-xs text-slate-500 mt-1">Encrypted pipelines for financial statements</p>
                        </div>
                        <div className="p-6">
                            {/* Tabs */}
                            <div className="flex border-b border-primary/10 mb-6">
                                {(['gst', 'bank', 'annual'] as const).map(tab => (
                                    <button
                                        key={tab}
                                        onClick={() => setActiveTab(tab)}
                                        className={`px-4 py-2 text-sm font-medium transition-colors ${activeTab === tab
                                            ? 'border-b-2 border-primary text-primary font-semibold'
                                            : 'text-slate-400 hover:text-primary'
                                            }`}
                                    >
                                        {tab === 'gst' ? 'GST Logs' : tab === 'bank' ? 'Bank Statements' : 'Annual Reports'}
                                    </button>
                                ))}
                            </div>

                            {/* Drop Zone */}
                            <div
                                onDrop={handleDrop}
                                onDragOver={e => e.preventDefault()}
                                onClick={() => fileInputRef.current?.click()}
                                className="border-2 border-dashed border-primary/20 rounded-xl p-10 flex flex-col items-center justify-center text-center space-y-4 hover:border-primary/50 transition-colors group cursor-pointer"
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    multiple
                                    accept=".pdf,.csv,.json,.xlsx"
                                    onChange={handleFileUpload}
                                    className="hidden"
                                />
                                <div className="size-16 rounded-full bg-primary/5 flex items-center justify-center text-slate-400 group-hover:text-primary transition-colors">
                                    <span className="material-symbols-outlined text-4xl">
                                        {app.isLoading.ingest ? 'hourglass_empty' : 'upload_file'}
                                    </span>
                                </div>
                                <div>
                                    <p className="text-sm font-semibold">
                                        {app.isLoading.ingest ? 'Processing...' : `Drag and drop ${activeTab.toUpperCase()} files`}
                                    </p>
                                    <p className="text-xs text-slate-500 mt-1">PDF, CSV, JSON, XLSX — Max 50MB</p>
                                </div>
                                <button className="bg-primary text-background-dark px-5 py-2 rounded-lg text-xs font-bold uppercase tracking-wider shadow-lg hover:bg-primary/90 transition-colors">
                                    Browse Files
                                </button>
                            </div>

                            {/* Uploaded Files */}
                            {app.ingestedDocs.length > 0 && (
                                <div className="mt-6 space-y-3">
                                    {app.ingestedDocs.map((doc, i) => (
                                        <div key={i} className="flex items-center justify-between p-3 bg-primary/5 rounded-lg border border-primary/10">
                                            <div className="flex items-center gap-3">
                                                <span className={`material-symbols-outlined text-xl ${doc.status === 'verified' ? 'text-green-500' : 'text-amber-500'}`}>
                                                    {doc.status === 'verified' ? 'check_circle' : 'hourglass_empty'}
                                                </span>
                                                <div>
                                                    <p className="text-[11px] font-bold">{doc.filename}</p>
                                                    <p className="text-[10px] text-slate-500">{doc.status} • {doc.doc_type} • {doc.timestamp}</p>
                                                </div>
                                            </div>
                                            <span className="text-[10px] font-mono text-slate-500">{doc.integrity_hash}</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Latest Extraction Preview */}
                            {app.latestExtraction && (
                                <div className="mt-6 p-4 bg-primary/5 border border-primary/10 rounded-lg">
                                    <h4 className="text-xs font-bold text-primary uppercase mb-2">Latest Extraction</h4>
                                    <div className="grid grid-cols-3 gap-4">
                                        {Object.entries(app.latestExtraction.financials).map(([k, v]) => (
                                            <div key={k}>
                                                <p className="text-[10px] text-slate-500 uppercase">{k.replace(/_/g, ' ')}</p>
                                                <p className="text-sm font-bold">{String(v)}</p>
                                            </div>
                                        ))}
                                    </div>
                                    {app.latestExtraction.flags.length > 0 && (
                                        <div className="mt-3 pt-3 border-t border-primary/10">
                                            <p className="text-[10px] text-amber-500 font-bold uppercase mb-1">Flags</p>
                                            {app.latestExtraction.flags.map((f, i) => (
                                                <p key={i} className="text-xs text-slate-400">• {f}</p>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </section>
                </div>

                {/* Ingestion Timeline */}
                <section className="bg-white dark:bg-surface-dark rounded-xl border border-primary/10 overflow-hidden">
                    <div className="p-6 border-b border-primary/10 flex items-center justify-between">
                        <h3 className="text-lg text-primary font-semibold">Ingestion Timeline</h3>
                        <span className="text-xs text-slate-500">{app.ingestedDocs.length} documents processed</span>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-primary/5 text-slate-400 uppercase text-[10px] font-bold tracking-widest">
                                <tr>
                                    <th className="px-6 py-4">Data Source</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4">Timestamp</th>
                                    <th className="px-6 py-4">Integrity Hash</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-primary/10">
                                {app.ingestedDocs.length === 0 ? (
                                    <tr><td colSpan={4} className="px-6 py-8 text-center text-slate-500 italic">No documents ingested yet. Upload files above to begin.</td></tr>
                                ) : (
                                    app.ingestedDocs.map((doc, i) => (
                                        <tr key={i} className="hover:bg-primary/5 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2">
                                                    <span className="material-symbols-outlined text-slate-400">description</span>
                                                    <span className="font-medium">{doc.filename}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${doc.status === 'verified'
                                                    ? 'bg-green-500/10 text-green-500'
                                                    : 'bg-amber-500/10 text-amber-500'
                                                    }`}>{doc.status}</span>
                                            </td>
                                            <td className="px-6 py-4 text-slate-500 text-xs">{doc.timestamp}</td>
                                            <td className="px-6 py-4 font-mono text-[10px] text-slate-500">{doc.integrity_hash}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </section>
            </div>
        </div>
    )
}
