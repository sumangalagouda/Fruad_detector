import React from 'react';
import { FileText, ShieldAlert, DollarSign, Calendar, ExternalLink } from 'lucide-react';

export default function EvidenceCard({
  transactionId,
  amount,
  sourceStatement,
  sourcePage = 1,
  detector,
  reason,
  date,
  onClick,
}) {
  return (
    <div
      onClick={onClick}
      className="bg-slate-900/90 border border-slate-700/60 hover:border-emerald-500/50 rounded-xl p-3.5 shadow-md transition-all hover:shadow-emerald-500/5 group"
    >
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
            {transactionId}
          </span>
          {detector && (
            <span className="text-[10px] uppercase font-semibold text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
              {detector.replace(/_/g, ' ')}
            </span>
          )}
        </div>

        {amount !== undefined && (
          <span className="text-sm font-bold font-mono text-slate-200">
            ₹{typeof amount === 'number' ? amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : amount}
          </span>
        )}
      </div>

      {reason && (
        <p className="text-xs text-slate-300 my-2 leading-relaxed font-sans">{reason}</p>
      )}

      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1.5 border-t border-slate-800/80">
        <div className="flex items-center gap-1.5 truncate max-w-[200px]" title={sourceStatement}>
          <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="truncate">{sourceStatement || 'Statement'}</span>
          <span className="text-slate-400">p.{sourcePage}</span>
        </div>

        {date && (
          <div className="flex items-center gap-1 shrink-0 font-mono text-[10px] text-slate-400">
            <Calendar className="w-3 h-3 text-slate-400" />
            <span>{date.slice(0, 10)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
