import React, { useState, useEffect } from 'react';
import { Send, Zap, Search, AlertCircle, XCircle, RotateCcw } from 'lucide-react';
import { VerificationMode, VerificationResponse } from '../types';
import { verifyAnswer } from '../services/api';

interface WorkspaceProps {
  initialQuestion?: string;
  initialAnswer?: string;
  onVerificationComplete: (response: VerificationResponse) => void;
}

const STAGES = [
  'Connecting to Bifrost AI Gateway...',
  'Extracting verifiable factual claims...',
  'Searching live web via Tavily...',
  'Analyzing evidence & computing freshness score...',
];

export const Workspace: React.FC<WorkspaceProps> = ({
  initialQuestion = '',
  initialAnswer = '',
  onVerificationComplete,
}) => {
  const [question, setQuestion] = useState(initialQuestion);
  const [answerText, setAnswerText] = useState(initialAnswer);
  const [mode, setMode] = useState<VerificationMode>('DEEP_CHECK');
  const [isLoading, setIsLoading] = useState(false);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [error, setError] = useState<{ message: string; type?: string; details?: any } | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  useEffect(() => {
    if (initialQuestion) setQuestion(initialQuestion);
    if (initialAnswer) setAnswerText(initialAnswer);
  }, [initialQuestion, initialAnswer]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isLoading) {
      interval = setInterval(() => {
        setCurrentStageIndex((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
      }, 2500);
    } else {
      setCurrentStageIndex(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (answerText.trim().length < 10) {
      setError({ message: 'Answer text must be at least 10 characters long to extract claims.' });
      return;
    }
    if (answerText.length > 10000) {
      setError({ message: 'Answer text exceeds maximum limit of 10,000 characters.' });
      return;
    }

    setError(null);
    setIsLoading(true);
    const controller = new AbortController();
    setAbortController(controller);

    try {
      const result = await verifyAnswer(answerText, question, mode, controller.signal);
      onVerificationComplete(result);
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setError({ message: 'Verification cancelled by user.' });
      } else {
        setError({
          message: err.message || 'An error occurred during verification.',
          type: err.errorType,
          details: err.details,
        });
      }
    } finally {
      setIsLoading(false);
      setAbortController(null);
    }
  };

  const handleCancel = () => {
    if (abortController) {
      abortController.abort();
    }
  };

  const handleClear = () => {
    setQuestion('');
    setAnswerText('');
    setError(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Workspace Card */}
      <div className="p-6 sm:p-8 rounded-2xl bg-dark-900 border border-dark-700/80 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-dark-800 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white">Verification Workspace</h2>
            <p className="text-xs text-slate-400">
              Paste any AI-generated response to extract verifiable facts and check live web evidence.
            </p>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center space-x-1 p-1 bg-dark-950 rounded-lg border border-dark-800 text-xs font-medium">
            <button
              type="button"
              onClick={() => setMode('QUICK_CHECK')}
              className={`px-3 py-1.5 rounded-md transition-all flex items-center space-x-1 ${
                mode === 'QUICK_CHECK'
                  ? 'bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Quick Check</span>
            </button>
            <button
              type="button"
              onClick={() => setMode('DEEP_CHECK')}
              className={`px-3 py-1.5 rounded-md transition-all flex items-center space-x-1 ${
                mode === 'DEEP_CHECK'
                  ? 'bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>Deep Check</span>
            </button>
          </div>
        </div>

        <form onSubmit={handleVerify} className="space-y-4">
          {/* Optional Question */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
              Original Prompt / Context (Optional)
            </label>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What is the latest version of Next.js and its release requirements?"
              disabled={isLoading}
              className="w-full px-4 py-2.5 rounded-xl bg-dark-950 border border-dark-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan transition-colors"
            />
          </div>

          {/* Answer Text Area */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                AI-Generated Answer to Verify <span className="text-rose-400">*</span>
              </label>
              <span className="text-[11px] font-mono text-slate-500">
                {answerText.length} / 10,000 chars
              </span>
            </div>
            <textarea
              rows={6}
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder="Paste the AI response here. FreshTrace will extract concrete claims, identify high-volatility statements (pricing, versioning, roles, laws), and query Tavily for live proof."
              disabled={isLoading}
              className="w-full px-4 py-3 rounded-xl bg-dark-950 border border-dark-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan transition-colors resize-y leading-relaxed font-sans"
            />
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs space-y-1 flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-semibold">{error.message}</p>
                {error.type === 'MISSING_CREDENTIALS' && (
                  <p className="text-slate-400 text-[11px]">
                    To enable live AI claim extraction and web research, provide <code className="text-brand-cyan">BIFROST_API_KEY</code> and <code className="text-brand-cyan">TAVILY_API_KEY</code> in <code className="text-slate-300">backend/.env</code>.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Loading / Stage Display */}
          {isLoading && (
            <div className="p-4 rounded-xl bg-dark-950 border border-brand-cyan/20 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-brand-cyan font-mono font-medium flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-brand-cyan animate-ping" />
                  <span>{STAGES[currentStageIndex]}</span>
                </span>
                <span className="text-slate-500 font-mono">Stage {currentStageIndex + 1} of 4</span>
              </div>
              <div className="w-full bg-dark-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-brand-cyan to-brand-emerald h-full transition-all duration-500"
                  style={{ width: `${((currentStageIndex + 1) / STAGES.length) * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={handleClear}
              disabled={isLoading || (!answerText && !question)}
              className="px-3 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors flex items-center space-x-1 disabled:opacity-30"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>

            <div className="flex items-center space-x-3">
              {isLoading ? (
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-4 py-2.5 rounded-xl border border-rose-500/40 text-rose-300 text-xs font-semibold hover:bg-rose-950/40 transition-colors flex items-center space-x-1.5"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Cancel</span>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={answerText.trim().length < 10}
                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-emerald text-dark-950 font-bold text-xs uppercase tracking-wider shadow-lg shadow-brand-cyan/20 hover:opacity-95 transition-all flex items-center space-x-2 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Verify Answer</span>
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
