import React, { useEffect, useState } from 'react';
import { ComparisonResult, HistoryItem, VerificationResponse } from '../types';
import { compareRuns, deleteRun, exportRunJsonUrl, fetchHistory, fetchRunDetails } from '../services/api';
import { Trash2, ArrowRight, AlertCircle, GitCompare, Download, Calendar, Shield, X, CheckCircle, AlertTriangle } from 'lucide-react';

interface HistoryViewProps {
  onSelectRun: (run: VerificationResponse) => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({ onSelectRun }) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Compare selection state
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  const loadHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const items = await fetchHistory();
      setHistory(items);
    } catch (err: any) {
      setError(err.message || 'Failed to load history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const toggleSelectForCompare = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setSelectedForCompare((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      }
      if (prev.length >= 2) {
        // Keep the second one and add new
        return [prev[1], id];
      }
      return [...prev, id];
    });
  };

  const handleRunCompare = async () => {
    if (selectedForCompare.length !== 2) return;
    setIsComparing(true);
    try {
      const result = await compareRuns(selectedForCompare[0], selectedForCompare[1]);
      setComparisonResult(result);
    } catch (err: any) {
      alert(`Comparison failed: ${err.message}`);
    } finally {
      setIsComparing(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this verification record?')) return;
    try {
      await deleteRun(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
      setSelectedForCompare((prev) => prev.filter((item) => item !== id));
    } catch (err: any) {
      alert(`Error deleting record: ${err.message}`);
    }
  };

  const handleOpen = async (id: string) => {
    try {
      const details = await fetchRunDetails(id);
      onSelectRun(details);
    } catch (err: any) {
      alert(`Error loading run details: ${err.message}`);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-dark-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Verification History &amp; Change Detection</h2>
          <p className="text-xs text-slate-400">
            Audit past verification runs, export JSON reports, or compare two runs to detect knowledge drift.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {selectedForCompare.length === 2 && (
            <button
              onClick={handleRunCompare}
              disabled={isComparing}
              className="px-3 py-1.5 rounded-lg bg-brand-cyan hover:bg-brand-teal text-dark-950 font-bold text-xs transition-colors flex items-center space-x-1.5 shadow-lg shadow-brand-cyan/10"
            >
              <GitCompare className="w-3.5 h-3.5" />
              <span>{isComparing ? 'Comparing...' : 'Compare Selected (2)'}</span>
            </button>
          )}

          <button
            onClick={loadHistory}
            className="px-3 py-1.5 rounded-lg bg-dark-850 hover:bg-dark-800 border border-dark-700 text-xs text-slate-300"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Comparison Modal / Diff Drawer */}
      {comparisonResult && (
        <div className="p-6 rounded-2xl bg-dark-900 border border-brand-cyan/40 shadow-2xl space-y-6 animate-in fade-in">
          <div className="flex items-center justify-between border-b border-dark-800 pb-3">
            <div className="flex items-center space-x-2">
              <GitCompare className="w-5 h-5 text-brand-cyan" />
              <h3 className="font-bold text-white text-base">Run Comparison &amp; Change Detection</h3>
            </div>
            <button
              onClick={() => setComparisonResult(null)}
              className="p-1 rounded-lg bg-dark-800 hover:bg-dark-700 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Diff Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-dark-950 border border-dark-800 space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400">Score Delta</span>
              <div className="text-2xl font-black text-white">
                <span className={comparisonResult.score_delta >= 0 ? 'text-brand-emerald' : 'text-rose-400'}>
                  {comparisonResult.score_delta > 0 ? `+${comparisonResult.score_delta}` : comparisonResult.score_delta}
                </span>
                <span className="text-xs text-slate-500 font-normal"> pts</span>
              </div>
              <p className="text-[10px] text-slate-400">
                Run A: {comparisonResult.overall_score_a} &rarr; Run B: {comparisonResult.overall_score_b}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-dark-950 border border-dark-800 space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400">Temporal Risk Shift</span>
              <div className="text-2xl font-black text-white">
                <span className={comparisonResult.risk_delta <= 0 ? 'text-brand-emerald' : 'text-rose-400'}>
                  {comparisonResult.risk_delta > 0 ? `+${comparisonResult.risk_delta}` : comparisonResult.risk_delta}
                </span>
                <span className="text-xs text-slate-500 font-normal"> pts</span>
              </div>
              <p className="text-[10px] text-slate-400">
                Risk A: {comparisonResult.temporal_risk_a} &rarr; Risk B: {comparisonResult.temporal_risk_b}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-dark-950 border border-dark-800 space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-400">Claims Compared</span>
              <div className="text-2xl font-black text-white">{comparisonResult.claims_diff.length}</div>
              <p className="text-[10px] text-slate-400">
                {comparisonResult.claims_diff.filter((d) => d.status_changed).length} status change(s) detected
              </p>
            </div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed font-mono bg-dark-950 p-3 rounded-xl border border-dark-800">
            {comparisonResult.summary}
          </p>

          {/* Claims Diff Table */}
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Claim-Level Changes
            </span>
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {comparisonResult.claims_diff.map((diff, idx) => (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border ${
                    diff.status_changed
                      ? 'bg-amber-950/20 border-amber-500/30'
                      : 'bg-dark-950 border-dark-800'
                  } space-y-2 text-xs`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-white font-medium leading-relaxed">"{diff.claim_text}"</p>
                    {diff.status_changed ? (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex-shrink-0">
                        Status Changed
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-dark-900 text-slate-500 flex-shrink-0">
                        Unchanged
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 font-mono">
                    <span>
                      Status: <span className="text-slate-300">{diff.status_a}</span> &rarr;{' '}
                      <span className={diff.status_changed ? 'text-amber-300 font-bold' : 'text-slate-300'}>
                        {diff.status_b}
                      </span>
                    </span>
                    <span>
                      Freshness: {diff.freshness_a} &rarr; {diff.freshness_b}
                    </span>
                    <span>
                      Sources: {diff.sources_count_a} &rarr; {diff.sources_count_b}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* History Items List */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 font-mono text-xs">Loading verification history...</div>
      ) : history.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-dark-900 border border-dark-800 text-slate-400 text-sm">
          No verification history found. Run a check from the Workspace to record verification runs.
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => {
            const isSelected = selectedForCompare.includes(item.id);
            return (
              <div
                key={item.id}
                onClick={() => handleOpen(item.id)}
                className={`p-5 rounded-2xl bg-dark-900 border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer group ${
                  isSelected ? 'border-brand-cyan shadow-lg shadow-brand-cyan/10' : 'border-dark-700/80 hover:border-dark-600'
                }`}
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    {/* Compare checkbox */}
                    <button
                      type="button"
                      onClick={(e) => toggleSelectForCompare(e, item.id)}
                      title="Select for comparison"
                      className={`px-2 py-0.5 rounded text-[10px] font-mono border transition-colors ${
                        isSelected
                          ? 'bg-brand-cyan text-dark-950 font-bold border-brand-cyan'
                          : 'bg-dark-950 text-slate-400 border-dark-700 hover:text-white'
                      }`}
                    >
                      {isSelected ? 'Selected' : '+ Compare'}
                    </button>

                    <span className="font-mono text-slate-500 flex items-center space-x-1">
                      <Calendar className="w-3 h-3 text-slate-600" />
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                    </span>

                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-dark-950 border border-dark-700 text-slate-400">
                      {item.mode}
                    </span>

                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        item.status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : 'bg-amber-500/10 text-amber-400'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>

                  <p className="text-sm font-medium text-white group-hover:text-brand-cyan transition-colors line-clamp-2">
                    "{item.original_answer_snippet}"
                  </p>

                  {item.question && (
                    <p className="text-xs text-slate-400">
                      <span className="text-slate-500 font-mono">Prompt:</span> {item.question}
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-4 self-end sm:self-center">
                  <div className="text-right">
                    <div className="text-[10px] font-mono text-slate-500">Freshness</div>
                    <div
                      className={`text-xl font-black ${
                        item.overall_score >= 75
                          ? 'text-brand-emerald'
                          : item.overall_score >= 45
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {item.overall_score}
                      <span className="text-xs font-normal text-slate-500">/100</span>
                    </div>
                  </div>

                  {/* Export Link */}
                  <a
                    href={exportRunJsonUrl(item.id)}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    title="Export JSON"
                    className="p-2 rounded-lg bg-dark-850 hover:bg-dark-800 text-slate-400 hover:text-white border border-dark-700 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                  </a>

                  {/* Delete Button */}
                  <button
                    onClick={(e) => handleDelete(e, item.id)}
                    title="Delete record"
                    className="p-2 rounded-lg bg-dark-850 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-dark-700 hover:border-rose-500/30 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <ArrowRight className="w-5 h-5 text-slate-500 group-hover:text-brand-cyan group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
