import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  FileText,
  CreditCard,
  ArrowLeftRight,
  ShieldCheck,
  AlertTriangle,
  GitBranch,
  RotateCw,
  Layers,
  Milestone,
  Bot,
  FileCheck2,
  History as HistoryIcon,
  Info,
} from 'lucide-react';

export default function CaseNav({ caseId, caseNumber, title, score }) {
  const tabs = [
    { name: 'Overview', path: `/cases/${caseId}`, icon: Info, end: true },
    { name: 'Statements', path: `/cases/${caseId}/statements`, icon: FileText },
    { name: 'Accounts', path: `/cases/${caseId}/accounts`, icon: CreditCard },
    { name: 'Transactions', path: `/cases/${caseId}/transactions`, icon: ArrowLeftRight },
    { name: 'Detectors', path: `/cases/${caseId}/detectors`, icon: ShieldCheck },
    { name: 'Suspicious', path: `/cases/${caseId}/suspicious`, icon: AlertTriangle },
    { name: 'Fund Flow', path: `/cases/${caseId}/fund-flow`, icon: GitBranch },
    { name: 'Circular Flows', path: `/cases/${caseId}/circular-flows`, icon: RotateCw },
    { name: 'Layering', path: `/cases/${caseId}/layering`, icon: Layers },
    { name: 'Money Trail', path: `/cases/${caseId}/money-trail`, icon: Milestone },
    { name: 'AI Investigation', path: `/cases/${caseId}/investigation`, icon: Bot, highlight: true },
    { name: 'Reports', path: `/cases/${caseId}/reports`, icon: FileCheck2 },
    { name: 'History', path: `/cases/${caseId}/history`, icon: HistoryIcon },
  ];

  const getScoreColor = (s) => {
    if (s >= 70) return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    if (s >= 50) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    if (s >= 25) return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
    return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  };

  return (
    <div className="bg-slate-900/90 border-b border-slate-800 backdrop-blur-sm sticky top-16 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        {/* Header Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {caseNumber}
              </span>
              <h1 className="text-lg font-bold text-white tracking-tight">{title}</h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-full border text-xs font-semibold flex items-center gap-1.5 ${getScoreColor(score || 0)}`}>
              <span>Suspicion Score:</span>
              <span className="text-sm font-bold font-mono">{score ?? 0}</span>
              <span className="text-[10px] text-slate-400">/ 100</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 overflow-x-auto pb-1 text-xs no-scrollbar">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <NavLink
                key={tab.name}
                to={tab.path}
                end={tab.end}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-lg font-medium whitespace-nowrap transition-all ${
                    isActive
                      ? tab.highlight
                        ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/20'
                        : 'bg-slate-800 text-emerald-400 border border-slate-700'
                      : tab.highlight
                      ? 'text-emerald-400 hover:bg-emerald-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
