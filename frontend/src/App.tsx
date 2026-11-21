import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { LandingHero } from './components/LandingHero';
import { Workspace } from './components/Workspace';
import { ResultsDashboard } from './components/ResultsDashboard';
import { HistoryView } from './components/HistoryView';
import { AboutModal } from './components/AboutModal';
import { HealthInfo, VerificationResponse } from './types';
import { fetchHealth } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<'workspace' | 'history' | 'about'>('workspace');
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [currentResult, setCurrentResult] = useState<VerificationResponse | null>(null);
  const [prefillQuestion, setPrefillQuestion] = useState('');
  const [prefillAnswer, setPrefillAnswer] = useState('');

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => console.warn('Could not fetch health status:', err));
  }, []);

  const handleSelectSample = (question: string, answer: string) => {
    setPrefillQuestion(question);
    setPrefillAnswer(answer);
    setCurrentResult(null);
    setActiveTab('workspace');
    window.scrollTo({ top: 300, behavior: 'smooth' });
  };

  const handleVerificationComplete = (response: VerificationResponse) => {
    setCurrentResult(response);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleReset = () => {
    setCurrentResult(null);
    setPrefillQuestion('');
    setPrefillAnswer('');
  };

  const handleSelectHistoryRun = (run: VerificationResponse) => {
    setCurrentResult(run);
    setActiveTab('workspace');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col font-sans selection:bg-brand-cyan/20 selection:text-brand-cyan">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} health={health} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
        {activeTab === 'workspace' && (
          <>
            {currentResult ? (
              <ResultsDashboard result={currentResult} onReset={handleReset} />
            ) : (
              <div className="space-y-12">
                <LandingHero
                  onSelectSample={handleSelectSample}
                  onStartVerify={() => {
                    const workspaceEl = document.getElementById('workspace-form');
                    workspaceEl?.scrollIntoView({ behavior: 'smooth' });
                  }}
                />
                <div id="workspace-form">
                  <Workspace
                    initialQuestion={prefillQuestion}
                    initialAnswer={prefillAnswer}
                    onVerificationComplete={handleVerificationComplete}
                  />
                </div>
              </div>
            )}
          </>
        )}

        {activeTab === 'history' && <HistoryView onSelectRun={handleSelectHistoryRun} />}

        {activeTab === 'about' && <AboutModal />}
      </main>

      <footer className="border-t border-dark-800 bg-dark-900/50 py-8 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 space-y-2">
          <p>FreshTrace &copy; 2026 &bull; AI Answer Freshness Verification System</p>
          <p className="text-[11px] text-slate-600">
            Powered by Bifrost AI Gateway &amp; Tavily Live Search API. Built for Hackathon Demo.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
