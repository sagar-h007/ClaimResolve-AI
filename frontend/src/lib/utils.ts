import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(n: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
}

export function formatDate(d: string | Date): string {
  return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

export function maskPolicy(pol: string): string {
  if (!pol) return '****';
  if (pol.includes('****')) return pol;
  return pol.slice(0, 3) + '****' + pol.slice(-4);
}

export const STATUS_COLORS: Record<string, string> = {
  Uploaded: 'bg-gray-100 text-gray-700',
  Processing: 'bg-blue-100 text-blue-700',
  'Analysis Complete': 'bg-indigo-100 text-indigo-700',
  'Appeal Drafted': 'bg-purple-100 text-purple-700',
  'Pending Review': 'bg-amber-100 text-amber-700',
  Submitted: 'bg-cyan-100 text-cyan-700',
  Approved: 'bg-emerald-100 text-emerald-700',
  Rejected: 'bg-red-100 text-red-700',
  draft: 'bg-gray-100 text-gray-700',
  pending_review: 'bg-amber-100 text-amber-700',
  approved: 'bg-emerald-100 text-emerald-700',
  submitted: 'bg-cyan-100 text-cyan-700',
  Strong: 'bg-emerald-100 text-emerald-700',
  Moderate: 'bg-amber-100 text-amber-700',
  Weak: 'bg-orange-100 text-orange-700',
  Insufficient: 'bg-red-100 text-red-700',
};

