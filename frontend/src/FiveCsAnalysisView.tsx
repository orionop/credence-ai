/**
 * Five Cs Analysis & Scoring Matrix — fully wired to backend.
 * Calls GET /api/v1/five-cs/{session_id} and renders dynamic scores.
 */

import { useApp } from './AppContext'

const CS_META = [
    { key: 'character', icon: 'person_search', label: 'Character' },
    { key: 'capacity', icon: 'trending_up', label: 'Capacity' },
    { key: 'capital', icon: 'account_balance_wallet', label: 'Capital' },
    { key: 'collateral', icon: 'domain', label: 'Collateral' },
    { key: 'conditions', icon: 'public', label: 'Conditions' },
] as const

// Compute radar chart polygon points from scores (0-100 scale)
function radarPoints(scores: number[], cx = 200, cy = 200, maxR = 150): string {
    const n = scores.length
    return scores.map((s, i) => {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2
        const r = (s / 100) * maxR
        return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`
    }).join(' ')
}

function axisEndpoint(i: number, n: number, cx = 200, cy = 200, r = 150): [number, number] {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)]
}

function labelPos(i: number, n: number, cx = 200, cy = 200, r = 175): { x: number; y: number; anchor: string } {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2
    const x = cx + r * Math.cos(angle)
    const y = cy + r * Math.sin(angle)
    const anchor = x < cx - 10 ? 'end' : x > cx + 10 ? 'start' : 'middle'
    return { x, y, anchor }
}


export default function FiveCsAnalysisView() {
    const app = useApp()
    const scores = app.fiveCsScores

    const handleComputeScores = async () => {
        await app.computeFiveCs()
    }

    // Build score values
    const scoreValues = CS_META.map(c => {
        if (!scores) return 50
        const cs = scores[c.key as keyof typeof scores]
        return typeof cs === 'object' && cs && 'score' in cs ? (cs as any).score : 50
    })
    const overallScore = scores?.overall_score ?? 0

    return (
        <div className="flex-1 overflow-y-auto p-8">
            {/* Toast */}
            {app.toastMessage && (
                <div className="fixed top-4 right-4 z-50 bg-primary text-background-dark px-6 py-3 rounded-lg shadow-2xl text-sm font-bold animate-pulse">
                    {app.toastMessage}
                </div>
            )}

            {/* Error */}
            {app.errors.fivecs && (
                <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-500 flex items-center justify-between">
                    <span>{app.errors.fivecs}</span>
                    <button onClick={() => app.clearError('fivecs')} className="material-symbols-outlined text-sm">close</button>
                </div>
            )}

            <div className="grid grid-cols-12 gap-8 max-w-7xl mx-auto">
                {/* Left Column */}
                <div className="col-span-12 lg:col-span-8 space-y-8">
                    {/* Radar Chart */}
                    <div className="bg-primary/5 border border-primary/10 rounded-xl p-8 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-6 opacity-20">
                            <span className="material-symbols-outlined text-8xl text-primary">hub</span>
                        </div>
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">Scoring Matrix Radar</h3>
                                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                    {app.entityName || 'Multi-dimensional risk assessment'}
                                </p>
                            </div>
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={handleComputeScores}
                                    disabled={app.isLoading.fivecs}
                                    className="bg-primary text-background-dark px-5 py-2 rounded-lg text-sm font-bold flex items-center gap-2 hover:bg-primary/90 transition-colors disabled:opacity-50"
                                >
                                    <span className="material-symbols-outlined text-lg">
                                        {app.isLoading.fivecs ? 'hourglass_empty' : 'analytics'}
                                    </span>
                                    {app.isLoading.fivecs ? 'Computing...' : 'Compute Five Cs'}
                                </button>
                                <div className="text-right">
                                    <div className="text-4xl font-black text-primary">
                                        {overallScore || '—'}<span className="text-lg text-slate-500">/100</span>
                                    </div>
                                    <div className="text-[10px] font-bold text-primary uppercase">
                                        {scores?.credit_rating || 'Awaiting Analysis'}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-center items-center py-4">
                            <svg className="drop-shadow-2xl" height="400" viewBox="0 0 400 400" width="400">
                                {/* Grid rings */}
                                {[0.33, 0.66, 1].map((scale, ri) => (
                                    <polygon
                                        key={ri}
                                        className="fill-none"
                                        points={radarPoints([100 * scale, 100 * scale, 100 * scale, 100 * scale, 100 * scale])}
                                        stroke="rgba(197,169,129,0.2)"
                                        strokeWidth="1"
                                    />
                                ))}
                                {/* Axes */}
                                {CS_META.map((_, i) => {
                                    const [ex, ey] = axisEndpoint(i, 5)
                                    return <line key={i} stroke="rgba(197,169,129,0.2)" strokeWidth="1" x1="200" y1="200" x2={ex} y2={ey} />
                                })}
                                {/* Data polygon */}
                                <polygon
                                    fill="rgba(197,169,129,0.15)"
                                    points={radarPoints(scoreValues)}
                                    stroke="#c5a981"
                                    strokeWidth="2"
                                    className="transition-all duration-700"
                                />
                                {/* Score dots */}
                                {scoreValues.map((s, i) => {
                                    const angle = (Math.PI * 2 * i) / 5 - Math.PI / 2
                                    const r = (s / 100) * 150
                                    const x = 200 + r * Math.cos(angle)
                                    const y = 200 + r * Math.sin(angle)
                                    return <circle key={i} cx={x} cy={y} r="4" fill="#c5a981" />
                                })}
                                {/* Labels */}
                                {CS_META.map((c, i) => {
                                    const { x, y, anchor } = labelPos(i, 5)
                                    return (
                                        <text key={c.key} className="fill-primary text-[12px] font-bold" textAnchor={anchor} x={x} y={y}>
                                            {c.label.toUpperCase()} ({scoreValues[i]})
                                        </text>
                                    )
                                })}
                            </svg>
                        </div>
                    </div>

                    {/* Five Cs Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {CS_META.map((c, i) => {
                            const csData = scores?.[c.key as keyof typeof scores]
                            const csObj = typeof csData === 'object' && csData && 'score' in csData ? csData as any : null
                            return (
                                <div key={c.key} className="bg-primary/5 border border-primary/20 rounded-xl p-5 hover:border-primary/50 transition-all flex flex-col">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="size-10 bg-primary/20 rounded-lg flex items-center justify-center text-primary">
                                            <span className="material-symbols-outlined">{c.icon}</span>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-2xl font-black text-slate-100">{scoreValues[i]}</span>
                                            <span className="text-xs text-slate-500">/100</span>
                                        </div>
                                    </div>
                                    <h4 className="font-bold text-slate-100 uppercase text-xs tracking-widest mb-1">{c.label}</h4>
                                    <p className="text-[11px] text-slate-400 mb-4">{csObj?.summary || 'Run scoring to see analysis'}</p>
                                    <div className="mt-auto pt-4 border-t border-primary/10">
                                        <details className="group">
                                            <summary className="list-none flex items-center justify-between cursor-pointer text-xs font-bold text-primary group-open:mb-3">
                                                <span>WHY?</span>
                                                <span className="material-symbols-outlined text-sm group-open:rotate-180 transition-transform">expand_more</span>
                                            </summary>
                                            <div className="text-[13px] leading-relaxed italic text-slate-300 bg-background-dark/40 p-3 rounded">
                                                {csObj?.detail || 'Score explanation will appear after computing Five Cs analysis.'}
                                            </div>
                                        </details>
                                    </div>
                                </div>
                            )
                        })}
                        <div
                            onClick={handleComputeScores}
                            className="bg-primary/5 border border-dashed border-primary/20 rounded-xl p-5 flex flex-col items-center justify-center opacity-50 grayscale hover:opacity-100 hover:grayscale-0 transition-all cursor-pointer"
                        >
                            <span className="material-symbols-outlined text-4xl text-primary mb-2">
                                {app.isLoading.fivecs ? 'hourglass_empty' : 'refresh'}
                            </span>
                            <span className="text-xs font-bold text-primary">
                                {app.isLoading.fivecs ? 'Computing...' : 'Recompute Scores'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Right Column: Rating Panel */}
                <div className="col-span-12 lg:col-span-4 space-y-6">
                    <div className="bg-primary/5 border border-primary/10 rounded-xl p-6 sticky top-0">
                        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-6">Overall Credit Rating</h3>
                        <div className="flex items-center gap-6 mb-8">
                            <div className="size-24 rounded-full border-4 border-primary flex flex-col items-center justify-center">
                                <span className="text-3xl font-black text-slate-100">
                                    {scores?.credit_rating || '—'}
                                </span>
                                <span className="text-[10px] font-bold text-primary uppercase">
                                    {scores?.recommendation || 'Pending'}
                                </span>
                            </div>
                            <div className="flex-1">
                                <div className="text-xs font-bold text-slate-400 mb-2 uppercase">Risk Profile</div>
                                <div className="w-full h-2 bg-background-dark rounded-full overflow-hidden flex">
                                    <div className="h-full bg-green-500" style={{ width: `${Math.max(10, 100 - overallScore)}%` }}></div>
                                    <div className="h-full bg-primary" style={{ width: `${overallScore}%` }}></div>
                                </div>
                                <div className="flex justify-between mt-1">
                                    <span className="text-[8px] font-bold text-slate-500">LOW</span>
                                    <span className="text-[8px] font-bold text-slate-500">MOD</span>
                                    <span className="text-[8px] font-bold text-slate-500">HIGH</span>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-4">
                            {scores?.appraisal_summary && (
                                <div className="p-4 bg-background-dark rounded-lg border border-primary/10">
                                    <h4 className="text-xs font-bold text-primary uppercase mb-2">AI Appraisal Summary</h4>
                                    <p className="text-sm leading-relaxed text-slate-300 italic">
                                        "{scores.appraisal_summary}"
                                    </p>
                                </div>
                            )}
                            <div className="space-y-3">
                                {[
                                    { label: 'Probability of Default', value: scores?.probability_of_default || '—' },
                                    { label: 'Loss Given Default', value: scores?.loss_given_default || '—' },
                                    { label: 'Recovery Rating', value: scores?.recovery_rating || '—', color: 'text-green-500' },
                                    { label: 'Risk Premium', value: scores?.risk_premium || '—' },
                                    { label: 'Recommended Limit', value: scores?.recommended_limit || '—', color: 'text-primary' },
                                ].map((item) => (
                                    <div key={item.label} className="flex justify-between items-center text-xs">
                                        <span className="text-slate-500">{item.label}</span>
                                        <span className={`font-bold ${item.color || 'text-slate-100'}`}>{item.value}</span>
                                    </div>
                                ))}
                            </div>
                            <button
                                onClick={handleComputeScores}
                                disabled={app.isLoading.fivecs}
                                className="w-full py-3 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 rounded-lg text-sm font-bold transition-all mt-4 uppercase tracking-widest disabled:opacity-50"
                            >
                                {app.isLoading.fivecs ? 'Computing...' : 'Refresh Scoring'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
