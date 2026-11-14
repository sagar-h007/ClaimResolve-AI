import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { formatCurrency, STATUS_COLORS } from '../lib/utils';
import {
  FileText,
  Search,
  Plus,
  Filter,
  Sparkles,
  ChevronRight,
  ExternalLink,
  X,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export default function ClaimsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New claim form state
  const [formData, setFormData] = useState({
    payer_name: 'United Healthcare',
    policy_number_masked: 'POL-****-4821',
    procedure_codes: '29881, 73721',
    diagnosis_codes: 'M23.22, M25.561',
    claim_amount: 5400,
    denied_amount: 4850,
    denial_date: '2025-08-14',
    denial_reason: 'Non-covered service: Insufficient medical necessity records for conservative therapy.',
    denial_code: 'CO-50',
    patient_first_name: 'David',
    patient_last_name: 'Miller',
    patient_dob: '1979-06-22',
  });

  const queryParams = new URLSearchParams();
  if (search) queryParams.set('search', search);
  if (statusFilter) queryParams.set('status', statusFilter);
  queryParams.set('limit', '50');

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['claims', search, statusFilter],
    queryFn: () => api.getClaims(queryParams.toString()),
  });

  const createClaimMutation = useMutation({
    mutationFn: (newClaim: any) => api.createClaim(newClaim),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claims'] });
      setIsModalOpen(false);
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      payer_name: formData.payer_name,
      policy_number_masked: formData.policy_number_masked,
      procedure_codes: formData.procedure_codes.split(',').map((s) => s.trim()).filter(Boolean),
      diagnosis_codes: formData.diagnosis_codes.split(',').map((s) => s.trim()).filter(Boolean),
      claim_amount: Number(formData.claim_amount),
      denied_amount: Number(formData.denied_amount),
      denial_date: formData.denial_date,
      denial_reason: formData.denial_reason,
      denial_code: formData.denial_code,
      patient_first_name: formData.patient_first_name,
      patient_last_name: formData.patient_last_name,
      patient_dob: formData.patient_dob,
    };
    createClaimMutation.mutate(payload);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Claims Ingestion & Management</h1>
          <p className="text-sm text-slate-500 mt-1">
            Review denied hospital claims, associated EOB codes, clinical documents, and appeal stages.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg shadow-sm shadow-brand-500/20 transition"
        >
          <Plus className="w-4 h-4" />
          Create New Claim
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search claim #, payer name, denial code, or reason..."
            className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500 text-slate-700 bg-white"
            >
              <option value="">All Statuses</option>
              <option value="Uploaded">Uploaded</option>
              <option value="Processing">Processing</option>
              <option value="Analysis Complete">Analysis Complete</option>
              <option value="Appeal Drafted">Appeal Drafted</option>
              <option value="Pending Review">Pending Review</option>
              <option value="Submitted">Submitted</option>
              <option value="Approved">Approved</option>
              <option value="Rejected">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Claims Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Claim ID & Patient</th>
                <th className="px-6 py-3.5">Payer & Policy</th>
                <th className="px-6 py-3.5">Denial Code & Grounds</th>
                <th className="px-6 py-3.5">Denied Amount</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(data?.items || []).map((claim: any) => (
                <tr key={claim.id} className="hover:bg-slate-50/80 transition">
                  <td className="px-6 py-4">
                    <Link
                      to={`/claims/${claim.id}`}
                      className="font-semibold text-slate-900 hover:text-brand-600 transition"
                    >
                      {claim.claim_number}
                    </Link>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {claim.patient
                        ? `${claim.patient.first_name} ${claim.patient.last_name} (DOB: ${claim.patient.dob})`
                        : 'Unassigned Patient'}
                    </p>
                  </td>

                  <td className="px-6 py-4">
                    <span className="font-medium text-slate-800">{claim.payer_name}</span>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">{claim.policy_number_masked}</p>
                  </td>

                  <td className="px-6 py-4 max-w-xs">
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">
                        {claim.denial_code || 'CO-50'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 truncate">{claim.denial_reason || 'Medical Necessity'}</p>
                  </td>

                  <td className="px-6 py-4">
                    <span className="font-bold text-slate-900">{formatCurrency(claim.denied_amount)}</span>
                    <p className="text-xs text-slate-400 mt-0.5">Claim: {formatCurrency(claim.claim_amount)}</p>
                  </td>

                  <td className="px-6 py-4">
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                        STATUS_COLORS[claim.claim_status] || 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {claim.claim_status}
                    </span>
                  </td>

                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        to={`/claims/${claim.id}/analysis`}
                        title="AI Analysis & Evidence"
                        className="p-1.5 text-brand-600 hover:bg-brand-50 rounded-lg transition"
                      >
                        <Sparkles className="w-4 h-4" />
                      </Link>
                      <Link
                        to={`/claims/${claim.id}/appeal`}
                        title="Generate/Edit Appeal Letter"
                        className="p-1.5 text-slate-600 hover:bg-slate-100 rounded-lg transition"
                      >
                        <FileText className="w-4 h-4" />
                      </Link>
                      <Link
                        to={`/claims/${claim.id}`}
                        title="Details"
                        className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg transition"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}

              {(!data || data.items?.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-400 text-sm">
                    No claims match your search criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Claim Creation Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">Create New Medical Claim</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Patient First Name</label>
                  <input
                    type="text"
                    required
                    value={formData.patient_first_name}
                    onChange={(e) => setFormData({ ...formData, patient_first_name: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Patient Last Name</label>
                  <input
                    type="text"
                    required
                    value={formData.patient_last_name}
                    onChange={(e) => setFormData({ ...formData, patient_last_name: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Date of Birth</label>
                  <input
                    type="date"
                    required
                    value={formData.patient_dob}
                    onChange={(e) => setFormData({ ...formData, patient_dob: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Payer Organization</label>
                  <input
                    type="text"
                    required
                    value={formData.payer_name}
                    onChange={(e) => setFormData({ ...formData, payer_name: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Policy / Member ID</label>
                  <input
                    type="text"
                    required
                    value={formData.policy_number_masked}
                    onChange={(e) => setFormData({ ...formData, policy_number_masked: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Denial Code (CARC)</label>
                  <input
                    type="text"
                    required
                    value={formData.denial_code}
                    onChange={(e) => setFormData({ ...formData, denial_code: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                    placeholder="CO-50, CO-16..."
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Procedure Codes (CPT)</label>
                  <input
                    type="text"
                    required
                    value={formData.procedure_codes}
                    onChange={(e) => setFormData({ ...formData, procedure_codes: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                    placeholder="29881, 73721"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Diagnosis Codes (ICD-10)</label>
                  <input
                    type="text"
                    required
                    value={formData.diagnosis_codes}
                    onChange={(e) => setFormData({ ...formData, diagnosis_codes: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                    placeholder="M23.22, M25.561"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Claim Amount ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.claim_amount}
                    onChange={(e) => setFormData({ ...formData, claim_amount: Number(e.target.value) })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Denied Amount ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.denied_amount}
                    onChange={(e) => setFormData({ ...formData, denied_amount: Number(e.target.value) })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Denial Reason Stated by Payer</label>
                <textarea
                  rows={3}
                  required
                  value={formData.denial_reason}
                  onChange={(e) => setFormData({ ...formData, denial_reason: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createClaimMutation.isPending}
                  className="px-4 py-2 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition disabled:opacity-50"
                >
                  {createClaimMutation.isPending ? 'Creating...' : 'Create Claim Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

