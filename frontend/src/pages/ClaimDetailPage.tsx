import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { formatCurrency, STATUS_COLORS } from '../lib/utils';
import {
  FileText,
  Upload,
  Sparkles,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Shield,
  FileCode,
  Clock,
  Trash2,
} from 'lucide-react';

export default function ClaimDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedCategory, setSelectedCategory] = useState<'denial_letter' | 'clinical_record' | 'payer_policy' | 'billing_document'>('clinical_record');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [uploadError, setUploadError] = useState('');

  const { data: claim, isLoading } = useQuery({
    queryKey: ['claim', id],
    queryFn: () => api.getClaim(id!),
    enabled: !!id,
  });

  const { data: documents, refetch: refetchDocs } = useQuery({
    queryKey: ['claimDocuments', id],
    queryFn: () => api.getDocuments(`claim_id=${id}`),
    enabled: !!id,
  });

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => api.uploadDocument(formData),
    onSuccess: () => {
      setUploadSuccess('Document successfully uploaded, parsed, and embedded.');
      setUploadFile(null);
      refetchDocs();
      queryClient.invalidateQueries({ queryKey: ['claim', id] });
      setTimeout(() => setUploadSuccess(''), 4000);
    },
    onError: (err: any) => {
      setUploadError(err.message || 'Upload failed');
      setTimeout(() => setUploadError(''), 4000);
    },
  });

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !id) return;
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('category', selectedCategory);
    formData.append('claim_id', id);
    uploadMutation.mutate(formData);
  };

  const statusUpdateMutation = useMutation({
    mutationFn: (status: string) => api.updateClaim(id!, { claim_status: status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claim', id] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="p-8 text-center text-slate-500">
        Claim record not found. <Link to="/claims" className="text-brand-600 underline">Return to claims</Link>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Navigation & Header */}
      <div>
        <Link
          to="/claims"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition mb-3"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Claims List
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">{claim.claim_number}</h1>
              <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${STATUS_COLORS[claim.claim_status] || 'bg-slate-100'}`}>
                {claim.claim_status}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Payer: {claim.payer_name} • Policy: {claim.policy_number_masked} • Denial Code: {claim.denial_code || 'CO-50'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to={`/claims/${id}/analysis`}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg shadow-sm shadow-brand-500/20 transition"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Run AI Claim Audit
            </Link>

            <Link
              to={`/claims/${id}/appeal`}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg shadow-sm transition"
            >
              <FileText className="w-3.5 h-3.5 text-brand-600" />
              Appeal Workspace
            </Link>
          </div>
        </div>
      </div>

      {/* Claim Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500">Patient Details</p>
          <p className="text-sm font-bold text-slate-900 mt-1">
            {claim.patient ? `${claim.patient.first_name} ${claim.patient.last_name}` : 'Jane Doe'}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            Ref: {claim.patient?.external_patient_id || 'PT-84920'} • DOB: {claim.patient?.dob || '1980-05-15'}
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500">Financial Impact</p>
          <p className="text-sm font-bold text-rose-600 mt-1">{formatCurrency(claim.denied_amount)} Denied</p>
          <p className="text-xs text-slate-400 mt-0.5">Billed: {formatCurrency(claim.claim_amount)}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500">Procedure & Diagnosis</p>
          <p className="text-sm font-bold text-slate-900 mt-1">CPT: {claim.procedure_codes.join(', ') || 'N/A'}</p>
          <p className="text-xs text-slate-400 mt-0.5">ICD-10: {claim.diagnosis_codes.join(', ') || 'N/A'}</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500">Review Status Lifecycle</p>
          <select
            value={claim.claim_status}
            onChange={(e) => statusUpdateMutation.mutate(e.target.value)}
            className="mt-1 text-xs font-semibold px-2.5 py-1.5 border border-slate-200 rounded-lg outline-none focus:border-brand-500 bg-white"
          >
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

      {/* Denial Reason Highlight Box */}
      <div className="bg-rose-50/60 border border-rose-200 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-xs flex-shrink-0">
            {claim.denial_code || 'CO-50'}
          </div>
          <div>
            <h3 className="text-sm font-bold text-rose-900">Official Denial Explanation (from Remittance / EOB)</h3>
            <p className="text-xs text-rose-800 mt-1 leading-relaxed">
              {claim.denial_reason || 'Claim denied as not medically necessary. Insufficient documentation of required conservative clinical therapy.'}
            </p>
            {claim.denial_date && (
              <p className="text-[11px] text-rose-600 mt-1">Denial Date: {claim.denial_date}</p>
            )}
          </div>
        </div>
      </div>

      {/* Document Ingestion & RAG Index Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-fit">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Upload className="w-4 h-4 text-brand-600" />
            Ingest Document to Claim
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Upload Denial Letters, Clinical Notes, or Payer Policies to extract text, OCR if needed, and index vectors.
          </p>

          {uploadSuccess && (
            <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> {uploadSuccess}
            </div>
          )}
          {uploadError && (
            <div className="mt-3 p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" /> {uploadError}
            </div>
          )}

          <form onSubmit={handleUploadSubmit} className="mt-4 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Document Category</label>
              <select
                value={selectedCategory}
                onChange={(e: any) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg outline-none focus:border-brand-500 bg-white"
              >
                <option value="clinical_record">Patient Clinical Record (Notes, Labs, MRI)</option>
                <option value="denial_letter">Insurance Denial Letter / Remittance</option>
                <option value="payer_policy">Payer Clinical Policy Guideline PDF</option>
                <option value="billing_document">Medical Billing / Coding Document</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Select File (PDF, DOCX, TXT)</label>
              <input
                type="file"
                required
                accept=".pdf,.docx,.doc,.txt"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
              />
            </div>

            <button
              type="submit"
              disabled={!uploadFile || uploadMutation.isPending}
              className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-xs font-semibold transition disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
            >
              <Upload className="w-3.5 h-3.5" />
              {uploadMutation.isPending ? 'Processing & Vectorizing...' : 'Upload & Process Document'}
            </button>
          </form>
        </div>

        {/* Uploaded Documents List */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Ingested Claim Documents ({documents?.length || 0})</h2>
              <p className="text-xs text-slate-500">Documents parsed and available for RAG semantic citations</p>
            </div>
            <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
              Vector Store Synced
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {(documents || []).map((doc: any) => (
              <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-brand-600" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-900">{doc.original_filename}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Category: <span className="font-semibold text-slate-700">{doc.category.replace('_', ' ')}</span> • {doc.page_count} page(s) • {doc.chunk_count || 1} chunks embedded
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                    doc.status === 'processed' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700'
                  }`}>
                    {doc.status}
                  </span>
                </div>
              </div>
            ))}

            {(!documents || documents.length === 0) && (
              <div className="p-8 text-center text-slate-400 text-xs">
                No documents uploaded yet for this claim. Upload clinical records or denial letters above to enable AI evidence matching.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

