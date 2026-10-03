import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi, reportApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import { FileCheck2, Printer, Plus, Calendar, User, ShieldCheck, AlertCircle } from 'lucide-react';

export default function Reports() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [reports, setReports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [generating, setGenerating] = useState(false);

  const fetchReports = async () => {
    try {
      const [caseRes, reportsRes] = await Promise.all([caseApi.get(id), reportApi.list(id)]);
      setCaseData(caseRes.data.data.case);
      const list = reportsRes.data.data.reports || [];
      setReports(list);
      if (list.length > 0) {
        setActiveReport(list[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [id]);

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      const res = await reportApi.generate(id);
      await fetchReports();
      setActiveReport(res.data.data.report);
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading reports...</div>;

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
              <FileCheck2 className="w-5 h-5 text-emerald-400" />
              Evidence-Grounded Investigation Reports
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Structured 17-section compliance reports generated strictly from verified case evidence.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {activeReport && (
              <button
                onClick={handlePrint}
                className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
              >
                <Printer className="w-4 h-4" />
                <span>Print / Export PDF</span>
              </button>
            )}

            <button
              onClick={handleGenerateReport}
              disabled={generating}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
              <span>{generating ? 'Generating 17-Section Report...' : 'Generate New Report'}</span>
            </button>
          </div>
        </div>

        {reports.length === 0 ? (
          <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-xl">
            <FileCheck2 className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <p className="text-slate-300 font-semibold">No reports generated yet for this case.</p>
            <p className="text-xs text-slate-400 mt-1">Click 'Generate New Report' to compile verified findings.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Reports Sidebar */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Available Reports ({reports.length})
              </span>
              {reports.map((r) => (
                <button
                  key={r.report_id}
                  onClick={() => setActiveReport(r)}
                  className={`w-full text-left p-3 rounded-xl border text-xs transition-all ${
                    activeReport?.report_id === r.report_id
                      ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400'
                      : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <p className="font-bold truncate">{r.title}</p>
                  <p className="text-[10px] text-slate-400 mt-1 font-mono">{r.generated_at?.slice(0, 16).replace('T', ' ')}</p>
                </button>
              ))}
            </div>

            {/* Main Report Content Viewer */}
            <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-6">
              {activeReport && (
                <article className="prose prose-invert max-w-none text-xs text-slate-300 leading-relaxed font-sans">
                  <div className="border-b border-slate-800 pb-5 mb-6 flex justify-between items-center">
                    <div>
                      <h2 className="text-xl font-bold text-white tracking-tight">{activeReport.title}</h2>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Generated by {activeReport.creator_name || 'System Analyst'} •{' '}
                        {activeReport.generated_at?.slice(0, 16).replace('T', ' ')} UTC
                      </p>
                    </div>
                    <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-emerald-400 font-bold">
                      {caseData.case_number}
                    </span>
                  </div>

                  {/* Render formatted Markdown / Sections */}
                  <div className="space-y-6 whitespace-pre-wrap font-sans text-sm">
                    {activeReport.content_markdown}
                  </div>
                </article>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
