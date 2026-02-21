const BASE = "";

export interface Tenant {
  id: number;
  slug: string;
  name: string;
  created_at: string;
}

export interface Project {
  id: number;
  tenant_id: number;
  name: string;
  hourly_rate_cents: number;
  created_at: string;
}

export interface TimeEntry {
  id: number;
  project_id: number;
  date: string;
  duration_minutes: number;
  is_billable: boolean;
  is_invoiced: boolean;
  created_at: string;
}

export interface InvoiceLineItem {
  project_id: number;
  project_name: string;
  total_minutes: number;
  hours: number;
  hourly_rate_cents: number;
  amount_cents: number;
}

export interface InvoiceData {
  invoice_number: string;
  tenant_slug: string;
  year: number;
  month: number;
  line_items: InvoiceLineItem[];
  subtotal_cents: number;
  tax_amount_cents: number;
  total_cents: number;
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `ERR ${res.status}`);
  }
  return res.json();
}

export const getTenant = (slug: string) => api<Tenant>(`/api/tenants/${slug}`);
export const createTenant = (slug: string, name: string) =>
  api<Tenant>("/api/tenants", {
    method: "POST",
    body: JSON.stringify({ slug, name }),
  });

export const listProjects = (slug: string) =>
  api<Project[]>(`/api/tenants/${slug}/projects`);
export const createProject = (
  slug: string,
  name: string,
  hourlyRateCents: number,
) =>
  api<Project>(`/api/tenants/${slug}/projects`, {
    method: "POST",
    body: JSON.stringify({ name, hourly_rate_cents: hourlyRateCents }),
  });

export const logTime = (
  slug: string,
  projectId: number,
  date: string,
  durationMinutes: number,
  isBillable: boolean,
) =>
  api<TimeEntry>(`/api/tenants/${slug}/projects/${projectId}/time`, {
    method: "POST",
    body: JSON.stringify({
      date,
      duration_minutes: durationMinutes,
      is_billable: isBillable,
    }),
  });

export const getInvoice = (slug: string, year: number, month: number) =>
  api<InvoiceData>(`/api/tenants/${slug}/invoice?year=${year}&month=${month}`);
export const finalizeInvoice = (slug: string, year: number, month: number) =>
  api<{ status: string; entries_locked: number }>(
    `/api/tenants/${slug}/invoice/finalize?year=${year}&month=${month}`,
    { method: "POST" },
  );

export function formatSEK(cents: number): string {
  const kr = Math.floor(cents / 100);
  return kr.toLocaleString("sv-SE") + " kr";
}

export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export function formatRate(cents: number): string {
  return `${Math.floor(cents / 100).toLocaleString("sv-SE")}/h`;
}

export function timestamp(): string {
  return new Date().toLocaleTimeString("sv-SE", { hour12: false });
}
