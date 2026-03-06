/**
 * Risk Intelligence Graph — no secondary sidebar, clean layout.
 */

import { useApp } from './AppContext'

export default function RiskIntelligenceView() {
    const app = useApp()
    const insights = app.researchInsights

    const handleDeepScan = async () => {
        await app.triggerResearch(app.entityName || undefined, app.sector || undefined)
    }

    return (
        <div className="flex flex-col flex-1 overflow-hidden">
            {/* Toast */}
            {app.toastMessage && (
                <div className="fixed top-4 right-4 z-50 bg-primary text-background-dark px-6 py-3 rounded-lg shadow-2xl text-sm font-bold animate-pulse">
                    {app.toastMessage}
                </div>
            )}

            {/* Top bar with entity info + actions */}
            <div className="flex items-center justify-between px-8 py-4 border-b border-primary/10 bg-primary/5 shrink-0">
                <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                        <span className="material-symbols-outlined">account_tree</span>
                    </div>
                    <div>
                        <h2 className="text-lg font-bold">{app.entityName || 'No Entity Configured'}</h2>
                        <p className="text-xs text-slate-500">{app.sector || 'Corporate Credit'} • {insights.length} insights found</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span className={`flex h-2 w-2 rounded-full ${insights.length > 0 ? 'bg-emerald-500' : 'bg-slate-500'}`}></span>
                        {insights.length > 0 ? 'Research Complete' : 'Awaiting Research'}
                    </div>
                    <button
                        onClick={handleDeepScan}
                        disabled={app.isLoading.research}
                        className="bg-primary text-background-dark px-5 py-2 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-primary/90 transition-colors disabled:opacity-50 shadow-lg"
                    >
                        <span className="material-symbols-outlined text-lg">
                            {app.isLoading.research ? 'hourglass_empty' : 'search'}
                        </span>
                        {app.isLoading.research ? 'Scanning...' : 'Run Research Agent'}
                    </button>
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
                {/* Main: Graph Visualization */}
                <main className="flex-1 flex flex-col overflow-hidden relative">
                    <div className="relative flex-1 bg-zinc-100 dark:bg-[#12110e] overflow-hidden">
                        {/* Abstract Graph Elements or Real Graph */}
                        {app.graphAnalysis && app.graphAnalysis.visualization_base64 ? (
                            <div className="absolute inset-0 p-8 flex flex-col items-center justify-center bg-black/50">
                                <img src={`data:image/png;base64,${app.graphAnalysis.visualization_base64}`} alt="Transaction Graph" className="w-full h-full object-contain rounded-xl mix-blend-screen opacity-80" />
                            </div>
                        ) : (
                            <div className="absolute inset-0 opacity-40">
                                <div className="absolute top-1/4 left-1/3 w-2 h-2 rounded-full bg-red-600 graph-glow-crimson"></div>
                                <div className="absolute top-1/4 left-1/3 w-32 h-[2px] bg-red-600/40 rotate-12"></div>
                                <div className="absolute top-[30%] left-[45%] w-4 h-4 rounded-full border-2 border-amber-500 graph-glow-amber"></div>
                                <div className="absolute top-[30%] left-[45%] w-24 h-[2px] bg-amber-500/30 -rotate-45"></div>
                                <div className="absolute top-[55%] left-[40%]">
                                    <div className="relative w-40 h-40 rounded-full border border-amber-500/40 border-dashed"></div>
                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-amber-500 rounded-full"></div>
                                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-amber-500 rounded-full"></div>
                                </div>
                            </div>
                        )}

                        {/* Filters overlay */}
                        {insights.length > 0 && (
                            <div className="absolute top-4 left-4 bg-background-dark/80 backdrop-blur p-3 rounded-lg border border-primary/20 shadow-xl">
                                <h4 className="text-xs font-bold text-primary mb-2 uppercase">Active Filters</h4>
                                <div className="flex gap-2 flex-wrap">
                                    <span className="px-2 py-1 bg-red-600/20 text-red-500 text-[10px] font-bold rounded border border-red-600/30">High Risk Nodes</span>
                                    <span className="px-2 py-1 bg-primary/20 text-primary text-[10px] font-bold rounded border border-primary/30">Suspicious Cycles</span>
                                </div>
                            </div>
                        )}

                        {/* Status Bar */}
                        <div className="absolute bottom-4 left-4 bg-background-dark/80 backdrop-blur px-4 py-2 rounded-full border border-primary/20 text-xs flex items-center gap-3">
                            <span className={`flex h-2 w-2 rounded-full ${insights.length > 0 ? 'bg-emerald-500' : 'bg-slate-500'}`}></span>
                            <span className="text-slate-400">Entity: <strong className="text-slate-900 dark:text-slate-100">{app.entityName || 'Not configured'}</strong></span>
                            <span className="text-slate-600">|</span>
                            <span className="text-slate-400">Insights: <strong className="text-slate-900 dark:text-slate-100">{insights.length}</strong></span>
                            {app.graphAnalysis && (
                                <>
                                    <span className="text-slate-600">|</span>
                                    <span className="text-slate-400">Nodes: <strong className="text-slate-900 dark:text-slate-100">{app.graphAnalysis.nodes?.length || 0}</strong></span>
                                    <span className="text-slate-600">|</span>
                                    <span className="text-slate-400">Risk Cycles: <strong className="text-slate-900 dark:text-slate-100">{app.graphAnalysis.cycle_count || 0}</strong></span>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Bottom Console: Market & Legal Intel */}
                    <div className="h-1/3 border-t border-primary/20 bg-background-light dark:bg-background-dark flex flex-col shrink-0">
                        <div className="flex items-center justify-between px-6 py-3 border-b border-primary/10 bg-primary/5">
                            <div className="flex items-center gap-3">
                                <span className="material-symbols-outlined text-primary">news</span>
                                <h3 className="text-sm font-bold uppercase tracking-wider">Market &amp; Legal Intelligence</h3>
                            </div>
                            <div className="flex items-center gap-4 text-xs">
                                {app.isLoading.research && <span className="text-primary animate-pulse">Searching...</span>}
                                <button
                                    onClick={handleDeepScan}
                                    disabled={app.isLoading.research}
                                    className="text-primary hover:underline font-bold disabled:opacity-50"
                                >
                                    Refresh Feed
                                </button>
                            </div>
                        </div>
                        <div className="flex-1 overflow-x-auto p-4 flex gap-4">
                            {insights.length === 0 ? (
                                <div className="flex-1 flex items-center justify-center text-slate-500 text-sm italic">
                                    Click "Run Research Agent" to scan for market intelligence, litigation, and sector risks.
                                </div>
                            ) : (
                                insights.map((insight, i) => (
                                    <div key={insight.id || i} className="min-w-[320px] bg-primary/5 rounded-xl border border-primary/10 p-4 flex flex-col gap-3">
                                        <div className="flex justify-between items-start">
                                            <span className="px-2 py-0.5 bg-amber-500/10 text-amber-500 text-[10px] font-bold rounded uppercase">
                                                {insight.source}
                                            </span>
                                            <span className="text-[10px] text-slate-500">{insight.timestamp}</span>
                                        </div>
                                        <p className="text-sm font-bold leading-tight">{insight.title}</p>
                                        <p className="text-xs text-slate-400 line-clamp-3">{insight.content}</p>
                                        <div className="mt-auto pt-3 border-t border-primary/10 flex items-center justify-between">
                                            <div className="flex flex-col gap-1 w-2/3">
                                                <div className="flex justify-between text-[10px]">
                                                    <span>Sentiment</span>
                                                    <span className="text-primary">{insight.sentiment}</span>
                                                </div>
                                                <div className="h-1 w-full bg-slate-200 dark:bg-slate-800 rounded-full">
                                                    <div className="h-full bg-primary rounded-full" style={{ width: '50%' }}></div>
                                                </div>
                                            </div>
                                            <button className="material-symbols-outlined text-primary p-1 rounded-lg hover:bg-primary/20">open_in_new</button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </main>

                {/* Right Panel: Research Summary */}
                <aside className="w-80 border-l border-primary/20 bg-background-light dark:bg-background-dark flex flex-col shrink-0">
                    <div className="p-4 border-b border-primary/10">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-slate-900 dark:text-slate-100">Research Summary</h3>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${insights.length > 0 ? 'bg-primary text-background-dark' : 'bg-slate-700 text-slate-400'}`}>
                                {insights.length} Found
                            </span>
                        </div>
                        {insights.length > 0 && (
                            <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                                <p className="text-[10px] text-amber-500 font-bold uppercase mb-1 flex items-center gap-1">
                                    <span className="material-symbols-outlined text-xs">warning</span> Key Finding
                                </p>
                                <p className="text-xs font-bold text-slate-900 dark:text-slate-200">{insights[0]?.title}</p>
                                <p className="text-[10px] text-slate-400 mt-1 line-clamp-2">{insights[0]?.content}</p>
                            </div>
                        )}
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                        {insights.map((insight, i) => (
                            <div key={i} className="p-3 bg-primary/5 rounded-lg border border-primary/10">
                                <p className="text-xs font-bold text-slate-900 dark:text-slate-200 mb-1">{insight.title}</p>
                                <p className="text-[10px] text-slate-400 line-clamp-3">{insight.content}</p>
                            </div>
                        ))}
                    </div>

                    {/* AI Assistant */}
                    <div className="p-4 bg-background-dark/50 border-t border-primary/10">
                        <div className="flex flex-col gap-3">
                            <div className="flex items-center gap-2">
                                <span className="material-symbols-outlined text-primary text-sm">smart_toy</span>
                                <span className="text-[10px] font-bold text-primary uppercase">Research Assistant AI</span>
                            </div>
                            <div className="bg-background-dark rounded-lg p-3 text-[11px] text-slate-400 border border-primary/10">
                                {insights.length > 0
                                    ? `Found ${insights.length} intelligence items for "${app.entityName || 'entity'}". Ready for deep scan or Five Cs analysis.`
                                    : 'Configure an entity and run the research agent to begin intelligence gathering.'}
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleDeepScan}
                                    disabled={app.isLoading.research}
                                    className="flex-1 bg-primary text-background-dark text-[10px] font-bold py-1.5 rounded hover:opacity-90 disabled:opacity-50"
                                >
                                    {app.isLoading.research ? 'Scanning...' : 'Deep Scan'}
                                </button>
                                <button className="flex-1 bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-[10px] font-bold py-1.5 rounded hover:text-slate-900 dark:hover:text-white">
                                    Dismiss
                                </button>
                            </div>
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    )
}
