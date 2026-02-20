import { create } from "zustand";

export type PipelineStatus =
  | "idle"
  | "recording"
  | "processing"
  | "clarifying"
  | "previewing"
  | "done"
  | "error";

export type ToastType = "success" | "error" | "info";

export interface ToastEntry {
  id: string;
  type: ToastType;
  message: string;
}

export interface TicketResult {
  key: string;
  url: string;
  summary: string;
}

interface ClarificationState {
  sessionId: string;
  questions: string[];
  partialSummary: string;
  round: number;
}

export interface LoopEventEntry {
  type: "ticket_queued" | "loop_started" | "loop_completed";
  issueKey: string;
  summary?: string;
  success?: boolean;
  timestamp: string;
}

interface PipelineState {
  status: PipelineStatus;
  transcription: string;
  log: string[];
  serverUrl: string;
  clarification: ClarificationState | null;
  loopEvents: LoopEventEntry[];

  // Fas 1: toasts + processing step
  toasts: ToastEntry[];
  processingStep: string;

  // Fas 3: audio preview
  pendingSamples: number[] | null;

  // Fas 4: ticket result + WS status
  ticketResult: TicketResult | null;
  wsConnected: boolean;

  setStatus: (status: PipelineStatus) => void;
  setTranscription: (text: string) => void;
  appendLog: (entry: string) => void;
  setServerUrl: (url: string) => void;
  setClarification: (c: ClarificationState | null) => void;
  clearClarification: () => void;
  addLoopEvent: (event: LoopEventEntry) => void;

  addToast: (type: ToastType, message: string) => void;
  removeToast: (id: string) => void;
  setProcessingStep: (step: string) => void;
  setPendingSamples: (samples: number[] | null) => void;
  setTicketResult: (result: TicketResult | null) => void;
  setWsConnected: (connected: boolean) => void;
}

const DEFAULT_SERVER_URL = "http://localhost:8000";

function loadServerUrl(): string {
  try {
    return localStorage.getItem("sejfa-voice-server-url") || DEFAULT_SERVER_URL;
  } catch {
    return DEFAULT_SERVER_URL;
  }
}

let toastId = 0;

export const usePipelineStore = create<PipelineState>((set) => ({
  status: "idle",
  transcription: "",
  log: [],
  serverUrl: loadServerUrl(),
  clarification: null,
  loopEvents: [],
  toasts: [],
  processingStep: "",
  pendingSamples: null,
  ticketResult: null,
  wsConnected: false,

  setStatus: (status) => set({ status }),

  setTranscription: (text) => set({ transcription: text }),

  appendLog: (entry) =>
    set((state) => ({
      log: [...state.log, `[${new Date().toLocaleTimeString()}] ${entry}`],
    })),

  setServerUrl: (url) => {
    try {
      localStorage.setItem("sejfa-voice-server-url", url);
    } catch {
      // localStorage unavailable
    }
    set({ serverUrl: url });
  },

  setClarification: (c) => set({ clarification: c, status: "clarifying" }),

  clearClarification: () => set({ clarification: null }),

  addLoopEvent: (event) =>
    set((state) => ({
      loopEvents: [...state.loopEvents, event],
    })),

  addToast: (type, message) => {
    const id = `toast-${++toastId}`;
    set((state) => ({
      toasts: [...state.toasts, { id, type, message }],
    }));
  },

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  setProcessingStep: (step) => set({ processingStep: step }),

  setPendingSamples: (samples) => set({ pendingSamples: samples }),

  setTicketResult: (result) => set({ ticketResult: result }),

  setWsConnected: (connected) => set({ wsConnected: connected }),
}));
