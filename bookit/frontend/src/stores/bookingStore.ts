import { create } from "zustand";
import * as api from "../lib/api";
import type { Service, Slot, Booking } from "../lib/api";

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

interface BookingState {
  // Data
  currentTenant: string;
  selectedService: number | null;
  selectedDate: string; // YYYY-MM-DD
  userEmail: string;
  services: Service[];
  slots: Slot[];
  myBookings: Booking[];
  loading: boolean;
  error: string | null;

  // Actions
  setTenant: (slug: string) => void;
  setSelectedService: (id: number | null) => void;
  setSelectedDate: (date: string) => void;
  setUserEmail: (email: string) => void;
  fetchServices: () => Promise<void>;
  fetchSlots: (serviceId: number) => Promise<void>;
  fetchMyBookings: () => Promise<void>;
  bookSlot: (
    slotId: number,
    name: string,
    email: string,
    phone?: string,
  ) => Promise<void>;
  cancelBooking: (id: number) => Promise<void>;
  createService: (data: api.ServiceCreate) => Promise<void>;
  generateSlots: (
    serviceId: number,
    data: api.SlotBulkCreate,
  ) => Promise<api.Slot[]>;
  clearError: () => void;
}

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// -----------------------------------------------------------------------
// Store
// -----------------------------------------------------------------------

export const useBookingStore = create<BookingState>((set, get) => ({
  currentTenant: "demo",
  selectedService: null,
  selectedDate: todayISO(),
  userEmail: "",
  services: [],
  slots: [],
  myBookings: [],
  loading: false,
  error: null,

  setTenant: (slug) => set({ currentTenant: slug }),
  setSelectedService: (id) => set({ selectedService: id }),
  setSelectedDate: (date) => set({ selectedDate: date }),
  setUserEmail: (email) => set({ userEmail: email }),
  clearError: () => set({ error: null }),

  fetchServices: async () => {
    const { currentTenant } = get();
    set({ loading: true, error: null });
    try {
      const services = await api.getServices(currentTenant);
      set({ services, loading: false });
      // Auto-select first service if none selected
      if (get().selectedService === null && services.length > 0) {
        const first = services[0];
        if (first) {
          set({ selectedService: first.id });
        }
      }
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte ladda tjänster",
      });
    }
  },

  fetchSlots: async (serviceId) => {
    const { currentTenant, selectedDate } = get();
    set({ loading: true, error: null });
    try {
      const slots = await api.getSlots(currentTenant, serviceId, selectedDate);
      set({ slots, loading: false });
    } catch (e) {
      set({
        loading: false,
        slots: [],
        error: e instanceof Error ? e.message : "Kunde inte ladda tider",
      });
    }
  },

  fetchMyBookings: async () => {
    const { userEmail } = get();
    if (!userEmail) return;
    set({ loading: true, error: null });
    try {
      const myBookings = await api.getMyBookings(userEmail);
      set({ myBookings, loading: false });
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte ladda bokningar",
      });
    }
  },

  bookSlot: async (slotId, name, email, phone) => {
    set({ loading: true, error: null });
    try {
      await api.createBooking({
        slot_id: slotId,
        customer_name: name,
        customer_email: email,
        customer_phone: phone,
      });
      set({ loading: false, userEmail: email });
      // Refresh slots
      const { selectedService } = get();
      if (selectedService !== null) {
        await get().fetchSlots(selectedService);
      }
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte boka",
      });
      throw e;
    }
  },

  cancelBooking: async (id) => {
    set({ loading: true, error: null });
    try {
      await api.cancelBooking(id);
      set({ loading: false });
      await get().fetchMyBookings();
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte avboka",
      });
    }
  },

  createService: async (data) => {
    const { currentTenant } = get();
    set({ loading: true, error: null });
    try {
      await api.createService(currentTenant, data);
      set({ loading: false });
      await get().fetchServices();
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte skapa tjänst",
      });
      throw e;
    }
  },

  generateSlots: async (serviceId, data) => {
    const { currentTenant } = get();
    set({ loading: true, error: null });
    try {
      const slots = await api.generateSlots(currentTenant, serviceId, data);
      set({ loading: false });
      return slots;
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte generera tider",
      });
      throw e;
    }
  },
}));
