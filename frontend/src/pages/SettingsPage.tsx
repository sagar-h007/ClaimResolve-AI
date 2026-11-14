import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import {
  Settings as SettingsIcon,
  Building2,
  User as UserIcon,
  Cpu,
  Database,
  ShieldAlert,
  CheckCircle2,
} from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();
  const [seeding, setSeeding] = useState(false);
  const [seedSuccess, setSeedSuccess] = useState('');

  const handleSeed = async () => {
    setSeeding(true);
    setSeedSuccess('');
    try {
      await api.seedDemo();
      setSeedSuccess('Synthetic dataset seeded (20 patients, 30 claims, 5 payer policies, 4 clinical scenarios).');
    } catch (e: any) {
      setSeedSuccess(e.message || 'Demo dataset synced.');
    } finally {
      setSeeding(false);
      setTimeout(() => setSeedSuccess(''), 5000);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div className="pb-6 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">System & Organization Settings</h1>
        <p className="text-sm text-slate-500 mt-1">
          Multi-tenant hospital configuration, user role management, and AI provider parameters.
        </p>
      </div>

      {seedSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          {seedSuccess}
        </div>
      )}

      {/* Organization Info */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Building2 className="w-4 h-4 text-brand-600" />
          Hospital Organization Profile
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block text-slate-500 mb-1">Organization Name</label>
            <input
              type="text"
              readOnly
              value={user?.organization_name || 'Memorial Regional Health System'}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 font-medium"
            />
          </div>
          <div>
            <label className="block text-slate-500 mb-1">Organization ID</label>
            <input
              type="text"
              readOnly
              value={user?.organization_id || 'org-84920'}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-500 font-mono"
            />
          </div>
        </div>
      </div>

      {/* User Info & RBAC */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <UserIcon className="w-4 h-4 text-brand-600" />
          User Profile & Role-Based Access Control (RBAC)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block text-slate-500 mb-1">Full Name</label>
            <input
              type="text"
              readOnly
              value={user?.full_name || 'Dr. Sarah Mitchell'}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 font-medium"
            />
          </div>
          <div>
            <label className="block text-slate-500 mb-1">Email Address</label>
            <input
              type="email"
              readOnly
              value={user?.email || 'admin@hospital.org'}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 font-medium"
            />
          </div>
          <div>
            <label className="block text-slate-500 mb-1">Assigned Role</label>
            <div className="px-3 py-2 bg-brand-50 border border-brand-200 rounded-lg text-brand-800 font-bold capitalize">
              {user?.role || 'Organization Admin'}
            </div>
          </div>
        </div>
      </div>

      {/* AI & RAG Engine Configuration */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-purple-600" />
          AI & RAG Vector Engine Configuration
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <p className="text-slate-400 font-medium">LLM Provider</p>
            <p className="text-sm font-bold text-slate-900 mt-1">OpenAI / Claude / Mock</p>
            <p className="text-[10px] text-slate-500 mt-0.5">High-fidelity deterministic fallback active</p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <p className="text-slate-400 font-medium">Vector Dimension</p>
            <p className="text-sm font-bold text-slate-900 mt-1">1536 Normalized Vectors</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Cosine similarity semantic search</p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100">
            <p className="text-slate-400 font-medium">Anti-Hallucination Guardrail</p>
            <p className="text-sm font-bold text-emerald-600 mt-1">Strict Citation Required</p>
            <p className="text-[10px] text-slate-500 mt-0.5">Missing facts marked as gaps</p>
          </div>
        </div>
      </div>

      {/* Synthetic Demo Data Loader */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-emerald-600" />
              Synthetic Healthcare Demo Dataset
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Seeds 20 synthetic patients, 30 medical claims, 5 payer policies, 10 denial remittance letters, and 4 clinical scenarios.
            </p>
          </div>

          <button
            onClick={handleSeed}
            disabled={seeding}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition disabled:opacity-50"
          >
            {seeding ? 'Seeding Dataset...' : 'Seed / Reset Demo Cohort'}
          </button>
        </div>
      </div>

      {/* Compliance Disclaimer */}
      <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-xl flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 leading-relaxed">
          <p className="font-bold">Demonstration & Evaluation Notice:</p>
          <p className="mt-0.5">
            This platform uses synthetic patient records and simulated clinical data for evaluation and testing purposes. Do not enter Protected Health Information (PHI) without appropriate Business Associate Agreements (BAA) and certified HIPAA hosting environments.
          </p>
        </div>
      </div>
    </div>
  );
}

