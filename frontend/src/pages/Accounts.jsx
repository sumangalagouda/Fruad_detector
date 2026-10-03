import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import StatusBadge from '../components/StatusBadge';
import { CreditCard, Landmark, Plus, CheckCircle2 } from 'lucide-react';

export default function Accounts() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAcc, setNewAcc] = useState({
    bank_name: '',
    account_number: '',
    account_holder: '',
    account_type: 'SAVINGS',
    currency: 'INR',
    branch: '',
  });

  const fetchData = async () => {
    try {
      const [caseRes, accRes] = await Promise.all([caseApi.get(id), caseApi.getAccounts(id)]);
      setCaseData(caseRes.data.data.case);
      setAccounts(accRes.data.data.accounts || []);
    } catch (e) {
      console.error('Failed to load accounts', e);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleAddAccount = async (e) => {
    e.preventDefault();
    try {
      await caseApi.addAccount(id, newAcc);
      setShowAddModal(false);
      setNewAcc({
        bank_name: '',
        account_number: '',
        account_holder: '',
        account_type: 'SAVINGS',
        currency: 'INR',
        branch: '',
      });
      await fetchData();
    } catch (e) {
      console.error('Failed to add account', e);
    }
  };

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading accounts...</div>;

  return (
    <div>
      <CaseNav
        caseId={caseData.case_id}
        caseNumber={caseData.case_number}
        title={caseData.title}
        score={caseData.suspicion_score}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-extrabold text-white tracking-tight">Multi-Bank Account Identities</h1>
            <p className="text-xs text-slate-400 mt-1">
              Maintains strict cryptographic and relational identity across all institutional bank accounts of the subject.
            </p>
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs shadow-md shadow-emerald-500/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Add Account</span>
          </button>
        </div>

        {/* Account Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {accounts.map((acc) => (
            <div key={acc.account_id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-purple-500/10 border border-purple-500/30 rounded-lg text-purple-400">
                    <Landmark className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-sm">{acc.bank_name}</h3>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider">{acc.account_type}</span>
                  </div>
                </div>
                <StatusBadge status={acc.status} />
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Account Number:</span>
                  <span className="font-mono font-bold text-slate-200">{acc.account_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Account Holder:</span>
                  <span className="text-slate-200 font-medium">{acc.account_holder || caseData.person?.full_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Currency:</span>
                  <span className="font-mono text-slate-300">{acc.currency}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Transactions:</span>
                  <span className="font-mono font-bold text-emerald-400">{acc.transactions_count}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Modal for adding account */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-md shadow-2xl space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Register Institutional Account</h3>
              <form onSubmit={handleAddAccount} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Bank Name *</label>
                  <input
                    type="text"
                    required
                    value={newAcc.bank_name}
                    onChange={(e) => setNewAcc({ ...newAcc, bank_name: e.target.value })}
                    placeholder="e.g. Standard Chartered"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Account Number *</label>
                  <input
                    type="text"
                    required
                    value={newAcc.account_number}
                    onChange={(e) => setNewAcc({ ...newAcc, account_number: e.target.value })}
                    placeholder="e.g. 98765432100"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Account Type</label>
                  <select
                    value={newAcc.account_type}
                    onChange={(e) => setNewAcc({ ...newAcc, account_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="SAVINGS">SAVINGS</option>
                    <option value="CURRENT">CURRENT</option>
                    <option value="CHECKING">CHECKING</option>
                    <option value="CREDIT">CREDIT</option>
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-3 py-1.5 border border-slate-800 rounded-lg text-slate-300 hover:bg-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg"
                  >
                    Save Account
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
