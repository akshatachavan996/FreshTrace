import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Clock,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Download,
  Printer,
  RotateCcw,
  Shield,
  Layers,
  Search,
  Radar,
  Calendar,
  AlertOctagon,
} from 'lucide-react';
import { ClaimStatus, VerificationResponse } from '../types';
import { exportRunJsonUrl } from '../services/api';

interface ResultsDashboardProps {
  result: VerificationResponse;
  onReset: () => void;
}

export const ResultsDashboard: React.FC<ResultsDashboardProps> = ({ result, onReset }) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [expandedClaims, setExpandedClaims] = useState<Record<string, boolean>>({});
  const [searchFilter, setSearchFilter] = useState('');
  const [sortBy, setSortBy] = useState<'default' | 'score_asc' | 'score_desc' | 'risk_desc'>('default');

  const toggleClaim = (id: string) => {
    setExpandedClaims((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const expandAll = () => {
    const all: Record<string, boolean> = {};
    result.claims.forEach((c) => (all[c.id] = true));
    setExpandedClaims(all);
  };

  const collapseAll = () => {
    setExpandedClaims({});
  };

  // Filter and sort claims
  const filteredClaims = result.claims
    .filter((claim) => {
      if (filterStatus !== 'ALL' && claim.status !== filterStatus) return false;
      if (searchFilter.trim()) {
        const query = searchFilter.toLowerCase();
        return (
          claim.claim_text.toLowerCase().includes(query) ||
          claim.explanation.toLowerCase().includes(query) ||
          claim.claim_type.toLowerCase().includes(query)
        );
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'score_asc') return a.freshness_score - b.freshness_score;
      if (sortBy === 'score_desc') return b.freshness_score - a.freshness_score;
      if (sortBy === 'risk_desc') return (b.temporal_risk_score || 0) - (a.temporal_risk_score || 0);
      return 0;
    });

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-brand-emerald';
    if (score >= 45) return 'text-amber-400';
    return 'text-rose-400';
  };

  const getScoreBg = (score: number) => {
    if (score >= 75) return 'bg-emerald-500/10 border-emerald-500/30';
    if (score >= 45) return 'bg-amber-500/10 border-amber-500/30';
    return 'bg-rose-500/10 border-rose-500/30';
  };

  const getRiskBadge = (risk: number) => {
    if (risk >= 70) {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/15 text-rose-300 border border-rose-500/30">
          <AlertOctagon className="w-3 h-3 text-rose-400" />
          <span>High Risk ({risk})</span>
        </span>
      );
    }
    if (risk >= 40) {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/15 text-amber-300 border border-amber-500/30">
          <Radar className="w-3 h-3 text-amber-400" />
          <span>Med Risk ({risk})</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
        <Shield className="w-3 h-3 text-emerald-400" />
        <span>Low Risk ({risk})</span>
      </span>
    );
  };

  const getStatusBadge = (status: ClaimStatus) => {
    switch (status) {
      case 'LIKELY_CURRENT':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Likely Current</span>
          </span>
        );
      case 'POTENTIALLY_STALE':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Potentially Stale</span>
          </span>
        );
      case 'CONFLICTING_EVIDENCE':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/30">
            <Layers className="w-3.5 h-3.5" />
            <span>Conflicting Evidence</span>
          </span>
        );
      case 'NOT_TIME_SENSITIVE':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/30">
            <Clock className="w-3.5 h-3.5" />
            <span>Not Time-Sensitive</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/30">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Unverified</span>
          </span>
        );
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top Action & Summary Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-dark-900 border border-dark-700">
        <div>
          <span className="text-xs font-mono text-slate-400">Run ID: {result.run_id}</span>
          <p className="text-xs text-slate-400">
            Mode: <span className="text-brand-cyan font-mono font-medium">{result.mode}</span> &bull; Verified at{' '}
            {new Date(result.created_at).toLocaleTimeString()}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href={exportRunJsonUrl(result.run_id)}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1.5 rounded-lg bg-dark-800 hover:bg-dark-700 text-xs font-medium text-slate-300 border border-dark-600 transition-colors flex items-center space-x-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </a>
          <button
            onClick={handlePrint}
            className="px-3 py-1.5 rounded-lg bg-dark-800 hover:bg-dark-700 text-xs font-medium text-slate-300 border border-dark-600 transition-colors flex items-center space-x-1.5"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
          <button
            onClick={onReset}
            className="px-4 py-1.5 rounded-lg bg-brand-cyan hover:bg-brand-teal text-dark-950 font-bold text-xs transition-colors flex items-center space-x-1"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Verify Another</span>
          </button>
        </div>
      </div>

      {/* Main Score Hero Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Overall Freshness Score */}
        <div className={`p-5 rounded-2xl border ${getScoreBg(result.overall_score)} flex flex-col justify-between`}>
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Freshness Score</span>
              <Shield className="w-4 h-4 text-slate-400" />
            </div>
            <div className="mt-3 flex items-baseline space-x-2">
              <span className={`text-4xl font-black ${getScoreColor(result.overall_score)}`}>
                {result.overall_score}
              </span>
              <span className="text-slate-500 font-mono text-xs">/ 100</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-300 mt-3 leading-relaxed">
            {result.overall_score >= 75
              ? 'High freshness: Strong live evidence supports current accuracy.'
              : result.overall_score >= 45
              ? 'Moderate freshness: Some claims may be stale or conflicting.'
              : 'Low freshness: Contradictory or obsolete claims detected.'}
          </p>
        </div>

        {/* Temporal Risk Radar */}
        <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Temporal Risk Radar</span>
              <Radar className="w-4 h-4 text-brand-cyan" />
            </div>
            <div className="mt-3 flex items-baseline space-x-2">
              <span className="text-4xl font-black text-white">{result.overall_temporal_risk || 50}</span>
              <span className="text-slate-500 font-mono text-xs">/ 100</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-3 leading-relaxed">
            Measures vulnerability to knowledge drift based on volatility, consequence, and evidence age.
          </p>
        </div>

        {/* Verification Confidence */}
        <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Confidence</span>
              <span className="text-xs font-mono text-brand-cyan">{result.confidence_score}%</span>
            </div>
            <div className="mt-3 flex items-baseline space-x-2">
              <span className="text-4xl font-black text-white">{result.confidence_score}</span>
              <span className="text-slate-500 font-mono text-xs">%</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 mt-3 leading-relaxed">
            Robustness of evidence volume, domain diversity, and agreement across sources.
          </p>
        </div>

        {/* Claims Breakdown Summary */}
        <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700 flex flex-col justify-between space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">Claims Breakdown</span>
          <div className="grid grid-cols-2 gap-1.5 text-xs">
            <div className="p-1.5 rounded-lg bg-dark-950 border border-dark-800 flex justify-between items-center">
              <span className="text-emerald-400 text-[11px]">Current</span>
              <span className="font-mono font-bold text-white text-[11px]">{result.likely_current_count}</span>
            </div>
            <div className="p-1.5 rounded-lg bg-dark-950 border border-dark-800 flex justify-between items-center">
              <span className="text-rose-400 text-[11px]">Stale</span>
              <span className="font-mono font-bold text-white text-[11px]">{result.potentially_stale_count}</span>
            </div>
            <div className="p-1.5 rounded-lg bg-dark-950 border border-dark-800 flex justify-between items-center">
              <span className="text-purple-400 text-[11px]">Conflict</span>
              <span className="font-mono font-bold text-white text-[11px]">{result.conflicting_count}</span>
            </div>
            <div className="p-1.5 rounded-lg bg-dark-950 border border-dark-800 flex justify-between items-center">
              <span className="text-slate-400 text-[11px]">Unverified</span>
              <span className="font-mono font-bold text-white text-[11px]">{result.unverified_count}</span>
            </div>
          </div>
          <div className="text-[10px] text-slate-500">
            Total {result.total_claims} claim(s) isolated from target text.
          </div>
        </div>
      </div>

      {/* Synthesis Report Summary */}
      <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700 space-y-2">
        <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-brand-cyan">
          Verification Synthesis
        </h3>
        <p className="text-sm text-slate-200 leading-relaxed font-sans">{result.report_summary}</p>
        {result.question && (
          <p className="text-xs text-slate-400 pt-1">
            <span className="font-medium text-slate-300">Prompt context:</span> "{result.question}"
          </p>
        )}
      </div>

      {/* Claims Section */}
      <div className="space-y-4">
        {/* Filter and Search Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Status Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <button
              onClick={() => setFilterStatus('ALL')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                filterStatus === 'ALL'
                  ? 'bg-brand-cyan text-dark-950 font-bold'
                  : 'bg-dark-850 text-slate-400 hover:text-white border border-dark-700'
              }`}
            >
              All ({result.claims.length})
            </button>
            <button
              onClick={() => setFilterStatus('POTENTIALLY_STALE')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                filterStatus === 'POTENTIALLY_STALE'
                  ? 'bg-rose-500 text-white font-bold'
                  : 'bg-dark-850 text-rose-300/80 hover:text-rose-200 border border-dark-700'
              }`}
            >
              Stale ({result.potentially_stale_count})
            </button>
            <button
              onClick={() => setFilterStatus('CONFLICTING_EVIDENCE')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                filterStatus === 'CONFLICTING_EVIDENCE'
                  ? 'bg-purple-600 text-white font-bold'
                  : 'bg-dark-850 text-purple-300/80 hover:text-purple-200 border border-dark-700'
              }`}
            >
              Conflicting ({result.conflicting_count})
            </button>
            <button
              onClick={() => setFilterStatus('LIKELY_CURRENT')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                filterStatus === 'LIKELY_CURRENT'
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'bg-dark-850 text-emerald-300/80 hover:text-emerald-200 border border-dark-700'
              }`}
            >
              Current ({result.likely_current_count})
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-2 py-1.5 rounded-lg bg-dark-950 border border-dark-700 text-xs text-slate-300 focus:outline-none"
            >
              <option value="default">Sort: Default</option>
              <option value="score_desc">Freshness: High to Low</option>
              <option value="score_asc">Freshness: Low to High (Stale First)</option>
              <option value="risk_desc">Temporal Risk: High to Low</option>
            </select>

            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search claims..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="pl-8 pr-3 py-1.5 rounded-lg bg-dark-950 border border-dark-700 text-xs text-slate-200 focus:outline-none focus:border-brand-cyan"
              />
            </div>

            <button
              onClick={expandAll}
              className="text-[11px] text-slate-400 hover:text-white px-2 py-1 rounded border border-dark-700 bg-dark-850"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="text-[11px] text-slate-400 hover:text-white px-2 py-1 rounded border border-dark-700 bg-dark-850"
            >
              Collapse All
            </button>
          </div>
        </div>

        {/* Claim Cards List with Freshness Passport */}
        <div className="space-y-4">
          {filteredClaims.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-dark-900 border border-dark-800 text-slate-400 text-xs">
              No claims match the selected filter.
            </div>
          ) : (
            filteredClaims.map((claim) => {
              const isExpanded = !!expandedClaims[claim.id];
              return (
                <div
                  key={claim.id}
                  className="rounded-2xl bg-dark-900 border border-dark-700/80 hover:border-dark-600 transition-all overflow-hidden"
                >
                  {/* Passport Header Strip */}
                  <div className="bg-dark-950/80 px-5 py-2 border-b border-dark-800 flex items-center justify-between text-[11px] font-mono">
                    <div className="flex items-center space-x-2 text-slate-400">
                      <Shield className="w-3 h-3 text-brand-cyan" />
                      <span className="uppercase tracking-widest text-slate-400 font-bold">FRESHNESS PASSPORT</span>
                      <span className="text-slate-600">&bull;</span>
                      <span className="text-slate-500">ID: {claim.id.slice(0, 8)}</span>
                    </div>

                    <div className="flex items-center space-x-3">
                      {claim.recheck_interval_days && (
                        <span className="text-slate-400 flex items-center space-x-1">
                          <Calendar className="w-3 h-3 text-slate-500" />
                          <span>Recheck: ~{claim.recheck_interval_days}d</span>
                        </span>
                      )}
                      {getRiskBadge(claim.temporal_risk_score || 50)}
                    </div>
                  </div>

                  {/* Claim Card Body */}
                  <div
                    onClick={() => toggleClaim(claim.id)}
                    className="p-5 cursor-pointer flex flex-col sm:flex-row sm:items-start justify-between gap-4"
                  >
                    <div className="space-y-2 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {getStatusBadge(claim.status)}
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-dark-950 border border-dark-700 text-slate-400">
                          {claim.claim_type}
                        </span>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded-md border ${
                            claim.volatility === 'HIGH'
                              ? 'bg-rose-500/10 text-rose-300 border-rose-500/20'
                              : claim.volatility === 'MEDIUM'
                              ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                              : 'bg-blue-500/10 text-blue-300 border-blue-500/20'
                          }`}
                        >
                          {claim.volatility} Volatility
                        </span>
                      </div>

                      <p className="text-sm font-semibold text-white leading-relaxed">
                        "{claim.claim_text}"
                      </p>
                    </div>

                    <div className="flex items-center space-x-4 self-end sm:self-center">
                      <div className="text-right">
                        <div className="text-[10px] font-mono text-slate-400">Freshness</div>
                        <div className={`text-lg font-black ${getScoreColor(claim.freshness_score)}`}>
                          {claim.freshness_score}
                          <span className="text-xs text-slate-500 font-normal">/100</span>
                        </div>
                      </div>

                      <button className="p-1 rounded-lg bg-dark-800 text-slate-400 hover:text-white">
                        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Evidence & Sources View */}
                  {isExpanded && (
                    <div className="p-5 border-t border-dark-800 bg-dark-950 space-y-4 text-xs">
                      {/* Analysis & Query */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-3.5 rounded-xl bg-dark-900 border border-dark-800 space-y-1">
                          <span className="font-mono text-[10px] text-slate-400 uppercase">Analysis Explanation</span>
                          <p className="text-slate-300 leading-relaxed">{claim.explanation}</p>
                        </div>
                        <div className="p-3.5 rounded-xl bg-dark-900 border border-dark-800 space-y-1">
                          <span className="font-mono text-[10px] text-slate-400 uppercase">Search Query Used</span>
                          <p className="text-brand-cyan font-mono text-[11px]">{claim.search_query}</p>
                          <span className="font-mono text-[10px] text-slate-400 uppercase pt-1 block">
                            Evidence Summary
                          </span>
                          <p className="text-slate-300 leading-relaxed">{claim.evidence_summary}</p>
                        </div>
                      </div>

                      {/* Sources Header */}
                      <div className="space-y-2 pt-2">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[11px] uppercase tracking-wider text-slate-400">
                            Retrieved Web Sources ({claim.sources.length})
                          </span>
                          <span className="text-[10px] text-slate-500">
                            Credibility heuristics: institutional domains, official docs, news
                          </span>
                        </div>

                        {claim.sources.length === 0 ? (
                          <div className="p-4 rounded-xl bg-dark-900 text-slate-400 text-center">
                            No web sources were found or required for this claim.
                          </div>
                        ) : (
                          <div className="space-y-2.5">
                            {claim.sources.map((src) => (
                              <div
                                key={src.id}
                                className="p-3.5 rounded-xl bg-dark-900 border border-dark-800 space-y-2"
                              >
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                  <a
                                    href={src.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-xs font-semibold text-brand-cyan hover:underline flex items-center space-x-1.5"
                                  >
                                    <span>{src.title}</span>
                                    <ExternalLink className="w-3.5 h-3.5" />
                                  </a>

                                  <div className="flex items-center space-x-2">
                                    {src.supports_claim === true ? (
                                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                        Supports
                                      </span>
                                    ) : src.supports_claim === false ? (
                                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                                        Contradicts
                                      </span>
                                    ) : (
                                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-500/10 text-slate-400 border border-slate-500/20">
                                        Neutral
                                      </span>
                                    )}

                                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-dark-950 border border-dark-700 text-slate-400">
                                      Domain: {src.domain}
                                    </span>

                                    <span
                                      className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                                        src.credibility_heuristic === 'HIGH'
                                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                                          : 'bg-slate-500/10 text-slate-300 border-slate-500/20'
                                      }`}
                                    >
                                      {src.credibility_heuristic} Credibility
                                    </span>

                                    {src.published_date && (
                                      <span className="text-[10px] font-mono text-slate-500">
                                        Date: {src.published_date}
                                      </span>
                                    )}
                                  </div>
                                </div>

                                <p className="text-slate-300 text-xs leading-relaxed bg-dark-950/70 p-2.5 rounded-lg border border-dark-800">
                                  {src.snippet}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
