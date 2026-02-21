import { create } from "zustand";
import * as api from "../lib/api";
import type { EventRead, TierRead, TicketRead } from "../lib/api";

interface EventState {
  // Data
  currentTenant: string;
  events: EventRead[];
  selectedEvent: EventRead | null;
  tiers: TierRead[];
  attendees: TicketRead[];
  loading: boolean;
  error: string | null;

  // Actions
  setTenant: (slug: string) => void;
  fetchPublishedEvents: () => Promise<void>;
  fetchTenantEvents: () => Promise<void>;
  fetchEvent: (id: number) => Promise<void>;
  fetchTiers: (eventId: number) => Promise<void>;
  fetchAttendees: (eventId: number) => Promise<void>;
  purchaseTicket: (
    eventId: number,
    data: api.TicketPurchase,
  ) => Promise<TicketRead>;
  transitionEvent: (id: number, status: string) => Promise<void>;
  createEvent: (data: api.EventCreate) => Promise<EventRead>;
  createTier: (eventId: number, data: api.TierCreate) => Promise<void>;
  clearError: () => void;
}

export const useEventStore = create<EventState>((set, get) => ({
  currentTenant: "demo-events",
  events: [],
  selectedEvent: null,
  tiers: [],
  attendees: [],
  loading: false,
  error: null,

  setTenant: (slug) => set({ currentTenant: slug }),
  clearError: () => set({ error: null }),

  fetchPublishedEvents: async () => {
    set({ loading: true, error: null });
    try {
      const events = await api.listPublishedEvents();
      set({ events, loading: false });
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte ladda evenemang",
      });
    }
  },

  fetchTenantEvents: async () => {
    const { currentTenant } = get();
    set({ loading: true, error: null });
    try {
      const events = await api.listTenantEvents(currentTenant);
      set({ events, loading: false });
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte ladda evenemang",
      });
    }
  },

  fetchEvent: async (id) => {
    set({ loading: true, error: null });
    try {
      const selectedEvent = await api.getEvent(id);
      set({ selectedEvent, loading: false });
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Evenemang hittades inte",
      });
    }
  },

  fetchTiers: async (eventId) => {
    set({ loading: true, error: null });
    try {
      const tiers = await api.listTiers(eventId);
      set({ tiers, loading: false });
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte ladda biljetter",
      });
    }
  },

  fetchAttendees: async (eventId) => {
    set({ loading: true, error: null });
    try {
      const attendees = await api.listAttendees(eventId);
      set({ attendees, loading: false });
    } catch (e) {
      set({
        loading: false,
        error:
          e instanceof Error ? e.message : "Kunde inte ladda deltagarlista",
      });
    }
  },

  purchaseTicket: async (eventId, data) => {
    set({ loading: true, error: null });
    try {
      const ticket = await api.purchaseTicket(eventId, data);
      set({ loading: false });
      return ticket;
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte köpa biljett",
      });
      throw e;
    }
  },

  transitionEvent: async (id, status) => {
    set({ loading: true, error: null });
    try {
      const updated = await api.transitionEvent(id, status);
      set((s) => ({
        loading: false,
        selectedEvent: s.selectedEvent?.id === id ? updated : s.selectedEvent,
        events: s.events.map((e) => (e.id === id ? updated : e)),
      }));
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Statusändring misslyckades",
      });
    }
  },

  createEvent: async (data) => {
    const { currentTenant } = get();
    set({ loading: true, error: null });
    try {
      const event = await api.createEvent(currentTenant, data);
      set({ loading: false });
      await get().fetchTenantEvents();
      return event;
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte skapa evenemang",
      });
      throw e;
    }
  },

  createTier: async (eventId, data) => {
    set({ loading: true, error: null });
    try {
      await api.createTier(eventId, data);
      set({ loading: false });
      await get().fetchTiers(eventId);
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Kunde inte skapa biljettyp",
      });
      throw e;
    }
  },
}));
