import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { caseApi } from '../api/client';
import { FolderOpen, Plus, Search, Filter, ArrowUpRight, ShieldAlert } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';

export default function CaseList() {
  const [cases, setCases] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCases = async () => {
      try {
        const res = await caseApi.list(statusFilter || undefined);
        setCases(res.data.data.cases || []);
      } catch (e) {
        console.error('Failed to load cases', e);
      } finally {
        setLoading(false);
      }
    };
    fetchCases();
  }, [statusFilter]);

  const filtered = cases.filter((c) => {
    const term = search.toLowerCase();
    return (
      c.case_number?.toLowerCase().includes(term) ||
      c.title?.toLowerCase().includes(term) ||
      c.person?.full_name?.toLowerCase().includes(term) ||
      c.person?.identifier_value?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Investigation Cases</h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage multi-bank financial crime inquiries, statement uploads, and forensic intelligence.
          </p>
        </div>

        <Link
          to="/cases/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-sm shadow-lg shadow-emerald-500/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Case</span>
        </Link>
      </div>

      {/* Filters Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 shadow">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by case #, title, person name, or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="PENDING_REVIEW">PENDING_REVIEW</option>
            <option value="CLOSED">CLOSED</option>
          </select>
        </div>
      </div>

      {/* Cases Grid */}
      {loading ? (
        <div className="text-center py-16 text-slate-400 text-sm">Loading investigation cases...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-slate-900 border border-slate-800 rounded-xl">
          <FolderOpen className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <p className="text-slate-300 font-medium">No investigation cases found.</p>
          <p className="text-xs text-slate-400 mt-1">Create a new case to start uploading bank statements.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((c) => (
            <div
              key={c.case_id}
              className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-950 text-emerald-400 border border-slate-800 font-semibold">
                    {c.case_number}
                  </span>
                  <StatusBadge status={c.status} />
                </div>

                <h3 className="font-bold text-white text-base tracking-tight mb-1">{c.title}</h3>
                <p className="text-xs text-slate-400 line-clamp-2 mb-4">{c.description || 'No description provided.'}</p>

                <div className="bg-slate-950/80 rounded-lg p-3 border border-slate-800/80 space-y-2 mb-4 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Subject:</span>
                    <span className="font-semibold text-slate-200">{c.person?.full_name || 'Unknown'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Accounts / Stmts:</span>
                    <span className="font-mono text-slate-300">
                      {c.accounts_count} accs / {c.statements_count} stmts
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Suspicious Flags:</span>
                    <span className="font-mono font-bold text-amber-400">{c.suspicious_count}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Suspicion Score</span>
                  <span className="font-mono font-bold text-sm text-white">
                    {c.suspicion_score?.toFixed(1) || '0.0'}{' '}
                    <span className="text-[10px] text-slate-400 font-normal">/ 100</span>
                  </span>
                </div>

                <Link
                  to={`/cases/${c.case_id}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500 hover:text-slate-950 text-emerald-400 text-xs font-bold rounded-lg border border-emerald-500/30 transition-all"
                >
                  <span>Open</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
