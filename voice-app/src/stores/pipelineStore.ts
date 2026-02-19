import { create } from "zustand";

export type PipelineStatus =
  | "idle"
  | "recording"
  | "processing"
  | "clarifying"
  | "done"
  | "error";

interface ClarificationState {
  sessionId: string;
  questions: string[];
  partialSummary: string;
  round: number;
}

interface PipelineState {
  status: PipelineStatus;
  transcription: string;
  log: string[];
  serverUrl: string;
  clarification: ClarificationState | null;
  setStatus: (status: PipelineStatus) => void;
  setTranscription: (text: string) => void;
  appendLog: (entry: string) => void;
  setServerUrl: (url: string) => void;
  setClarification: (c: ClarificationState | null) => void;
  clearClarification: () => void;
}

const DEFAULT_SERVER_URL = "http://localhost:8000";

function loadServerUrl(): string {
  try {
    return localStorage.getItem("sejfa-voice-server-url") || DEFAULT_SERVER_URL;
  } catch {
    return DEFAULT_SERVER_URL;
  }
}

export const usePipelineStore = create<PipelineState>((set) => ({
  status: "idle",
  transcription: "",
  log: [],
  serverUrl: loadServerUrl(),
  clarification: null,

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
}));
