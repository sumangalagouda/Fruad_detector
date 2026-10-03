import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { caseApi } from '../api/client';
import { FolderPlus, User, ShieldAlert, ArrowRight, AlertCircle } from 'lucide-react';

export default function CreateCase() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'HIGH',
    person: {
      full_name: '',
      identifier_type: 'PAN',
      identifier_value: '',
      date_of_birth: '',
      address: '',
      phone: '',
      email: '',
      notes: '',
    },
  });

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handlePersonChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      person: { ...prev.person, [field]: value },
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await caseApi.create(formData);
      const newCase = res.data.data.case;
      // Navigate straight to statement upload tab for the new case
      navigate(`/cases/${newCase.case_id}/statements`);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to create case.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Create Financial Crime Case</h1>
        <p className="text-sm text-slate-400 mt-1">
          Initiate an investigation file for a person subject to multi-account financial scrutiny.
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-rose-400 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Case Details */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <FolderPlus className="w-4 h-4 text-emerald-400" />
            Case Information
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">Case Title *</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                placeholder="e.g. Investigation: Suspected Corporate Dispersals - John Doe"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => handleChange('priority', e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Case Description</label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Background context, investigative mandate, or preliminary intelligence notes..."
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        {/* Section 2: Person Under Investigation */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <User className="w-4 h-4 text-blue-400" />
            Subject Person Identity
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Subject Full Name *</label>
              <input
                type="text"
                required
                value={formData.person.full_name}
                onChange={(e) => handlePersonChange('full_name', e.target.value)}
                placeholder="John Doe"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">ID Type</label>
                <select
                  value={formData.person.identifier_type}
                  onChange={(e) => handlePersonChange('identifier_type', e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="PAN">PAN (Income Tax)</option>
                  <option value="SSN">SSN</option>
                  <option value="PASSPORT">Passport</option>
                  <option value="NATIONAL_ID">National ID</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">ID Number</label>
                <input
                  type="text"
                  value={formData.person.identifier_value}
                  onChange={(e) => handlePersonChange('identifier_value', e.target.value)}
                  placeholder="ABCDE1234F"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Date of Birth</label>
              <input
                type="date"
                value={formData.person.date_of_birth}
                onChange={(e) => handlePersonChange('date_of_birth', e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Phone Number</label>
              <input
                type="text"
                value={formData.person.phone}
                onChange={(e) => handlePersonChange('phone', e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Address</label>
            <input
              type="text"
              value={formData.person.address}
              onChange={(e) => handlePersonChange('address', e.target.value)}
              placeholder="742 Evergreen Terrace, Sector 4, Financial District"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/cases')}
            className="px-4 py-2 border border-slate-800 rounded-lg text-xs text-slate-300 hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            <span>{loading ? 'Creating Case...' : 'Create Case & Upload Statements'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
