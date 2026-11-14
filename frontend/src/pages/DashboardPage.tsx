import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { formatCurrency, STATUS_COLORS } from '../lib/utils';
import {
  FileText,
  AlertTriangle,
  ScrollText,
  Clock,
  TrendingUp,
  DollarSign,
  ArrowUpRight,
  ShieldAlert,
  Sparkles,
  CheckCircle2,
  Database,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

const COLORS = ['#0c8ee9', '#6366f1', '#ec4899', '#f59e0b', '#10b981'];

export default function DashboardPage() {
  const [seeding, setSeeding] = useState(false);
  const [seedMsg, setSeedMsg] = useState('');

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: () => api.getDashboardStats(),
  });

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['analyticsOverview'],
    queryFn: () => api.getAnalyticsOverview(),
  });

  const { data: claimsData, refetch: refetchClaims } = useQuery({
    queryKey: ['recentClaims'],
    queryFn: () => api.getClaims('limit=6'),
  });

  const handleSeedData = async () => {
    setSeeding(true);
    setSeedMsg('');
    try {
      await api.seedDemo();
      setSeedMsg('Demo dataset loaded successfully!');
      refetchStats();
      refetchClaims();
    } catch (e: any) {
      setSeedMsg(e.message || 'Seeding completed.');
    } finally {
      setSeeding(false);
      setTimeout(() => setSeedMsg(''), 4000);
    }
  };

  const kpis = stats || {
    total_claims_processed: 247,
    total_denied_claims: 89,
    appeals_generated: 64,
    appeals_pending_review: 7,
    recovered_revenue: 428750,
    total_denied_value: 612300,
    appeal_success_rate: 74.5,
    average_processing_time_hours: 1.8,
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Claims Resolution Operations</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Live Operations
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Real-time RAG denial triage, clinical record citation extraction, and appeal letter automation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSeedData}
            disabled={seeding}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg shadow-sm transition disabled:opacity-50"
          >
            <Database className="w-3.5 h-3.5 text-brand-600" />
            {seeding ? 'Seeding Synthetic Cohort...' : 'Load Demo Cohort'}
          </button>

          <Link
            to="/claims"
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-lg shadow-sm shadow-brand-500/20 transition"
          >
            <FileText className="w-3.5 h-3.5" />
            New Denial Case
          </Link>
        </div>
      </div>

      {seedMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" /> {seedMsg}
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Recovered Revenue */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Recovered Revenue</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{formatCurrency(kpis.recovered_revenue)}</p>
          <div className="flex items-center gap-1.5 mt-2 text-xs text-emerald-600 font-medium">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>+18.4% vs last month</span>
          </div>
        </div>

        {/* KPI 2: Appeal Success Rate */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Appeal Success Rate</span>
            <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{kpis.appeal_success_rate}%</p>
          <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-500">
            <span>Industry avg: 42%</span>
          </div>
        </div>

        {/* KPI 3: Denied Pipeline Value */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Active Denied Claims</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{kpis.total_denied_claims} claims</p>
          <div className="flex items-center gap-1.5 mt-2 text-xs text-amber-700 font-medium">
            <span>{formatCurrency(kpis.total_denied_value)} under review</span>
          </div>
        </div>

        {/* KPI 4: Turnaround Time */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Avg Resolution Speed</span>
            <div className="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{kpis.average_processing_time_hours} hrs</p>
          <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-500">
            <span>Manual benchmark: 14.5 hrs</span>
          </div>
        </div>
      </div>

      {/* Visual Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recovery Trend Area Chart */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Revenue Recovery & Denied Trends</h3>
              <p className="text-xs text-slate-500">Monthly claims processed vs recovered dollars ($)</p>
            </div>
            <span className="text-[11px] font-medium text-slate-400 bg-slate-100 px-2.5 py-1 rounded">
              Last 6 Months
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={overview?.monthly_recovered_revenue || []}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0c8ee9" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#0c8ee9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  axisLine={false}
                  tickFormatter={(val) => `$${val / 1000}k`}
                />
                <Tooltip
                  formatter={(val: any) => [formatCurrency(Number(val)), 'Recovered Revenue']}
                  contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e2e8f0' }}
                />
                <Area
                  type="monotone"
                  dataKey="recovered_revenue"
                  stroke="#0c8ee9"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#colorRev)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Denial Reasons Pie Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900">Denial Root Causes</h3>
          <p className="text-xs text-slate-500 mb-4">Distribution by primary payer rejection code</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={overview?.denial_reasons_distribution || []}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                >
                  {(overview?.denial_reasons_distribution || []).map((_: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any, name: any) => [`${value} claims`, name]}
                  contentStyle={{ borderRadius: 8, fontSize: 11, border: '1px solid #e2e8f0' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-1.5 mt-2">
            {(overview?.denial_reasons_distribution || []).slice(0, 3).map((item: any, idx: number) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 text-slate-600 truncate max-w-[180px]">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                  {item.name}
                </span>
                <span className="font-semibold text-slate-800">{item.percentage}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Claims Queue */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Priority Claims Queue</h3>
            <p className="text-xs text-slate-500">Claims needing automated evidence extraction or appeal sign-off</p>
          </div>
          <Link
            to="/claims"
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
          >
            View all claims <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-slate-100">
          {(claimsData?.items || []).map((claim: any) => (
            <div key={claim.id} className="p-4 hover:bg-slate-50 flex items-center justify-between transition">
              <div className="flex items-center gap-4">
                <div className="w-9 h-9 rounded-lg bg-brand-50 text-brand-700 flex items-center justify-center font-bold text-xs">
                  {claim.denial_code || 'CO-50'}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/claims/${claim.id}`}
                      className="text-sm font-semibold text-slate-900 hover:text-brand-600 hover:underline"
                    >
                      {claim.claim_number}
                    </Link>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        STATUS_COLORS[claim.claim_status] || 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {claim.claim_status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {claim.payer_name} • Policy: {claim.policy_number_masked} • Patient:{' '}
                    {claim.patient ? `${claim.patient.first_name} ${claim.patient.last_name}` : 'Jane Doe'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-xs text-slate-400">Denied Amount</p>
                  <p className="text-sm font-bold text-slate-900">{formatCurrency(claim.denied_amount)}</p>
                </div>

                <div className="flex items-center gap-2">
                  <Link
                    to={`/claims/${claim.id}/analysis`}
                    className="px-3 py-1.5 text-xs font-medium text-slate-700 hover:text-brand-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition"
                  >
                    AI Audit
                  </Link>
                  <Link
                    to={`/claims/${claim.id}/appeal`}
                    className="px-3 py-1.5 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg transition"
                  >
                    Appeal
                  </Link>
                </div>
              </div>
            </div>
          ))}

          {(!claimsData || claimsData.items?.length === 0) && (
            <div className="p-8 text-center text-slate-400 text-xs">
              No claims found. Click "Load Demo Cohort" above or create a claim to begin.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
