import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi, aiApi, auditApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import { History as HistoryIcon, Shield, Activity, Calendar, Bot, CheckCircle } from 'lucide-react';

export default function History() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [investigations, setInvestigations] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('investigations'); // investigations or audit

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [caseRes, invRes, auditRes] = await Promise.all([
          caseApi.get(id),
          aiApi.getInvestigations(id),
          auditApi.getCaseLogs(id),
        ]);
        setCaseData(caseRes.data.data.case);
        setInvestigations(invRes.data.data.investigations || []);
        setAuditLogs(auditRes.data.data.audit_logs || []);
      } catch (e) {
        console.error(e);
      }
    };
    fetchData();
  }, [id]);

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading case history...</div>;

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
              <HistoryIcon className="w-5 h-5 text-emerald-400" />
              Investigation Memory & Audit Trail
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Case-scoped immutable records of past AI inquiries, executed tools, and investigator actions.
            </p>
          </div>

          <div className="flex rounded-lg bg-slate-950 p-1 border border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('investigations')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeTab === 'investigations' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-white'
              }`}
            >
              AI Sessions ({investigations.length})
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeTab === 'audit' ? 'bg-slate-800 text-emerald-400' : 'text-slate-400 hover:text-white'
              }`}
            >
              Audit Trail ({auditLogs.length})
            </button>
          </div>
        </div>

        {activeTab === 'investigations' ? (
          <div className="space-y-4">
            {investigations.length === 0 ? (
              <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-xl">
                <Bot className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <p className="text-slate-300 text-sm">No past investigation sessions recorded.</p>
              </div>
            ) : (
              investigations.map((inv) => (
                <div key={inv.investigation_id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <span className="font-bold text-white text-xs">{inv.title}</span>
                    <span className="font-mono text-[10px] text-slate-400">{inv.created_at?.slice(0, 16).replace('T', ' ')}</span>
                  </div>

                  <div className="space-y-3">
                    {inv.messages?.map((m) => (
                      <div key={m.message_id} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-2 text-xs">
                        <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                          <span className="text-[10px] uppercase bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/30">
                            Q
                          </span>
                          <span>{m.user_question}</span>
                        </div>
                        <p className="text-slate-300 leading-relaxed font-sans line-clamp-3 pl-4 border-l-2 border-slate-800">
                          {m.response_text}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3.5">Timestamp</th>
                    <th className="px-5 py-3.5">Action</th>
                    <th className="px-5 py-3.5">Tool</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3.5 font-mono text-[11px] text-slate-400">
                        {log.timestamp?.slice(0, 19).replace('T', ' ')}
                      </td>
                      <td className="px-5 py-3.5 font-bold text-emerald-400">{log.action}</td>
                      <td className="px-5 py-3.5 font-mono text-cyan-400">{log.tool || '-'}</td>
                      <td className="px-5 py-3.5">
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                          {log.result_status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-slate-400">{log.ip_address || '127.0.0.1'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
