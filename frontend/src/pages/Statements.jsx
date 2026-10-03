import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { caseApi, statementApi } from '../api/client';
import CaseNav from '../components/CaseNav';
import StatusBadge from '../components/StatusBadge';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, RefreshCw, Paperclip } from 'lucide-react';

export default function Statements() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [statements, setStatements] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccountId, setSelectedAccountId] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchStatements = async () => {
    try {
      const [caseRes, stmtRes, accRes] = await Promise.all([
        caseApi.get(id),
        statementApi.list(id),
        caseApi.getAccounts(id),
      ]);
      setCaseData(caseRes.data.data.case);
      setStatements(stmtRes.data.data.statements || []);
      setAccounts(accRes.data.data.accounts || []);
    } catch (e) {
      console.error('Failed to load statements', e);
    }
  };

  useEffect(() => {
    fetchStatements();
  }, [id]);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });
    if (selectedAccountId) {
      formData.append('account_id', selectedAccountId);
    }

    try {
      const res = await statementApi.upload(id, formData);
      setMessage({ type: 'success', text: res.data.message || 'Statements uploaded and normalized successfully!' });
      setSelectedFiles([]);
      await fetchStatements();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.error?.message || 'Failed to process statement upload.',
      });
    } finally {
      setUploading(false);
    }
  };

  if (!caseData) return <div className="text-center py-20 text-slate-400">Loading statements...</div>;

  return (
    <div>
      <CaseNav
        caseId={caseData.case_id}
        caseNumber={caseData.case_number}
        title={caseData.title}
        score={caseData.suspicion_score}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Upload Box */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-emerald-400" />
                Upload Multi-Bank Statements
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Upload PDF (digital/scanned with OCR), CSV, Excel (XLSX), or Images (PNG/JPG).
              </p>
            </div>

            {accounts.length > 0 && (
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400">Target Account:</label>
                <select
                  value={selectedAccountId}
                  onChange={(e) => setSelectedAccountId(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Auto-Detect from Statement</option>
                  {accounts.map((a) => (
                    <option key={a.account_id} value={a.account_id}>
                      {a.bank_name} ({a.account_number})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {message && (
            <div
              className={`p-3 rounded-lg flex items-center gap-2 text-xs border ${
                message.type === 'success'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
              }`}
            >
              {message.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
              <span>{message.text}</span>
            </div>
          )}

          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-slate-800 hover:border-emerald-500/50 rounded-xl p-8 text-center transition-all bg-slate-950/60"
          >
            <input
              type="file"
              id="file-upload"
              multiple
              accept=".pdf,.csv,.xlsx,.xls,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
              <div className="p-3 bg-slate-900 border border-slate-800 rounded-full mb-3 text-slate-400">
                <UploadCloud className="w-8 h-8 text-emerald-400" />
              </div>
              <p className="text-sm font-semibold text-slate-200">
                Drag & drop statements here, or <span className="text-emerald-400 underline underline-offset-4">browse files</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">Supports PDF, CSV, Excel (XLSX/XLS), PNG, JPG</p>
            </label>

            {selectedFiles.length > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-800/80 max-w-md mx-auto text-left">
                <p className="text-xs font-semibold text-slate-300 mb-2">Selected Files ({selectedFiles.length}):</p>
                <ul className="space-y-1.5 text-xs text-slate-400 font-mono">
                  {selectedFiles.map((f, i) => (
                    <li key={i} className="flex items-center gap-1.5 truncate">
                      <Paperclip className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span className="truncate">{f.name}</span>
                      <span className="text-slate-400 shrink-0">({(f.size / 1024).toFixed(0)} KB)</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="mt-4 w-full py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${uploading ? 'animate-spin' : ''}`} />
                  <span>{uploading ? 'Processing Statements & Running Normalizer...' : 'Upload & Process All'}</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Statements Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
          <div className="p-5 border-b border-slate-800">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
              Uploaded Statements & Extraction Provenance ({statements.length})
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Filename</th>
                  <th className="px-5 py-3.5">Format</th>
                  <th className="px-5 py-3.5">Bank Name</th>
                  <th className="px-5 py-3.5">Account #</th>
                  <th className="px-5 py-3.5">Pages</th>
                  <th className="px-5 py-3.5">Method</th>
                  <th className="px-5 py-3.5">Transactions</th>
                  <th className="px-5 py-3.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {statements.map((s) => (
                  <tr key={s.statement_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-5 py-4 font-medium text-white flex items-center gap-2">
                      <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>{s.original_filename}</span>
                    </td>
                    <td className="px-5 py-4 font-mono">{s.file_type}</td>
                    <td className="px-5 py-4 font-semibold text-slate-200">{s.bank_name || 'N/A'}</td>
                    <td className="px-5 py-4 font-mono text-slate-400">{s.account_number || 'N/A'}</td>
                    <td className="px-5 py-4 font-mono">{s.page_count}</td>
                    <td className="px-5 py-4">
                      <span className="font-mono text-[10px] bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-slate-300">
                        {s.extraction_method}
                      </span>
                    </td>
                    <td className="px-5 py-4 font-mono font-bold text-white">{s.transactions_count}</td>
                    <td className="px-5 py-4">
                      <StatusBadge status={s.processing_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
