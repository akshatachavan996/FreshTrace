import React from 'react';
import { ArrowRight, Search, FileText, Activity, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface LandingHeroProps {
  onSelectSample: (question: string, answer: string) => void;
  onStartVerify: () => void;
}

const SAMPLE_PRESETS = [
  {
    title: 'Software Versions & APIs',
    badge: 'High Volatility',
    question: 'What is the current stable version of Next.js and does it require React 19?',
    answer:
      'The current stable version of Next.js is Next.js 14, released in late 2023. Next.js 14 requires React 18 and does not yet support React 19. Server Actions are still in experimental alpha preview.',
  },
  {
    title: 'Company Leadership & Roles',
    badge: 'High Volatility',
    question: 'Who is the CEO of Twitter / X and when did they take office?',
    answer:
      'Elon Musk is the current CEO of Twitter (now X), having purchased the company in October 2022 and remaining the active chief executive officer today.',
  },
  {
    title: 'Cloud & AI Pricing',
    badge: 'High Volatility',
    question: 'How much does OpenAI GPT-4 API cost per million tokens?',
    answer:
      'The standard GPT-4 model costs $30.00 per 1 million input tokens and $60.00 per 1 million output tokens. There are no cheaper mini variants available.',
  },
];

export const LandingHero: React.FC<LandingHeroProps> = ({ onSelectSample, onStartVerify }) => {
  return (
    <div className="py-8 space-y-12">
      {/* Top Banner / Hero */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-cyan/10 border border-brand-cyan/20 text-brand-cyan text-xs font-mono uppercase tracking-wider">
          <Activity className="w-3.5 h-3.5" />
          <span>Automated Stale-Answer Detection</span>
        </div>

        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
          Trust the answer. <br />
          <span className="bg-gradient-to-r from-brand-cyan via-teal-300 to-brand-emerald bg-clip-text text-transparent">
            Verify what's changed.
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
          AI models speak with confidence—even when their knowledge is outdated, APIs have changed, prices have shifted,
          or leadership has moved on. FreshTrace extracts discrete claims and verifies them against the live web in real time.
        </p>

        <div className="pt-2 flex justify-center">
          <button
            onClick={onStartVerify}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-teal text-dark-950 font-semibold text-sm shadow-lg shadow-brand-cyan/20 hover:opacity-95 transition-all flex items-center space-x-2"
          >
            <span>Verify an Answer</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* How It Works Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700/60 space-y-2">
          <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-sm">
            1
          </div>
          <h3 className="font-semibold text-white text-sm">Claim Extraction</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Deconstructs complex answers into isolated, verifiable factual assertions via Bifrost AI Gateway.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700/60 space-y-2">
          <div className="w-9 h-9 rounded-lg bg-brand-cyan/10 border border-brand-cyan/20 flex items-center justify-center text-brand-cyan font-bold text-sm">
            2
          </div>
          <h3 className="font-semibold text-white text-sm">Volatility Analysis</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Categorizes claims (High, Med, Low) based on susceptibility to drift (pricing, versions, laws).
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700/60 space-y-2">
          <div className="w-9 h-9 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400 font-bold text-sm">
            3
          </div>
          <h3 className="font-semibold text-white text-sm">Live Web Search</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Gathers recent, authoritative evidence across independent domains using Tavily Search API.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-dark-900 border border-dark-700/60 space-y-2">
          <div className="w-9 h-9 rounded-lg bg-brand-emerald/10 border border-brand-emerald/20 flex items-center justify-center text-brand-emerald font-bold text-sm">
            4
          </div>
          <h3 className="font-semibold text-white text-sm">Freshness Scoring</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Computes a transparent 0-100 score weighing support, recency, credibility heuristics, and consensus.
          </p>
        </div>
      </div>

      {/* Preset Test Scenarios */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider font-mono">
            Try Example AI Answers
          </h2>
          <span className="text-xs text-slate-500">Click to load into workspace</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {SAMPLE_PRESETS.map((preset, idx) => (
            <div
              key={idx}
              onClick={() => onSelectSample(preset.question, preset.answer)}
              className="p-4 rounded-xl bg-dark-900 hover:bg-dark-850 border border-dark-700/80 hover:border-brand-cyan/40 cursor-pointer transition-all space-y-2.5 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white group-hover:text-brand-cyan transition-colors">
                  {preset.title}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  {preset.badge}
                </span>
              </div>
              <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">
                "{preset.answer}"
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
