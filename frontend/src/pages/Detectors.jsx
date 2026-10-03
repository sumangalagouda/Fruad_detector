import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { caseApi, detectorApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import StatusBadge from '../components/StatusBadge';
import {
  ShieldCheck,
  ShieldAlert,
  RefreshCw,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Sliders,
} from 'lucide-react';

export default function Detectors() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [detectorResults, setDetectorResults] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);

  const fetchData = async () => {
    try {
      const [caseRes, detRes] = await Promise.all([caseApi.get(id), detectorApi.getDetectors(id)]);
      setCaseData(caseRes.data.data.case);
      setDetectorResults(detRes.data.data.detector_results || []);
    } catch (e) {
      console.error('Failed to load detectors', e);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleRunDetectors = async () => {
    setAnalyzing(true);
    try {
      await detectorApi.analyze(id);
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(false);
    }
  };

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading detectors...</div>;

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
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Eight Deterministic Crime Detectors
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Zero hallucination: algorithms evaluate rule-based compliance patterns, returning explainable evidence.
            </p>
          </div>

          <button
            onClick={handleRunDetectors}
            disabled={analyzing}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
            <span>{analyzing ? 'Analyzing Transactions...' : 'Re-Run All 8 Detectors'}</span>
          </button>
        </div>

        {/* 8 Detector Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {detectorResults.map((det) => {
            const isTriggered = det.triggered;
            const flagCount = det.transactions?.length || 0;

            return (
              <div
                key={det.id || det.detector}
                className={`bg-slate-900 border rounded-xl p-5 shadow-lg flex flex-col justify-between transition-all ${
                  isTriggered ? 'border-amber-500/40 bg-gradient-to-b from-slate-900 to-amber-950/10' : 'border-slate-800'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <span className="font-bold text-xs uppercase tracking-wider text-slate-200 truncate">
                      {det.detector?.replace(/_/g, ' ')}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        isTriggered
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {isTriggered ? 'TRIGGERED' : 'CLEAR'}
                    </span>
                  </div>

                  <div className="my-3 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">Severity:</span>
                      <StatusBadge status={det.severity} />
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">Flagged Transactions:</span>
                      <span className="font-mono font-bold text-white">{flagCount}</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed font-sans line-clamp-3 bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 mb-3">
                    {det.reason}
                  </p>

                  {/* Key Metrics */}
                  {det.metrics && Object.keys(det.metrics).length > 0 && (
                    <div className="text-[11px] text-slate-400 space-y-1 pt-2 border-t border-slate-800/80">
                      {Object.entries(det.metrics).slice(0, 3).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span className="capitalize">{k.replace(/_/g, ' ')}:</span>
                          <span className="font-mono font-semibold text-slate-200">
                            {typeof v === 'number' && v > 1000 ? `₹${v.toLocaleString('en-IN')}` : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {isTriggered && (
                  <div className="pt-3 border-t border-slate-800/80 mt-3 text-right">
                    <Link
                      to={`/cases/${id}/suspicious?detector=${det.detector}`}
                      className="inline-flex items-center gap-1 text-xs text-amber-400 hover:text-amber-300 font-medium"
                    >
                      <span>View Flagged ({flagCount})</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
