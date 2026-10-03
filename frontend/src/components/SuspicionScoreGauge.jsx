import React from 'react';
import { AlertTriangle, ShieldCheck, Info } from 'lucide-react';

export default function SuspicionScoreGauge({ score = 0, breakdown = {} }) {
  const getRiskDetails = (val) => {
    if (val >= 70) {
      return {
        level: 'CRITICAL RISK',
        color: 'text-rose-400',
        bg: 'bg-rose-500',
        border: 'border-rose-500/30',
        barBg: 'bg-rose-500',
      };
    }
    if (val >= 50) {
      return {
        level: 'HIGH RISK',
        color: 'text-amber-400',
        bg: 'bg-amber-500',
        border: 'border-amber-500/30',
        barBg: 'bg-amber-500',
      };
    }
    if (val >= 25) {
      return {
        level: 'MODERATE RISK',
        color: 'text-yellow-400',
        bg: 'bg-yellow-500',
        border: 'border-yellow-500/30',
        barBg: 'bg-yellow-500',
      };
    }
    return {
      level: 'LOW RISK',
      color: 'text-emerald-400',
      bg: 'bg-emerald-500',
      border: 'border-emerald-500/30',
      barBg: 'bg-emerald-500',
    };
  };

  const risk = getRiskDetails(score);
  const contributions = breakdown.detector_contributions || {};

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Suspicion Score</h3>
          <p className="text-xs text-slate-400 mt-0.5">Investigation Risk Indicator (Not a probability of fraud)</p>
        </div>
        <span className={`px-2.5 py-1 text-xs font-bold rounded-md border ${risk.color} ${risk.border} bg-slate-950`}>
          {risk.level}
        </span>
      </div>

      {/* Main Score Gauge */}
      <div className="flex items-baseline gap-2 my-4">
        <span className={`text-4xl font-extrabold font-mono ${risk.color}`}>{score.toFixed(1)}</span>
        <span className="text-sm text-slate-400 font-mono">/ 100.0</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950 rounded-full h-3 overflow-hidden border border-slate-800 mb-6">
        <div
          className={`h-full transition-all duration-700 rounded-full ${risk.barBg}`}
          style={{ width: `${Math.min(100, Math.max(2, score))}%` }}
        />
      </div>

      {/* Breakdown Contributions */}
      <div>
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">Detector Contributions</h4>
        <div className="space-y-2.5">
          {Object.entries(contributions).map(([det, val]) => {
            const label = det.replace(/_/g, ' ');
            const pct = Math.min(100, (val / 20.0) * 100);
            return (
              <div key={det} className="text-xs">
                <div className="flex justify-between text-slate-300 mb-1">
                  <span className="capitalize">{label.toLowerCase()}</span>
                  <span className="font-mono font-medium">{val > 0 ? `+${val.toFixed(1)}` : '0.0'}</span>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${val > 0 ? 'bg-emerald-400' : 'bg-slate-800'}`}
                    style={{ width: `${val > 0 ? Math.max(10, pct) : 0}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
