import React from 'react';

export default function StatusBadge({ status, type = 'transaction' }) {
  if (!status) return null;

  const s = status.toUpperCase();

  let styles = 'bg-slate-800 text-slate-300 border-slate-700';

  if (s === 'SUCCESS' || s === 'COMPLETED' || s === 'ACTIVE' || s === 'VALID') {
    styles = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (s === 'FAILED' || s === 'CRITICAL' || s === 'INVALID') {
    styles = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  } else if (s === 'REVERSED' || s === 'RETURNED') {
    styles = 'bg-purple-500/10 text-purple-400 border-purple-500/30';
  } else if (s === 'PENDING' || s === 'PROCESSING' || s === 'WARNING') {
    styles = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  } else if (s === 'REFUNDED') {
    styles = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
  } else if (s === 'HIGH') {
    styles = 'bg-orange-500/10 text-orange-400 border-orange-500/30';
  } else if (s === 'MEDIUM' || s === 'MODERATE') {
    styles = 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';
  } else if (s === 'LOW') {
    styles = 'bg-blue-500/10 text-blue-400 border-blue-500/30';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${styles}`}>
      {status}
    </span>
  );
}
