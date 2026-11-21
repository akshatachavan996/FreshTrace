import React from 'react';
import { ShieldCheck, Cpu, Globe, Scale, AlertCircle, Radar, Clock, GitCompare } from 'lucide-react';

export const AboutModal: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4">
      {/* Header */}
      <div className="border-b border-dark-800 pb-6 space-y-2">
        <h2 className="text-2xl font-black text-white">About FreshTrace</h2>
        <p className="text-sm text-slate-300">
          An automated freshness verification engine designed for modern AI applications.
        </p>
      </div>

      {/* Problem & Solution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-dark-900 border border-dark-700 space-y-3">
          <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm">
            <AlertCircle className="w-5 h-5" />
            <span>The Stale-Answer Problem</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Large Language Models generate text with convincing authority. However, real-world data constantly shifts:
            software libraries release breaking versions, cloud pricing fluctuates, company leadership changes, and legal
            regulations evolve. Outdated training weights lead to silent hallucination of obsolete information.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-dark-900 border border-dark-700 space-y-3">
          <div className="flex items-center space-x-2 text-brand-cyan font-bold text-sm">
            <ShieldCheck className="w-5 h-5" />
            <span>The FreshTrace Solution</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            FreshTrace deconstructs answers into isolated, verifiable factual claims, estimates their volatility drift, queries
            authoritative live web sources via Tavily, and calculates transparent claim-level freshness scores, confidence metrics,
            and temporal risk radar assessments.
          </p>
        </div>
      </div>

      {/* Core Hackathon Integrations */}
      <div className="space-y-4">
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
          Core Hackathon Integrations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-2xl bg-dark-900 border border-dark-700 space-y-2">
            <div className="flex items-center space-x-2 text-white font-bold text-sm">
              <Cpu className="w-4 h-4 text-brand-cyan" />
              <span>Bifrost by Maxim AI</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Acts as the unified AI Gateway for our LLM calls. Enforces structured JSON schema extraction, handles provider
              configuration, and extracts atomic factual assertions from messy AI-generated answers.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-dark-900 border border-dark-700 space-y-2">
            <div className="flex items-center space-x-2 text-white font-bold text-sm">
              <Globe className="w-4 h-4 text-brand-emerald" />
              <span>Tavily Search API</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Provides real-time, search-depth tuned live web research with snippet extraction, publishing dates, and domain
              metadata optimized for factual grounding and evidence retrieval.
            </p>
          </div>
        </div>
      </div>

      {/* Distinct Features */}
      <div className="space-y-4">
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
          FreshTrace Differentiating Features
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700 space-y-2">
            <div className="flex items-center space-x-2 text-brand-cyan text-sm font-semibold">
              <ShieldCheck className="w-4 h-4" />
              <span>Freshness Passport</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every extracted claim carries an audit passport with status badge, freshness score, confidence level, temporal
              risk, and direct source links.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700 space-y-2">
            <div className="flex items-center space-x-2 text-amber-400 text-sm font-semibold">
              <Radar className="w-4 h-4" />
              <span>Temporal Risk Radar</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Heuristic score assessing how quickly information is likely to decay, combining volatility classification
              with evidence recency and conflict.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700 space-y-2">
            <div className="flex items-center space-x-2 text-brand-emerald text-sm font-semibold">
              <GitCompare className="w-4 h-4" />
              <span>Change Detection</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Audit and compare two verification runs over time to track knowledge drift, status changes, and newly emerged
              evidence.
            </p>
          </div>
        </div>
      </div>

      {/* Transparent Scoring Formula */}
      <div className="p-6 rounded-2xl bg-dark-900 border border-dark-700 space-y-4">
        <div className="flex items-center space-x-2 text-white font-bold text-sm">
          <Scale className="w-4 h-4 text-amber-400" />
          <span>Transparent Scoring Formula &amp; Disclosures</span>
        </div>
        <div className="text-xs text-slate-300 space-y-2.5 leading-relaxed">
          <p>
            <strong>Freshness Score (0–100):</strong> Measures how strongly retrieved live evidence supports current accuracy.
            Penalizes contradictory evidence and outdated timestamps on high-volatility claims.
          </p>
          <p>
            <strong>Confidence Score (0–100):</strong> Independent measure of statistical evidence strength (volume of sources,
            domain diversity, consensus vs contradiction).
          </p>
          <p>
            <strong>Temporal Risk Score (0–100):</strong> Prioritizes claims most vulnerable to rapid change (e.g. pricing,
            software versions, executive roles).
          </p>
          <p className="text-slate-400 italic pt-1 border-t border-dark-800">
            * Important Disclosure: Credibility heuristics and freshness scores are rule-based and model-assisted assessments,
            not absolute scientific proofs. Always verify critical decisions against original sources.
          </p>
        </div>
      </div>
    </div>
  );
};
