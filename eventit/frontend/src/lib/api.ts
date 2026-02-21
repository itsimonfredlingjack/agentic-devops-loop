const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((error as { detail?: string }).detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Tenant {
  id: number;
  slug: string;
  name: string;
  created_at: string;
}

export interface TenantCreate {
  slug: string;
  name: string;
}

export type EventStatus = "draft" | "published" | "cancelled" | "completed";

export interface EventRead {
  id: number;
  tenant_id: number;
  title: string;
  slug: string;
  description: string | null;
  venue: string | null;
  start_time: string;
  end_time: string;
  status: EventStatus;
  capacity: number;
  created_at: string;
}

export interface EventCreate {
  title: string;
  slug: string;
  description?: string;
  venue?: string;
  start_time: string;
  end_time: string;
  capacity?: number;
}

export interface TierRead {
  id: number;
  event_id: number;
  name: string;
  price_cents: number;
  capacity: number;
  sold_count: number;
  created_at: string;
}

export interface TierCreate {
  name: string;
  price_cents: number;
  capacity: number;
}

export interface TicketRead {
  id: number;
  tier_id: number;
  attendee_name: string;
  attendee_email: string;
  qr_code: string;
  qr_image_b64: string | null;
  status: "confirmed" | "checked_in" | "cancelled";
  created_at: string;
}

export interface TicketPurchase {
  tier_id: number;
  attendee_name: string;
  attendee_email: string;
}

export interface CheckInResponse {
  status: string;
  ticket_id: number;
  attendee_name: string;
  attendee_email: string;
  tier_name: string;
  event_title: string;
  checked_in_at: string;
}

// ---------------------------------------------------------------------------
// Tenant APIs
// ---------------------------------------------------------------------------

export const createTenant = (data: TenantCreate) =>
  request<Tenant>("/tenants", { method: "POST", body: JSON.stringify(data) });

export const getTenant = (slug: string) => request<Tenant>(`/tenants/${slug}`);

// ---------------------------------------------------------------------------
// Event APIs
// ---------------------------------------------------------------------------

export const listPublishedEvents = () => request<EventRead[]>("/events/public");

export const getEvent = (id: number) => request<EventRead>(`/events/${id}`);

export const listTenantEvents = (slug: string) =>
  request<EventRead[]>(`/tenants/${slug}/events`);

export const createEvent = (slug: string, data: EventCreate) =>
  request<EventRead>(`/tenants/${slug}/events`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const transitionEvent = (id: number, status: string) =>
  request<EventRead>(`/events/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

// ---------------------------------------------------------------------------
// Tier APIs
// ---------------------------------------------------------------------------

export const listTiers = (eventId: number) =>
  request<TierRead[]>(`/events/${eventId}/tiers`);

export const createTier = (eventId: number, data: TierCreate) =>
  request<TierRead>(`/events/${eventId}/tiers`, {
    method: "POST",
    body: JSON.stringify(data),
  });

// ---------------------------------------------------------------------------
// Ticket APIs
// ---------------------------------------------------------------------------

export const purchaseTicket = (eventId: number, data: TicketPurchase) =>
  request<TicketRead>(`/events/${eventId}/tickets`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const listAttendees = (eventId: number) =>
  request<TicketRead[]>(`/events/${eventId}/attendees`);

// ---------------------------------------------------------------------------
// Check-in APIs
// ---------------------------------------------------------------------------

export const scanCheckIn = (qrCode: string) =>
  request<CheckInResponse>(`/checkin/${qrCode}`, { method: "POST" });

export const lookupTicket = (qrCode: string) =>
  request<TicketRead>(`/checkin/${qrCode}`);

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

export function formatSEK(cents: number): string {
  if (cents === 0) return "Gratis";
  const kr = cents / 100;
  return `${kr.toLocaleString("sv-SE")} kr`;
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("sv-SE", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("sv-SE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
