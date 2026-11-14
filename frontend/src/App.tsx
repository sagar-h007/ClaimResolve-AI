import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ClaimsPage from './pages/ClaimsPage';
import ClaimDetailPage from './pages/ClaimDetailPage';
import AnalysisPage from './pages/AnalysisPage';
import AppealEditorPage from './pages/AppealEditorPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SettingsPage from './pages/SettingsPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" /></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<DashboardPage />} />
        <Route path="claims" element={<ClaimsPage />} />
        <Route path="claims/:id" element={<ClaimDetailPage />} />
        <Route path="claims/:id/analysis" element={<AnalysisPage />} />
        <Route path="claims/:id/appeal" element={<AppealEditorPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

