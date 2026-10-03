import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi, graphApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import StatusBadge from '../components/StatusBadge';
import { Layers, ArrowRight, RefreshCw, Clock, AlertTriangle } from 'lucide-react';

export default function Layering() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [layeringChains, setLayeringChains] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchChains = async (refresh = false) => {
    setLoading(true);
    try {
      const [caseRes, chainsRes] = await Promise.all([
        caseApi.get(id),
        graphApi.getLayering(id, refresh),
      ]);
      setCaseData(caseRes.data.data.case);
      setLayeringChains(chainsRes.data.data.layering_chains || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChains();
  }, [id]);

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading layering chains...</div>;

  return (
    <div>
      <CaseNav
        caseId={caseData.case_id}
        caseNumber={caseData.case_number}
        title={caseData.title}
        score={caseData.suspicion_score}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow">
          <div>
            <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Layers className="w-5 h-5 text-emerald-400" />
              Layering & Transit Chains ({layeringChains.length})
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Multi-hop path exploration (A → B → C → D). Tracks rapid fund dispersion and intermediary conduits.
            </p>
          </div>

          <button
            onClick={() => fetchChains(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg text-xs border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-emerald-400" />
            <span>Re-traverse Chains</span>
          </button>
        </div>

        {layeringChains.length === 0 ? (
          <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-xl">
            <Layers className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <p className="text-slate-300 font-semibold">No multi-hop layering chains detected.</p>
            <p className="text-xs text-slate-400 mt-1">
              No continuous paths with 3 or more hops were identified across the accounts.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {layeringChains.map((lc) => (
              <div key={lc.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded border border-cyan-500/30">
                      {lc.hops_count} Hops
                    </span>
                    <StatusBadge status={lc.risk_level} />
                  </div>

                  <div className="flex items-center gap-4 text-xs font-mono">
                    <span className="text-slate-400">Bottleneck Volume:</span>
                    <span className="text-base font-bold text-white">
                      ₹{lc.total_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                    <span className="text-slate-400">Duration:</span>
                    <span className="font-semibold text-slate-200">{lc.duration_hours} hrs</span>
                  </div>
                </div>

                {/* Chain Path Visualizer */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-x-auto">
                  <div className="flex items-center gap-3 min-w-max">
                    {lc.chain_path?.map((step, idx) => (
                      <React.Fragment key={idx}>
                        <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono font-bold text-white shadow">
                          {step}
                        </div>
                        {idx < lc.chain_path.length - 1 && (
                          <div className="flex items-center text-cyan-400 font-bold">
                            <span>→</span>
                          </div>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-sans">{lc.evidence_summary}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
