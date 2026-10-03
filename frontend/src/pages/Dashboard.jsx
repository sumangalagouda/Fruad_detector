import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { caseApi, auditApi } from '../api/client';
import {
  FolderOpen,
  ShieldAlert,
  FileText,
  CreditCard,
  AlertTriangle,
  Activity,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

export default function Dashboard() {
  const [cases, setCases] = useState([]);
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [casesRes, auditRes] = await Promise.all([
          caseApi.list(),
          auditApi.getAllLogs().catch(() => ({ data: { data: { audit_logs: [] } } })),
        ]);
        setCases(casesRes.data.data.cases || []);
        setRecentLogs(auditRes.data.data.audit_logs?.slice(0, 6) || []);
      } catch (e) {
        console.error('Dashboard load error', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalCases = cases.length;
  const totalStatements = cases.reduce((acc, c) => acc + (c.statements_count || 0), 0);
  const totalAccounts = cases.reduce((acc, c) => acc + (c.accounts_count || 0), 0);
  const totalTransactions = cases.reduce((acc, c) => acc + (c.transactions_count || 0), 0);
  const totalSuspicious = cases.reduce((acc, c) => acc + (c.suspicious_count || 0), 0);

  // Risk breakdown chart data
  const riskData = [
    { name: 'Critical (>70)', count: cases.filter((c) => (c.suspicion_score || 0) >= 70).length, color: '#f43f5e' },
    { name: 'High (50-70)', count: cases.filter((c) => (c.suspicion_score || 0) >= 50 && (c.suspicion_score || 0) < 70).length, color: '#f59e0b' },
    { name: 'Medium (25-50)', count: cases.filter((c) => (c.suspicion_score || 0) >= 25 && (c.suspicion_score || 0) < 50).length, color: '#eab308' },
    { name: 'Low (<25)', count: cases.filter((c) => (c.suspicion_score || 0) < 25).length, color: '#10b981' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Investigation Operations Center</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time intelligence across multi-bank financial statements, relationship graphs, and AI agents.
          </p>
        </div>
        <Link
          to="/cases/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-sm shadow-lg shadow-emerald-500/20 transition-all"
        >
          <span>Create New Case</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Cases</span>
            <FolderOpen className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-white">{totalCases}</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Statements</span>
            <FileText className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-white">{totalStatements}</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Accounts</span>
            <CreditCard className="w-5 h-5 text-purple-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-white">{totalAccounts}</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Transactions</span>
            <Activity className="w-5 h-5 text-cyan-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-white">{totalTransactions}</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Suspicious Flags</span>
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-amber-400">{totalSuspicious}</p>
        </div>
      </div>

      {/* Analytics Charts & Risk Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Chart */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow col-span-2">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            Cases Risk Tier Distribution
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Audit Events */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-400" />
            Recent Investigation Events
          </h3>
          <div className="space-y-3">
            {recentLogs.length === 0 ? (
              <p className="text-xs text-slate-400">No events recorded yet.</p>
            ) : (
              recentLogs.map((log) => (
                <div key={log.id} className="text-xs border-b border-slate-800/80 pb-2">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="font-semibold text-emerald-400">{log.action}</span>
                    <span className="text-[10px] text-slate-400">{log.timestamp ? log.timestamp.slice(11, 19) : ''}</span>
                  </div>
                  {log.tool && <p className="text-slate-400 text-[11px] mt-0.5">Tool: {log.tool}</p>}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Active Cases Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Active Investigation Cases</h3>
          <Link to="/cases" className="text-xs text-emerald-400 hover:text-emerald-300 font-medium">
            View all cases →
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-semibold border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Case #</th>
                <th className="px-5 py-3.5">Subject Person</th>
                <th className="px-5 py-3.5">Statements</th>
                <th className="px-5 py-3.5">Accounts</th>
                <th className="px-5 py-3.5">Transactions</th>
                <th className="px-5 py-3.5">Suspicious</th>
                <th className="px-5 py-3.5">Suspicion Score</th>
                <th className="px-5 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {cases.slice(0, 5).map((c) => (
                <tr key={c.case_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-5 py-4 font-mono font-medium text-emerald-400">{c.case_number}</td>
                  <td className="px-5 py-4 font-semibold text-white">{c.person?.full_name || 'Unknown'}</td>
                  <td className="px-5 py-4 font-mono">{c.statements_count}</td>
                  <td className="px-5 py-4 font-mono">{c.accounts_count}</td>
                  <td className="px-5 py-4 font-mono">{c.transactions_count}</td>
                  <td className="px-5 py-4 font-mono text-amber-400 font-bold">{c.suspicious_count}</td>
                  <td className="px-5 py-4">
                    <span className="font-mono font-bold text-white px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                      {c.suspicion_score?.toFixed(1) || '0.0'}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <Link
                      to={`/cases/${c.case_id}`}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-slate-800 hover:bg-emerald-500 hover:text-slate-950 font-semibold rounded text-slate-200 transition-colors"
                    >
                      Open Case
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
