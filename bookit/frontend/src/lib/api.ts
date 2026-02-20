// -----------------------------------------------------------------------
// BookIt API client
// -----------------------------------------------------------------------

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

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  created_at: string;
}

export interface Service {
  id: number;
  tenant_id: number;
  name: string;
  duration_minutes: number;
  capacity: number;
  created_at: string;
}

export interface ServiceCreate {
  name: string;
  duration_minutes: number;
  capacity: number;
}

export interface Slot {
  id: number;
  service_id: number;
  date: string;
  start_time: string;
  end_time: string;
  capacity: number;
  booked_count: number;
}

export interface SlotBulkCreate {
  date: string;
  start_hour: number;
  end_hour: number;
}

export interface Booking {
  id: number;
  slot_id: number;
  customer_name: string;
  customer_email: string;
  status: "confirmed" | "cancelled";
  created_at: string;
  // Joined fields from backend
  service_name?: string;
  slot_date?: string;
  slot_start_time?: string;
  slot_end_time?: string;
}

export interface BookingCreate {
  slot_id: number;
  customer_name: string;
  customer_email: string;
}

// -----------------------------------------------------------------------
// Tenant APIs
// -----------------------------------------------------------------------

export const getTenant = (slug: string) => request<Tenant>(`/tenants/${slug}`);

export const createTenant = (name: string) =>
  request<Tenant>("/tenants", {
    method: "POST",
    body: JSON.stringify({ name }),
  });

// -----------------------------------------------------------------------
// Service APIs
// -----------------------------------------------------------------------

export const getServices = (slug: string) =>
  request<Service[]>(`/tenants/${slug}/services`);

export const createService = (slug: string, data: ServiceCreate) =>
  request<Service>(`/tenants/${slug}/services`, {
    method: "POST",
    body: JSON.stringify(data),
  });

// -----------------------------------------------------------------------
// Slot APIs
// -----------------------------------------------------------------------

export const getSlots = (slug: string, serviceId: number, date: string) =>
  request<Slot[]>(`/tenants/${slug}/services/${serviceId}/slots?date=${date}`);

export const generateSlots = (
  slug: string,
  serviceId: number,
  data: SlotBulkCreate,
) =>
  request<Slot[]>(`/tenants/${slug}/services/${serviceId}/slots/generate`, {
    method: "POST",
    body: JSON.stringify(data),
  });

// -----------------------------------------------------------------------
// Booking APIs
// -----------------------------------------------------------------------

export const createBooking = (data: BookingCreate) =>
  request<Booking>("/bookings", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const cancelBooking = (id: number) =>
  request<Booking>(`/bookings/${id}`, { method: "DELETE" });

export const getMyBookings = (email: string) =>
  request<Booking[]>(`/bookings?email=${encodeURIComponent(email)}`);

// -----------------------------------------------------------------------
// Public booking APIs
// -----------------------------------------------------------------------

export interface PublicSlot {
  id: number;
  service_id: number;
  date: string;
  start_time: string;
  end_time: string;
  available: number;
}

export interface PublicTenantView {
  name: string;
  slug: string;
  services: Service[];
  slots_by_service: Record<number, PublicSlot[]>;
}

export const getPublicTenantView = (slug: string) =>
  request<PublicTenantView>(`/book/${slug}`);
