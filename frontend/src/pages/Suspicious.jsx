import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { caseApi, detectorApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import StatusBadge from '../components/StatusBadge';
import EvidenceCard from '../components/EvidenceCard';
import { AlertTriangle, Filter, Search, FileText } from 'lucide-react';

export default function Suspicious() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const detectorParam = searchParams.get('detector') || '';

  const [caseData, setCaseData] = useState(null);
  const [suspiciousList, setSuspiciousList] = useState([]);
  const [detectors, setDetectors] = useState([]);
  const [selectedDetector, setSelectedDetector] = useState(detectorParam);
  const [activeEvidence, setActiveEvidence] = useState(null);

  const fetchData = async () => {
    try {
      const [caseRes, suspRes, detRes] = await Promise.all([
        caseApi.get(id),
        detectorApi.getSuspicious(id, selectedDetector || undefined),
        detectorApi.getDetectors(id),
      ]);
      setCaseData(caseRes.data.data.case);
      setSuspiciousList(suspRes.data.data.suspicious_transactions || []);
      setDetectors(detRes.data.data.detector_results || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id, selectedDetector]);

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading suspicious transactions...</div>;

  return (
    <div>
      <CaseNav
        caseId={caseData.case_id}
        caseNumber={caseData.case_number}
        title={caseData.title}
        score={caseData.suspicion_score}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Controls */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Flagged Suspicious Transactions ({suspiciousList.length})
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Transactions identified by one or more of the 8 surveillance algorithms with source provenance.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedDetector}
              onChange={(e) => {
                setSelectedDetector(e.target.value);
                setSearchParams(e.target.value ? { detector: e.target.value } : {});
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Detectors</option>
              {detectors.map((d) => (
                <option key={d.detector} value={d.detector}>
                  {d.detector.replace(/_/g, ' ')} ({d.transactions?.length || 0})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Suspicious Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {suspiciousList.length === 0 ? (
            <div className="col-span-full text-center py-16 bg-slate-900 border border-slate-800 rounded-xl">
              <AlertTriangle className="w-10 h-10 text-slate-400 mx-auto mb-2" />
              <p className="text-slate-300 text-sm">No suspicious transactions flagged for this filter.</p>
            </div>
          ) : (
            suspiciousList.map((st) => {
              const tx = st.transaction || {};
              return (
                <EvidenceCard
                  key={st.id}
                  transactionId={st.transaction_id}
                  amount={tx.amount}
                  detector={st.detector_name}
                  reason={st.reason}
                  sourceStatement={tx.source_file}
                  sourcePage={tx.source_page}
                  date={tx.transaction_date}
                  onClick={() => setActiveEvidence(st)}
                />
              );
            })
          )}
        </div>

        {/* Evidence Detail Modal */}
        {activeEvidence && (
          <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-bold text-emerald-400 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                    {activeEvidence.transaction_id}
                  </span>
                  <StatusBadge status={activeEvidence.severity} />
                </div>
                <button
                  onClick={() => setActiveEvidence(null)}
                  className="text-slate-400 hover:text-white text-lg font-bold px-2"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 uppercase tracking-wider text-[10px] font-semibold block mb-0.5">
                    Flagging Detector
                  </span>
                  <span className="font-bold text-amber-400 text-sm">{activeEvidence.detector_name}</span>
                </div>

                <div>
                  <span className="text-slate-400 uppercase tracking-wider text-[10px] font-semibold block mb-0.5">
                    Evidentiary Rationale
                  </span>
                  <p className="text-slate-200 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800">
                    {activeEvidence.reason}
                  </p>
                </div>

                {activeEvidence.transaction && (
                  <div className="grid grid-cols-2 gap-3 bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Amount:</span>
                      <span className="font-bold font-mono text-white text-sm">
                        ₹{activeEvidence.transaction.amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Account:</span>
                      <span className="font-mono text-slate-200">
                        {activeEvidence.transaction.bank_name} ({activeEvidence.transaction.account_number})
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Source Statement:</span>
                      <span className="text-slate-300 font-mono truncate block">
                        {activeEvidence.transaction.source_file} (p.{activeEvidence.transaction.source_page})
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Date:</span>
                      <span className="text-slate-300 font-mono">
                        {activeEvidence.transaction.transaction_date?.slice(0, 16).replace('T', ' ')}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-slate-800 text-right">
                <button
                  onClick={() => setActiveEvidence(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
