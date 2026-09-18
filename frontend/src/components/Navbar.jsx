import React from 'react';
import { ShieldCheck, Database, Sliders, Lock, Mail, Eye, Activity, RefreshCw } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, onSeed }) {
  const tabs = [
    { id: 'discovery', label: '1. PII Discovery', icon: Database },
    { id: 'batch', label: '2. Policy & Batch', icon: Sliders },
    { id: 'protected', label: '3. Protected Data', icon: Lock },
    { id: 'marketing', label: '4. Privacy Gateway', icon: Mail },
    { id: 'reveal', label: '5. Controlled Reveal', icon: Eye },
    { id: 'audit', label: '6. Audit Trail', icon: Activity },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-tr from-emerald-600 to-teal-400 p-2 rounded-xl shadow-lg shadow-emerald-900/30">
              <ShieldCheck className="h-6 w-6 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg text-white tracking-tight flex items-center gap-1.5">
                Flyyy<span className="text-emerald-400 font-extrabold">.AI</span>
                <span className="text-xs font-mono uppercase bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 px-2 py-0.5 rounded-full ml-1">
                  CDP Engine
                </span>
              </span>
              <p className="text-[11px] text-slate-400 font-medium">Protected by Default • Reveal by Exception</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={onSeed}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 transition"
              title="Generate 50 synthetic customer records"
            >
              <RefreshCw className="h-3.5 w-3.5 text-emerald-400" />
              <span>Reset & Seed Data</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 overflow-x-auto pb-1 pt-1 scrollbar-none border-t border-slate-800/60">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
