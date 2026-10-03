import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi, graphApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import StatusBadge from '../components/StatusBadge';
import { RotateCw, ArrowRight, RefreshCw, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function CircularFlows() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [circularFlows, setCircularFlows] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchFlows = async (refresh = false) => {
    setLoading(true);
    try {
      const [caseRes, flowsRes] = await Promise.all([
        caseApi.get(id),
        graphApi.getCircularFlows(id, refresh),
      ]);
      setCaseData(caseRes.data.data.case);
      setCircularFlows(flowsRes.data.data.circular_flows || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlows();
  }, [id]);

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading circular flows...</div>;

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
              <RotateCw className="w-5 h-5 text-emerald-400" />
              Circular Fund Flow Cycles ({circularFlows.length})
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Closed loop fund movement (A → B → C → A). Described objectively as detected financial patterns.
            </p>
          </div>

          <button
            onClick={() => fetchFlows(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg text-xs border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-emerald-400" />
            <span>Re-detect Cycles</span>
          </button>
        </div>

        {circularFlows.length === 0 ? (
          <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-xl">
            <RotateCw className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <p className="text-slate-300 font-semibold">No closed circular flow patterns identified.</p>
            <p className="text-xs text-slate-400 mt-1">
              The graph traversal algorithm did not detect fund returns within the configured cycle limit.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {circularFlows.map((cf) => (
              <div key={cf.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/30">
                      Cycle Length: {cf.length} Nodes
                    </span>
                    <StatusBadge status={cf.risk_level} />
                  </div>

                  <div className="flex items-center gap-4 text-xs font-mono">
                    <span className="text-slate-400">Circulating Volume:</span>
                    <span className="text-base font-bold text-white">
                      ₹{cf.total_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                    <span className="text-slate-400">Duration:</span>
                    <span className="font-semibold text-slate-200">{cf.duration_days} days</span>
                  </div>
                </div>

                {/* Path Visualizer */}
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 overflow-x-auto">
                  <div className="flex items-center gap-3 min-w-max">
                    {cf.cycle_path?.map((node, idx) => (
                      <React.Fragment key={idx}>
                        <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono font-bold text-white shadow">
                          {node}
                        </div>
                        {idx < cf.cycle_path.length - 1 && (
                          <div className="flex items-center text-emerald-400">
                            <span className="text-xs font-bold mr-1">→</span>
                          </div>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-sans">{cf.evidence_summary}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
