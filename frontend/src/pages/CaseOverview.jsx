import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { caseApi, detectorApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import SuspicionScoreGauge from '../components/SuspicionScoreGauge';
import StatusBadge from '../components/StatusBadge';
import {
  FileText,
  CreditCard,
  ArrowLeftRight,
  AlertTriangle,
  Play,
  Bot,
  FileCheck2,
  User,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

export default function CaseOverview() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  const fetchCase = async () => {
    try {
      const res = await caseApi.get(id);
      setCaseData(res.data.data.case);
    } catch (e) {
      console.error('Failed to load case', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCase();
  }, [id]);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      await detectorApi.analyze(id);
      await fetchCase();
    } catch (e) {
      console.error('Analysis trigger failed', e);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading || !caseData) {
    return <div className="text-center py-20 text-slate-400">Loading case details...</div>;
  }

  const person = caseData.person || {};

  return (
    <div>
      <CaseNav
        caseId={caseData.case_id}
        caseNumber={caseData.case_number}
        title={caseData.title}
        score={caseData.suspicion_score}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Top Control Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Status:</span>
            <StatusBadge status={caseData.status} />
            <span className="text-xs text-slate-400 ml-2">Priority:</span>
            <StatusBadge status={caseData.priority} />
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs transition-all shadow shadow-emerald-500/20 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              <span>{analyzing ? 'Running Detectors...' : 'Run 8 Detectors'}</span>
            </button>

            <Link
              to={`/cases/${id}/investigation`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-lg text-xs transition-all shadow shadow-blue-500/20"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>AI Investigation Assistant</span>
            </Link>

            <Link
              to={`/cases/${id}/reports`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg text-xs border border-slate-700 transition-all"
            >
              <FileCheck2 className="w-3.5 h-3.5" />
              <span>View Report</span>
            </Link>
          </div>
        </div>

        {/* Grid: Left Summary & Right Gauge */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column (2 spans): Person details and case metrics */}
          <div className="lg:col-span-2 space-y-6">
            {/* Person Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow space-y-4">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <User className="w-4 h-4 text-emerald-400" />
                Person Under Investigation
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5">Full Name</span>
                  <span className="font-bold text-white text-sm">{person.full_name || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Official Identifier</span>
                  <span className="font-mono text-slate-200 bg-slate-950 px-2 py-1 rounded border border-slate-800">
                    {person.identifier_type || 'ID'}: {person.identifier_value || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Phone Number</span>
                  <span className="text-slate-200">{person.phone || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Email</span>
                  <span className="text-slate-200">{person.email || 'N/A'}</span>
                </div>
                <div className="sm:col-span-2">
                  <span className="text-slate-400 block mb-0.5">Address</span>
                  <span className="text-slate-200">{person.address || 'N/A'}</span>
                </div>
                {person.notes && (
                  <div className="sm:col-span-2 pt-2 border-t border-slate-800/80">
                    <span className="text-slate-400 block mb-0.5">Investigative Background</span>
                    <p className="text-slate-300 leading-relaxed">{person.notes}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <Link to={`/cases/${id}/statements`} className="bg-slate-900 border border-slate-800 hover:border-slate-700 p-4 rounded-xl transition-all block">
                <div className="flex items-center justify-between text-slate-400 mb-1">
                  <span className="text-xs uppercase font-medium">Statements</span>
                  <FileText className="w-4 h-4 text-blue-400" />
                </div>
                <p className="text-2xl font-bold font-mono text-white">{caseData.statements_count}</p>
              </Link>

              <Link to={`/cases/${id}/accounts`} className="bg-slate-900 border border-slate-800 hover:border-slate-700 p-4 rounded-xl transition-all block">
                <div className="flex items-center justify-between text-slate-400 mb-1">
                  <span className="text-xs uppercase font-medium">Accounts</span>
                  <CreditCard className="w-4 h-4 text-purple-400" />
                </div>
                <p className="text-2xl font-bold font-mono text-white">{caseData.accounts_count}</p>
              </Link>

              <Link to={`/cases/${id}/transactions`} className="bg-slate-900 border border-slate-800 hover:border-slate-700 p-4 rounded-xl transition-all block">
                <div className="flex items-center justify-between text-slate-400 mb-1">
                  <span className="text-xs uppercase font-medium">Transactions</span>
                  <ArrowLeftRight className="w-4 h-4 text-cyan-400" />
                </div>
                <p className="text-2xl font-bold font-mono text-white">{caseData.transactions_count}</p>
              </Link>

              <Link to={`/cases/${id}/suspicious`} className="bg-slate-900 border border-slate-800 hover:border-slate-700 p-4 rounded-xl transition-all block">
                <div className="flex items-center justify-between text-slate-400 mb-1">
                  <span className="text-xs uppercase font-medium">Flagged</span>
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                </div>
                <p className="text-2xl font-bold font-mono text-amber-400">{caseData.suspicious_count}</p>
              </Link>
            </div>
          </div>

          {/* Right Column (1 span): Suspicion Score Gauge */}
          <div>
            <SuspicionScoreGauge
              score={caseData.suspicion_score || 0}
              breakdown={caseData.score_breakdown || {}}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
