import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi, graphApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import { Milestone, ArrowRight, RefreshCw, Info, Calendar } from 'lucide-react';

export default function MoneyTrail() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [moneyTrails, setMoneyTrails] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTrails = async (refresh = false) => {
    setLoading(true);
    try {
      const [caseRes, trailsRes] = await Promise.all([
        caseApi.get(id),
        graphApi.getMoneyTrail(id, null, refresh),
      ]);
      setCaseData(caseRes.data.data.case);
      setMoneyTrails(trailsRes.data.data.money_trails || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrails();
  }, [id]);

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading money trails...</div>;

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
              <Milestone className="w-5 h-5 text-emerald-400" />
              FIFO Fund Allocation Trails ({moneyTrails.length})
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              First-In-First-Out fund matching linking verified credits to subsequent debits.
            </p>
          </div>

          <button
            onClick={() => fetchTrails(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg text-xs border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-emerald-400" />
            <span>Re-calculate FIFO Trails</span>
          </button>
        </div>

        {/* Disclaimer Banner (Required by Section 18) */}
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3 text-xs text-slate-300">
          <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-white">Investigative Caveat:</strong> FIFO allocation indicates the mathematical
            sequencing of funds availability and subsequent outflow. It does not definitively prove physical or
            cryptographic provenance of fungible currency across multi-source accounts.
          </p>
        </div>

        {/* Trails List */}
        {moneyTrails.length === 0 ? (
          <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-xl">
            <Milestone className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <p className="text-slate-300 font-semibold">No FIFO fund trail allocations available.</p>
            <p className="text-xs text-slate-400 mt-1">Upload statements containing inflows and outflows to compute FIFO links.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {moneyTrails.map((trail) => {
              const srcLink = trail.links?.find((l) => l.step_order === 1);
              const dstLink = trail.links?.find((l) => l.step_order === 2);

              return (
                <div key={trail.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <span className="font-mono text-xs font-bold text-white bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
                      Allocated Amount: ₹{trail.allocated_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                    <span className="text-[10px] uppercase font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                      {trail.trail_status}
                    </span>
                  </div>

                  {/* Flow Diagram */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                    {/* Source Link */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-1 text-xs">
                      <span className="text-[10px] uppercase text-emerald-400 font-bold block">1. Inflow Deposit</span>
                      <span className="font-mono font-bold text-white text-sm">
                        Tx: {trail.source_transaction_id}
                      </span>
                      <p className="text-slate-300 font-mono text-[11px] truncate">
                        From: {srcLink?.from_account || 'External Source'}
                      </p>
                      {srcLink?.date && (
                        <p className="text-slate-500 text-[10px] flex items-center gap-1 font-mono">
                          <Calendar className="w-3 h-3" />
                          {srcLink.date.slice(0, 16).replace('T', ' ')}
                        </p>
                      )}
                    </div>

                    {/* Intermediate Account */}
                    <div className="text-center p-3">
                      <div className="inline-flex items-center justify-center p-2 rounded-full bg-slate-800 text-emerald-400 mb-1 border border-slate-700">
                        <ArrowRight className="w-4 h-4" />
                      </div>
                      <p className="text-xs font-semibold text-slate-200">Transit Account</p>
                      <p className="text-[11px] font-mono text-slate-400">{srcLink?.to_account || 'Intermediary Account'}</p>
                    </div>

                    {/* Destination Outflow Link */}
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-1 text-xs">
                      <span className="text-[10px] uppercase text-rose-400 font-bold block">2. Outflow Dispersal</span>
                      <span className="font-mono font-bold text-white text-sm">
                        Tx: {trail.destination_transaction_id || 'Pending Outflow'}
                      </span>
                      <p className="text-slate-300 font-mono text-[11px] truncate">
                        To: {dstLink?.to_account || 'Beneficiary'}
                      </p>
                      {dstLink?.date && (
                        <p className="text-slate-500 text-[10px] flex items-center gap-1 font-mono">
                          <Calendar className="w-3 h-3" />
                          {dstLink.date.slice(0, 16).replace('T', ' ')}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
