import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, FileText, FolderOpen, Brain, ScrollText,
  BarChart3, Settings, LogOut, ShieldCheck, ChevronRight
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/claims', icon: FileText, label: 'Claims' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 bg-navy-900 text-white flex flex-col flex-shrink-0">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-brand-500 rounded-lg flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-[15px] font-bold tracking-tight leading-tight">ClaimResolve</h1>
              <p className="text-[10px] text-brand-300 font-medium tracking-widest uppercase">AI Platform</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-colors',
                isActive
                  ? 'bg-brand-600/20 text-brand-300'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              )}
            >
              <item.icon className="w-[18px] h-[18px]" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-3 py-4 border-t border-white/10">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate">{user?.full_name}</p>
              <p className="text-[10px] text-slate-400 truncate">{user?.organization_name}</p>
            </div>
            <button onClick={handleLogout} className="text-slate-400 hover:text-red-400 transition-colors">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}

