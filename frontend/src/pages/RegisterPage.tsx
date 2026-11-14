import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, AlertCircle } from 'lucide-react';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '', full_name: '', organization_name: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const update = (key: string, val: string) => setForm(prev => ({ ...prev, [key]: val }));

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-brand-500/20">
            <ShieldCheck className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Create Account</h1>
          <p className="text-sm text-slate-500 mt-1">Start managing claim denials with AI</p>
        </div>
        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/60 p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Full Name</label>
              <input type="text" required value={form.full_name} onChange={e => update('full_name', e.target.value)}
                className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none" placeholder="Dr. Sarah Mitchell" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Organization Name</label>
              <input type="text" required value={form.organization_name} onChange={e => update('organization_name', e.target.value)}
                className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none" placeholder="Memorial Regional Hospital" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
              <input type="email" required value={form.email} onChange={e => update('email', e.target.value)}
                className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none" placeholder="admin@hospital.org" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
              <input type="password" required minLength={6} value={form.password} onChange={e => update('password', e.target.value)}
                className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none" placeholder="Min 6 characters" />
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-semibold transition disabled:opacity-50">
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
          <p className="text-sm text-slate-500 text-center mt-6">
            Already have an account? <Link to="/login" className="text-brand-600 font-medium hover:underline">Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

