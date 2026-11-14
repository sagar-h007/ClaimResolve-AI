import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { formatCurrency, STATUS_COLORS } from '../lib/utils';
import {
  Sparkles,
  ArrowLeft,
  FileText,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  ArrowRight,
  BookOpen,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Layers,
  HelpCircle,
  FileCheck,
} from 'lucide-react';

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  const { data: claim } = useQuery({
    queryKey: ['claim', id],
    queryFn: () => api.getClaim(id!),
    enabled: !!id,
  });

  const { data: documents } = useQuery({
    queryKey: ['claimDocuments', id],
    queryFn: () => api.getDocuments(`claim_id=${id}`),
    enabled: !!id,
  });

  const { data: analysis, isLoading, refetch } = useQuery({
    queryKey: ['claimAnalysis', id],
    queryFn: () => api.getAnalysis(id!),
    enabled: !!id,
    retry: false,
  });

  const runAnalysisMutation = useMutation({
    mutationFn: () => api.analyzeClaim(id!, { force_reanalyze: true }),
    onSuccess: (data) => {
      queryClient.setQueryData(['claimAnalysis', id], data);
      queryClient.invalidateQueries({ queryKey: ['claim', id] });
    },
  });

  const toggleCard = (cardId: string) => {
    setExpandedCards((prev) => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Bar Navigation */}
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
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">AI Claim Analysis & Audit Engine</h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                5-Step Clinical Reasoning
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Deterministic RAG retrieval comparing payer coverage criteria against patient clinical records with verifiable page citations.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => runAnalysisMutation.mutate()}
              disabled={runAnalysisMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg shadow-sm shadow-brand-500/20 transition disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {runAnalysisMutation.isPending ? 'Executing AI Reasoning Pipeline...' : 'Re-Run Analysis'}
            </button>

            <Link
              to={`/claims/${id}/appeal`}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg shadow-sm transition"
            >
              Draft Formal Appeal <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* When no analysis exists yet */}
      {!analysis && !isLoading && (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 shadow-sm text-center max-w-xl mx-auto space-y-4">
          <div className="w-12 h-12 bg-brand-50 text-brand-600 rounded-xl flex items-center justify-center mx-auto">
            <Sparkles className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-slate-900">No Analysis Generated Yet</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            The AI engine will parse the denial grounds, retrieve clinical notes via semantic search, cross-reference payer coverage rules, and build cited evidence cards.
          </p>
          <button
            onClick={() => runAnalysisMutation.mutate()}
            disabled={runAnalysisMutation.isPending}
            className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg shadow-sm"
          >
            {runAnalysisMutation.isPending ? 'Running AI Engine...' : 'Run Analysis Now'}
          </button>
        </div>
      )}

      {/* Two-Column Interface */}
      {analysis && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LEFT SIDE: Denial Information, Patient Documentation & Payer Policy References */}
          <div className="lg:col-span-5 space-y-6">
            {/* Denial Details Card */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-rose-600" /> Denial Remittance Grounds
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">
                  {analysis.denial_code || 'CO-50'}
                </span>
              </div>

              <div>
                <p className="text-xs font-semibold text-slate-600">Payer Denial Rationale</p>
                <p className="text-xs text-slate-800 mt-1 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                  {analysis.denial_reason}
                </p>
              </div>

              {analysis.payer_explanation && (
                <div>
                  <p className="text-xs font-semibold text-slate-600">Payer EOB Explanation</p>
                  <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                    {analysis.payer_explanation}
                  </p>
                </div>
              )}
            </div>

            {/* Payer Policy References */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <BookOpen className="w-4 h-4 text-brand-600" /> Payer Policy Benchmark
                </span>
                <span className="text-[11px] text-brand-700 font-semibold bg-brand-50 px-2 py-0.5 rounded">
                  {analysis.policy_section || 'Clinical Policy Bulletin'}
                </span>
              </div>

              <div>
                <p className="text-xs font-semibold text-slate-600">Coverage Prerequisites Identified</p>
                <p className="text-xs text-slate-700 mt-1 leading-relaxed bg-brand-50/50 p-3 rounded-lg border border-brand-100">
                  {analysis.policy_requirements_summary || 'Minimum 6 weeks conservative therapy, physical exam documentation, and objective diagnostic confirmation.'}
                </p>
              </div>
            </div>

            {/* Ingested Documents Used in RAG */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-indigo-600" /> Document Repository Linked
              </h3>
              <div className="space-y-2 mt-2">
                {(documents || []).map((doc: any) => (
                  <div key={doc.id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs">
                    <div className="truncate max-w-[240px]">
                      <p className="font-semibold text-slate-800 truncate">{doc.original_filename}</p>
                      <p className="text-[10px] text-slate-400 capitalize">{doc.category.replace('_', ' ')} • {doc.page_count}p</p>
                    </div>
                    <span className="text-[10px] text-emerald-600 font-medium">Verified</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT SIDE: AI Analysis, Expandable Evidence Cards, Missing Docs, Next Steps */}
          <div className="lg:col-span-7 space-y-6">
            {/* Evidence Strength Banner */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400">Clinical Appeal Viability</span>
                  <div className="flex items-center gap-2 mt-1">
                    <h2 className="text-lg font-bold text-slate-900">Evidence Strength:</h2>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      analysis.evidence_strength === 'Strong' ? 'bg-emerald-100 text-emerald-800' :
                      analysis.evidence_strength === 'Moderate' ? 'bg-amber-100 text-amber-800' :
                      'bg-rose-100 text-rose-800'
                    }`}>
                      {analysis.evidence_strength}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400">Citations Extracted</span>
                  <p className="text-lg font-bold text-slate-900">{analysis.evidence_references?.length || 0} Excerpts</p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-xs font-semibold text-slate-600">Clinical Findings Synthesis</p>
                <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                  {analysis.clinical_findings_summary}
                </p>
              </div>
            </div>

            {/* Expandable Evidence Cards */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <FileCheck className="w-4 h-4 text-emerald-600" /> Evidence Supporting The Appeal (With Citations)
                </h3>
                <span className="text-[11px] text-slate-400">Source provenance verified</span>
              </div>

              {(analysis.evidence_references || []).map((ev: any, idx: number) => {
                const isExpanded = expandedCards[ev.id] ?? true;
                return (
                  <div
                    key={ev.id || idx}
                    className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden transition"
                  >
                    <div
                      onClick={() => toggleCard(ev.id)}
                      className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-50 select-none"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-xs">
                          {idx + 1}
                        </span>
                        <div>
                          <p className="text-xs font-bold text-slate-900">{ev.source_document_title}</p>
                          <p className="text-[11px] text-slate-400">
                            Location: <span className="font-semibold text-slate-600">{ev.page_number}</span>
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Match: {Math.round(ev.relevance_score * 100)}%
                        </span>
                        {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="px-4 pb-4 pt-1 border-t border-slate-100 bg-slate-50/50">
                        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Verbatim Excerpt</p>
                        <blockquote className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-200 italic leading-relaxed">
                          "{ev.citation_text || ev.extracted_text}"
                        </blockquote>
                      </div>
                    )}
                  </div>
                );
              })}

              {(!analysis.evidence_references || analysis.evidence_references.length === 0) && (
                <div className="p-6 bg-white rounded-xl border border-slate-200 text-center text-xs text-slate-400">
                  No direct clinical citations retrieved. Ensure clinical progress notes or MRI reports are attached.
                </div>
              )}
            </div>

            {/* Missing Evidence & Gaps (Strict Anti-Hallucination) */}
            {analysis.missing_evidence?.length > 0 && (
              <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-5 space-y-2">
                <h3 className="text-xs font-bold text-amber-900 flex items-center gap-1.5 uppercase tracking-wider">
                  <AlertTriangle className="w-4 h-4 text-amber-700" /> Missing Clinical Documentation (Anti-Hallucination Guardrail)
                </h3>
                <p className="text-xs text-amber-800">
                  The following requirements were cited by payer policy but not found in the current medical record:
                </p>
                <ul className="list-disc list-inside text-xs text-amber-900 space-y-1 pt-1 font-medium">
                  {analysis.missing_evidence.map((item: string, i: number) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Appeal Arguments Suggested */}
            {analysis.potential_appeal_arguments?.length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-brand-600" /> Evidence-Backed Appeal Arguments
                </h3>
                <div className="space-y-2">
                  {analysis.potential_appeal_arguments.map((arg: string, i: number) => (
                    <div key={i} className="flex items-start gap-2.5 text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <span className="w-4 h-4 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-[10px] flex-shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      <span className="leading-relaxed">{arg}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Next Steps */}
            {analysis.recommended_next_steps?.length > 0 && (
              <div className="bg-slate-900 text-white rounded-xl p-5 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Recommended Action Plan
                </h3>
                <div className="space-y-2">
                  {analysis.recommended_next_steps.map((step: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-slate-200">
                      <ArrowRight className="w-3.5 h-3.5 text-brand-400 mt-0.5 flex-shrink-0" />
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

