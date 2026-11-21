import React from 'react';
import { ShieldCheck, History, Info, Sparkles, Server } from 'lucide-react';
import { HealthInfo } from '../types';

interface NavbarProps {
  activeTab: 'workspace' | 'history' | 'about';
  setActiveTab: (tab: 'workspace' | 'history' | 'about') => void;
  health: HealthInfo | null;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, health }) => {
  const isHealthy = health?.status === 'healthy';
  const bifrostConfigured = health?.providers.bifrost.configured;
  const tavilyConfigured = health?.providers.tavily.configured;

  return (
    <header className="border-b border-dark-700 bg-dark-900/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div
          className="flex items-center space-x-3 cursor-pointer group"
          onClick={() => setActiveTab('workspace')}
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-cyan to-brand-emerald p-[1px] shadow-lg shadow-brand-cyan/20">
            <div className="w-full h-full bg-dark-950 rounded-xl flex items-center justify-center group-hover:bg-dark-900 transition-colors">
              <ShieldCheck className="w-6 h-6 text-brand-cyan" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-white">FreshTrace</span>
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/30">
                AI Freshness
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono hidden sm:block">Trust the answer. Verify what's changed.</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          <button
            onClick={() => setActiveTab('workspace')}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-1.5 ${
              activeTab === 'workspace'
                ? 'bg-brand-cyan/15 text-brand-cyan border border-brand-cyan/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-dark-800'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Verify Workspace</span>
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-1.5 ${
              activeTab === 'history'
                ? 'bg-brand-cyan/15 text-brand-cyan border border-brand-cyan/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-dark-800'
            }`}
          >
            <History className="w-4 h-4" />
            <span>History</span>
          </button>

          <button
            onClick={() => setActiveTab('about')}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-1.5 ${
              activeTab === 'about'
                ? 'bg-brand-cyan/15 text-brand-cyan border border-brand-cyan/30 shadow-sm'
                : 'text-slate-400 hover:text-white hover:bg-dark-800'
            }`}
          >
            <Info className="w-4 h-4" />
            <span>How It Works</span>
          </button>
        </nav>

        {/* System Provider Status Pill */}
        <div className="hidden md:flex items-center space-x-2 text-xs font-mono">
          <div
            title={`Bifrost: ${bifrostConfigured ? 'Connected' : 'Missing Key'} | Tavily: ${
              tavilyConfigured ? 'Connected' : 'Missing Key'
            }`}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-dark-800 border border-dark-700 text-slate-300"
          >
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="flex items-center space-x-1">
              <span
                className={`w-2 h-2 rounded-full ${
                  bifrostConfigured && tavilyConfigured ? 'bg-brand-emerald animate-pulse' : 'bg-amber-400'
                }`}
              />
              <span>
                {bifrostConfigured && tavilyConfigured
                  ? 'Gateway Live'
                  : !bifrostConfigured && !tavilyConfigured
                  ? 'Keys Missing'
                  : 'Partial Config'}
              </span>
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
