import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { formatCurrency } from '../lib/utils';
import {
  BarChart3,
  TrendingUp,
  Download,
  Calendar,
  DollarSign,
  PieChart as PieIcon,
  ShieldCheck,
  Clock,
  ArrowUpRight,
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

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('6m');

  const { data: overview, isLoading } = useQuery({
    queryKey: ['analyticsOverview'],
    queryFn: () => api.getAnalyticsOverview(),
  });

  const handleExportCSV = () => {
    if (!overview) return;
    const rows = [
      ['Category', 'Name', 'Count', 'Amount ($)', 'Percentage (%)'],
      ...(overview.denial_reasons_distribution || []).map((d: any) => [
        'Denial Reason',
        d.name,
        d.count,
        d.amount,
        d.percentage,
      ]),
      ...(overview.payer_distribution || []).map((p: any) => [
        'Payer',
        p.name,
        p.count,
        p.amount,
        p.percentage,
      ]),
    ];
    const csvContent =
      'data:text/csv;charset=utf-8,' + rows.map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'ClaimResolve_Denial_Analytics_Report.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const kpis = overview?.kpis || {
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Claims Denial Analytics & Revenue Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Aggregate clinical denial trends, payer dispute performance, and recovered revenue reporting.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 border border-slate-200 rounded-lg text-xs text-slate-600">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="outline-none bg-transparent font-medium cursor-pointer"
            >
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="6m">Last 6 Months</option>
              <option value="1y">Last 12 Months</option>
            </select>
          </div>

          <button
            onClick={handleExportCSV}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg shadow-sm transition"
          >
            <Download className="w-3.5 h-3.5 text-brand-600" />
            Export CSV Report
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-medium text-slate-500">Total Recovered Revenue</span>
          <p className="text-2xl font-bold text-slate-900 mt-2">{formatCurrency(kpis.recovered_revenue)}</p>
          <p className="text-xs text-emerald-600 font-medium mt-1">74.5% appeal recovery rate</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-medium text-slate-500">Gross Denied Volume</span>
          <p className="text-2xl font-bold text-slate-900 mt-2">{formatCurrency(kpis.total_denied_value)}</p>
          <p className="text-xs text-slate-400 mt-1">{kpis.total_denied_claims} rejected claims</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-medium text-slate-500">Appeals Generated</span>
          <p className="text-2xl font-bold text-slate-900 mt-2">{kpis.appeals_generated}</p>
          <p className="text-xs text-slate-400 mt-1">{kpis.appeals_pending_review} awaiting admin sign-off</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs font-medium text-slate-500">Avg Generation Time</span>
          <p className="text-2xl font-bold text-slate-900 mt-2">{kpis.average_processing_time_hours} Hours</p>
          <p className="text-xs text-slate-400 mt-1">Down from 14.5 hours manual</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payer Distribution Bar Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900">Payer Denial Volume & Dollars</h2>
          <p className="text-xs text-slate-500 mb-4">Total dollar value of claims denied by major payer</p>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overview?.payer_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  axisLine={false}
                  tickFormatter={(val) => `$${val / 1000}k`}
                />
                <Tooltip
                  formatter={(val: any) => [formatCurrency(Number(val)), 'Denied Amount']}
                  contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="amount" fill="#0c8ee9" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Appeal Outcomes Bar Chart */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900">Appeal Determination Outcomes</h2>
          <p className="text-xs text-slate-500 mb-4">Success distribution of AI-drafted reconsideration letters</p>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overview?.appeal_outcomes || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} width={130} />
                <Tooltip
                  formatter={(val: any) => [`${val} claims`, 'Count']}
                  contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Denial Code Breakdown Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h2 className="text-sm font-bold text-slate-900">CARC Denial Code Frequency & Resolution Rate</h2>
          <p className="text-xs text-slate-500">Breakdown of frequent denial reasons and financial exposure</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
              <tr>
                <th className="px-6 py-3">Denial Code & Grounds</th>
                <th className="px-6 py-3">Claims Count</th>
                <th className="px-6 py-3">Denied Exposure ($)</th>
                <th className="px-6 py-3">Share (%)</th>
                <th className="px-6 py-3 text-right">Target Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(overview?.denial_reasons_distribution || []).map((item: any, idx: number) => (
                <tr key={idx} className="hover:bg-slate-50 transition">
                  <td className="px-6 py-3.5 font-semibold text-slate-900">{item.name}</td>
                  <td className="px-6 py-3.5">{item.count} claims</td>
                  <td className="px-6 py-3.5 font-bold text-slate-900">{formatCurrency(item.amount)}</td>
                  <td className="px-6 py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-brand-500 h-full rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-slate-700">{item.percentage}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-3.5 text-right text-xs text-brand-600 font-semibold">
                    Automate Level 1 Appeal
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

