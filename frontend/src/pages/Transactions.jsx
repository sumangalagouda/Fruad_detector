import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi, transactionApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import StatusBadge from '../components/StatusBadge';
import { Search, Filter, ArrowDownRight, ArrowUpRight, FileText, ChevronLeft, ChevronRight } from 'lucide-react';

export default function Transactions() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [query, setQuery] = useState('');
  const [selectedAccount, setSelectedAccount] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [minAmount, setMinAmount] = useState('');

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 25,
        query: query || undefined,
        account_id: selectedAccount || undefined,
        status: statusFilter || undefined,
        transaction_type: typeFilter || undefined,
        min_amount: minAmount ? parseFloat(minAmount) : undefined,
      };
      const res = await transactionApi.list(id, params);
      setTransactions(res.data.data.transactions || []);
      setTotalCount(res.data.data.total || 0);
    } catch (e) {
      console.error('Failed to load transactions', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadInit = async () => {
      try {
        const [caseRes, accRes] = await Promise.all([caseApi.get(id), caseApi.getAccounts(id)]);
        setCaseData(caseRes.data.data.case);
        setAccounts(accRes.data.data.accounts || []);
      } catch (e) {
        console.error(e);
      }
    };
    loadInit();
  }, [id]);

  useEffect(() => {
    fetchTransactions();
  }, [id, page, selectedAccount, statusFilter, typeFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTransactions();
  };

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading transactions...</div>;

  const totalPages = Math.ceil(totalCount / 25) || 1;

  return (
    <div>
      <CaseNav
        caseId={caseData.case_id}
        caseNumber={caseData.case_number}
        title={caseData.title}
        score={caseData.suspicion_score}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header & Filter Controls */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h1 className="text-xl font-extrabold text-white tracking-tight">
              Canonical Transactions ({totalCount})
            </h1>

            {/* Quick Status Explanatory Note */}
            <p className="text-xs text-slate-400">
              Preserves verified financial provenance. Failed and reversed transactions are retained for investigation.
            </p>
          </div>

          <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
            <div className="relative lg:col-span-2">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search description, reference, counterparty, account..."
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <select
                value={selectedAccount}
                onChange={(e) => {
                  setSelectedAccount(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="">All Accounts</option>
                {accounts.map((a) => (
                  <option key={a.account_id} value={a.account_id}>
                    {a.bank_name} ({a.account_number.slice(-4)})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="">All Statuses</option>
                <option value="SUCCESS">SUCCESS</option>
                <option value="FAILED">FAILED</option>
                <option value="REVERSED">REVERSED</option>
                <option value="RETURNED">RETURNED</option>
                <option value="REFUNDED">REFUNDED</option>
                <option value="PENDING">PENDING</option>
              </select>
            </div>

            <div className="flex gap-2">
              <input
                type="number"
                value={minAmount}
                onChange={(e) => setMinAmount(e.target.value)}
                placeholder="Min Amount (₹)"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-emerald-500"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg shrink-0 transition-colors"
              >
                Apply
              </button>
            </div>
          </form>
        </div>

        {/* Transactions Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3.5">ID / Ref</th>
                  <th className="px-4 py-3.5">Date</th>
                  <th className="px-4 py-3.5">Bank / Account</th>
                  <th className="px-4 py-3.5">Description & Counterparty</th>
                  <th className="px-4 py-3.5 text-right">Debit (₹)</th>
                  <th className="px-4 py-3.5 text-right">Credit (₹)</th>
                  <th className="px-4 py-3.5 text-right">Balance (₹)</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={9} className="text-center py-12 text-slate-400">
                      Loading transactions...
                    </td>
                  </tr>
                ) : transactions.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-12 text-slate-400">
                      No transactions matched the criteria.
                    </td>
                  </tr>
                ) : (
                  transactions.map((tx) => (
                    <tr key={tx.transaction_id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-4 py-3.5">
                        <span className="font-mono font-bold text-emerald-400 block">{tx.transaction_id}</span>
                        {tx.reference_number && (
                          <span className="text-[10px] font-mono text-slate-400 block">{tx.reference_number}</span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap font-mono text-[11px] text-slate-300">
                        {tx.transaction_date ? tx.transaction_date.slice(0, 16).replace('T', ' ') : 'N/A'}
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="font-semibold text-slate-200 block">{tx.bank_name}</span>
                        <span className="font-mono text-[10px] text-slate-400">Acc: {tx.account_number}</span>
                      </td>
                      <td className="px-4 py-3.5 max-w-xs">
                        <p className="line-clamp-2 text-slate-200">{tx.description}</p>
                        {tx.counterparty_name && (
                          <span className="inline-block mt-0.5 text-[10px] px-1.5 py-0.2 rounded bg-slate-950 text-cyan-400 border border-slate-800 font-mono">
                            CP: {tx.counterparty_name}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 text-right font-mono text-rose-400 font-medium">
                        {tx.debit > 0 ? `₹${tx.debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
                      </td>
                      <td className="px-4 py-3.5 text-right font-mono text-emerald-400 font-medium">
                        {tx.credit > 0 ? `₹${tx.credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
                      </td>
                      <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                        {tx.balance !== null && tx.balance !== undefined
                          ? `₹${tx.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                          : '-'}
                      </td>
                      <td className="px-4 py-3.5">
                        <StatusBadge status={tx.status} />
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono" title={tx.source_file}>
                          <FileText className="w-3 h-3 text-slate-400" />
                          <span className="truncate max-w-[90px]">{tx.source_file}</span>
                          <span>p.{tx.source_page}</span>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <div>
              Showing page <span className="font-mono font-bold text-white">{page}</span> of{' '}
              <span className="font-mono font-bold text-white">{totalPages}</span> ({totalCount} total)
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
