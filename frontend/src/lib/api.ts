let rawBase = import.meta.env.VITE_API_URL || '';
if (rawBase && !rawBase.startsWith('http://') && !rawBase.startsWith('https://')) {
  rawBase = `https://${rawBase}`;
}
const API_BASE = (rawBase ? rawBase.replace(/\/+$/, '') : '') + '/api/v1';

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) return null as T;
  return res.json();
}

export const api = {
  // Auth
  register: (data: any) => request<any>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data: any) => request<any>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request<any>('/auth/me'),

  // Claims
  getClaims: (params?: string) => request<any>(`/claims${params ? `?${params}` : ''}`),
  getClaim: (id: string) => request<any>(`/claims/${id}`),
  createClaim: (data: any) => request<any>('/claims', { method: 'POST', body: JSON.stringify(data) }),
  updateClaim: (id: string, data: any) => request<any>(`/claims/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Documents
  uploadDocument: (formData: FormData) => request<any>('/documents/upload', { method: 'POST', body: formData }),
  getDocuments: (params?: string) => request<any[]>(`/documents${params ? `?${params}` : ''}`),
  getDocument: (id: string) => request<any>(`/documents/${id}`),
  getDocumentStatus: (id: string) => request<any>(`/documents/${id}/status`),

  // Analysis
  analyzeClaim: (claimId: string, data?: any) => request<any>(`/claims/${claimId}/analyze`, { method: 'POST', body: JSON.stringify(data || {}) }),
  getAnalysis: (claimId: string) => request<any>(`/claims/${claimId}/analysis`),

  // Appeals
  generateAppeal: (claimId: string, data?: any) => request<any>(`/claims/${claimId}/appeal/generate`, { method: 'POST', body: JSON.stringify(data || {}) }),
  getAppeal: (claimId: string) => request<any>(`/claims/${claimId}/appeal`),
  updateAppeal: (appealId: string, data: any) => request<any>(`/appeals/${appealId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  exportAppealPDF: async (appealId: string) => {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE}/appeals/${appealId}/export`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('PDF export failed');
    return res.blob();
  },

  // Analytics
  getDashboardStats: () => request<any>('/analytics/dashboard'),
  getAnalyticsOverview: () => request<any>('/analytics/overview'),

  // Demo
  seedDemo: () => request<any>('/demo/seed', { method: 'POST' }),
};

