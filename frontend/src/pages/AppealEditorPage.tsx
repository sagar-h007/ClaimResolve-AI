import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { formatCurrency, STATUS_COLORS, formatDate } from '../lib/utils';
import {
  FileText,
  Download,
  Save,
  CheckCircle,
  Sparkles,
  ArrowLeft,
  Clock,
  History,
  ShieldCheck,
  AlertCircle,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';

export default function AppealEditorPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [fullText, setFullText] = useState('');
  const [tone, setTone] = useState('formal_assertive');
  const [saveMsg, setSaveMsg] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const [activeTab, setActiveTab] = useState<'editor' | 'citations' | 'versions'>('editor');

  const { data: claim } = useQuery({
    queryKey: ['claim', id],
    queryFn: () => api.getClaim(id!),
    enabled: !!id,
  });

  const { data: appeal, isLoading, refetch } = useQuery({
    queryKey: ['claimAppeal', id],
    queryFn: () => api.getAppeal(id!),
    enabled: !!id,
    retry: false,
  });

  useEffect(() => {
    if (appeal?.full_letter_text) {
      setFullText(appeal.full_letter_text);
    }
  }, [appeal?.full_letter_text]);

  const generateMutation = useMutation({
    mutationFn: () => api.generateAppeal(id!, { tone }),
    onSuccess: (data) => {
      queryClient.setQueryData(['claimAppeal', id], data);
      setFullText(data.full_letter_text);
      setSaveMsg('New appeal draft generated successfully.');
      setTimeout(() => setSaveMsg(''), 4000);
    },
  });

  const saveMutation = useMutation({
    mutationFn: (newStatus?: string) => {
      if (!appeal) throw new Error('No appeal');
      const payload: any = { full_letter_text: fullText };
      if (newStatus) payload.status = newStatus;
      return api.updateAppeal(appeal.id, payload);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['claimAppeal', id], data);
      setSaveMsg('Appeal draft saved.');
      setTimeout(() => setSaveMsg(''), 3000);
    },
  });

  const handleExportPDF = async () => {
    if (!appeal) return;
    setIsExporting(true);
    try {
      const blob = await api.exportAppealPDF(appeal.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Appeal_${claim?.claim_number || id}_v${appeal.current_version}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert('PDF generation error: ' + err.message);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          to={`/claims/${id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition mb-3"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Claim #{claim?.claim_number || id}
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Insurance Appeal Letter Workspace</h1>
              {appeal && (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${STATUS_COLORS[appeal.status] || 'bg-slate-100'}`}>
                  {appeal.status.replace('_', ' ')} (v{appeal.current_version})
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Evidence-backed formal reconsideration demand citing verbatim clinical pages and payer coverage guidelines.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {appeal && (
              <>
                <button
                  onClick={() => saveMutation.mutate(undefined)}
                  disabled={saveMutation.isPending}
                  className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg shadow-sm transition disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  {saveMutation.isPending ? 'Saving...' : 'Save Draft'}
                </button>

                <button
                  onClick={handleExportPDF}
                  disabled={isExporting}
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg shadow-sm transition disabled:opacity-50"
                >
                  <Download className="w-3.5 h-3.5" />
                  {isExporting ? 'Generating PDF...' : 'Export Formal PDF'}
                </button>

                {appeal.status !== 'approved' && (
                  <button
                    onClick={() => saveMutation.mutate('approved')}
                    disabled={saveMutation.isPending}
                    className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg shadow-sm transition disabled:opacity-50"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    Approve for Submission
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {saveMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium rounded-lg flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600" /> {saveMsg}
        </div>
      )}

      {/* If no appeal exists yet */}
      {!appeal && !isLoading && (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 shadow-sm text-center max-w-xl mx-auto space-y-4">
          <div className="w-12 h-12 bg-brand-50 text-brand-600 rounded-xl flex items-center justify-center mx-auto">
            <FileText className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-slate-900">No Appeal Letter Drafted Yet</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            Generate an evidence-backed formal appeal letter synthesized from the claim's verified medical records and payer policy requirements.
          </p>

          <div className="flex items-center justify-center gap-3 pt-2">
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="text-xs px-3 py-2 border border-slate-200 rounded-lg outline-none bg-white"
            >
              <option value="formal_assertive">Tone: Formal & Assertive Legal Rebuttal</option>
              <option value="clinical_collaborative">Tone: Clinical Peer-to-Peer Review</option>
            </select>

            <button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-sm"
            >
              {generateMutation.isPending ? 'Generating Letter...' : 'Generate Appeal Letter'}
            </button>
          </div>
        </div>
      )}

      {/* Appeal Letter Editor Interface */}
      {appeal && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Document Editor Column */}
          <div className="lg:col-span-8 space-y-4">
            {/* Tab Controls */}
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab('editor')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                    activeTab === 'editor' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Appeal Text Editor
                </button>
                <button
                  onClick={() => setActiveTab('citations')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                    activeTab === 'citations' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Verified Citations ({appeal.supporting_document_references?.length || 0})
                </button>
                <button
                  onClick={() => setActiveTab('versions')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                    activeTab === 'versions' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  Version History ({appeal.versions?.length || 1})
                </button>
              </div>

              <button
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isPending}
                className="text-xs text-brand-600 hover:text-brand-800 font-semibold flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${generateMutation.isPending ? 'animate-spin' : ''}`} />
                Regenerate AI Draft
              </button>
            </div>

            {/* TAB 1: Editor */}
            {activeTab === 'editor' && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Full Formal Written Demand
                  </span>
                  <span className="text-[11px] text-slate-400">
                    Live editable draft • Auto-formats on PDF export
                  </span>
                </div>

                <textarea
                  value={fullText}
                  onChange={(e) => setFullText(e.target.value)}
                  rows={26}
                  className="w-full text-xs text-slate-800 font-mono leading-relaxed p-4 bg-slate-50/60 rounded-xl border border-slate-200 outline-none focus:bg-white focus:border-brand-500 transition resize-y"
                  placeholder="Appeal letter content..."
                />
              </div>
            )}

            {/* TAB 2: Verified Citations Table */}
            {activeTab === 'citations' && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                <h3 className="text-sm font-bold text-slate-900">Source Document Provenance Table</h3>
                <p className="text-xs text-slate-500">
                  Every factual assertion in this appeal links directly to an uploaded clinical record or published policy document.
                </p>

                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden mt-4">
                  {(appeal.supporting_document_references || []).map((item: any, idx: number) => (
                    <div key={idx} className="p-4 flex items-center justify-between bg-white hover:bg-slate-50 transition">
                      <div className="flex items-center gap-3">
                        <span className="w-7 h-7 rounded-lg bg-brand-50 text-brand-700 flex items-center justify-center font-bold text-xs">
                          {String.fromCharCode(65 + idx)}
                        </span>
                        <div>
                          <p className="text-xs font-bold text-slate-900">{item.title}</p>
                          <p className="text-[11px] text-slate-500">Page Citation: <span className="font-semibold text-slate-800">{item.page}</span></p>
                        </div>
                      </div>
                      <span className="px-2.5 py-1 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {Math.round((item.relevance || 0.95) * 100)}% Confidence
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 3: Version History */}
            {activeTab === 'versions' && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                <h3 className="text-sm font-bold text-slate-900">Document Revision History</h3>
                <p className="text-xs text-slate-500">
                  Track every manual revision and AI regeneration with full audit timestamps.
                </p>

                <div className="space-y-3 mt-4">
                  {(appeal.versions || []).map((ver: any) => (
                    <div key={ver.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center font-bold">
                          v{ver.version_number}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{ver.change_summary || 'Manual user edit'}</p>
                          <p className="text-slate-400 text-[10px]">{formatDate(ver.created_at)}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => setFullText(ver.full_letter_text)}
                        className="px-3 py-1.5 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg font-semibold text-slate-700 text-xs transition"
                      >
                        Restore Version
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Sidebar: Appeal Meta & Approval Status */}
          <div className="lg:col-span-4 space-y-6">
            {/* Approval Safeguard Card */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-brand-600" /> Administrative Approval Gate
              </span>
              <p className="text-xs text-slate-500 leading-relaxed">
                As required by billing compliance, appeals are never automatically dispatched to insurance payers without explicit administrator review and sign-off.
              </p>

              <div className="pt-2">
                <p className="text-xs text-slate-400">Current Status</p>
                <p className="text-sm font-bold text-slate-900 capitalize mt-0.5">{appeal.status.replace('_', ' ')}</p>
              </div>

              {appeal.approved_at && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>Approved on {formatDate(appeal.approved_at)}</span>
                </div>
              )}
            </div>

            {/* Provider Header Preview */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Hospital Provider Details
              </span>
              <div className="text-xs text-slate-600 space-y-1">
                <p className="font-bold text-slate-900">{appeal.provider_info?.facility_name || 'Memorial Regional Health System'}</p>
                <p>{appeal.provider_info?.department || 'Utilization Review'}</p>
                <p>NPI: {appeal.provider_info?.npi || '1942859102'}</p>
                <p>Phone: {appeal.provider_info?.phone || '(800) 555-4920'}</p>
              </div>
            </div>

            {/* Claim Reference Block */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Claim & Patient Reference
              </span>
              <div className="text-xs text-slate-600 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-400">Claim #:</span>
                  <span className="font-semibold text-slate-900">{claim?.claim_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Patient:</span>
                  <span className="font-semibold text-slate-900">
                    {claim?.patient ? `${claim.patient.first_name} ${claim.patient.last_name}` : 'Jane Doe'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Payer:</span>
                  <span className="font-semibold text-slate-900">{claim?.payer_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Denied:</span>
                  <span className="font-bold text-rose-600">{formatCurrency(claim?.denied_amount || 0)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

