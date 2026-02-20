import { describe, it, expect, beforeEach } from "vitest";
import { usePipelineStore } from "../stores/pipelineStore";
import type { PipelineStatus } from "../stores/pipelineStore";

// Reset store between tests
function resetStore() {
  usePipelineStore.setState({
    status: "idle",
    transcription: "",
    log: [],
    clarification: null,
    loopEvents: [],
    toasts: [],
    processingStep: "",
    pendingSamples: null,
    ticketResult: null,
    wsConnected: false,
  });
}

describe("pipelineStore", () => {
  beforeEach(() => {
    resetStore();
    window.localStorage.clear();
  });

  describe("initial state", () => {
    it("should have idle status by default", () => {
      const state = usePipelineStore.getState();
      expect(state.status).toBe("idle");
    });

    it("should start with empty transcription", () => {
      const state = usePipelineStore.getState();
      expect(state.transcription).toBe("");
    });

    it("should start with empty log", () => {
      const state = usePipelineStore.getState();
      expect(state.log).toEqual([]);
    });

    it("should start with no toasts", () => {
      const state = usePipelineStore.getState();
      expect(state.toasts).toEqual([]);
    });

    it("should start with wsConnected false", () => {
      const state = usePipelineStore.getState();
      expect(state.wsConnected).toBe(false);
    });
  });

  describe("setStatus", () => {
    it("should update status to recording", () => {
      usePipelineStore.getState().setStatus("recording");
      expect(usePipelineStore.getState().status).toBe("recording");
    });

    it("should cycle through all valid statuses", () => {
      const statuses: PipelineStatus[] = [
        "idle",
        "recording",
        "processing",
        "clarifying",
        "previewing",
        "done",
        "error",
      ];
      for (const s of statuses) {
        usePipelineStore.getState().setStatus(s);
        expect(usePipelineStore.getState().status).toBe(s);
      }
    });
  });

  describe("setTranscription", () => {
    it("should update transcription text", () => {
      usePipelineStore.getState().setTranscription("Hello world");
      expect(usePipelineStore.getState().transcription).toBe("Hello world");
    });

    it("should handle empty string", () => {
      usePipelineStore.getState().setTranscription("Some text");
      usePipelineStore.getState().setTranscription("");
      expect(usePipelineStore.getState().transcription).toBe("");
    });
  });

  describe("appendLog", () => {
    it("should add timestamped entries to the log", () => {
      usePipelineStore.getState().appendLog("Test message");
      const log = usePipelineStore.getState().log;
      expect(log).toHaveLength(1);
      expect(log[0]).toContain("Test message");
      // Verify timestamp prefix pattern [HH:MM:SS]
      expect(log[0]).toMatch(/^\[.*\] Test message$/);
    });

    it("should accumulate multiple log entries", () => {
      usePipelineStore.getState().appendLog("First");
      usePipelineStore.getState().appendLog("Second");
      usePipelineStore.getState().appendLog("Third");
      expect(usePipelineStore.getState().log).toHaveLength(3);
    });
  });

  describe("setServerUrl", () => {
    it("should update server URL", () => {
      usePipelineStore.getState().setServerUrl("http://example.com:9000");
      expect(usePipelineStore.getState().serverUrl).toBe(
        "http://example.com:9000",
      );
    });

    it("should persist server URL to localStorage", () => {
      usePipelineStore.getState().setServerUrl("http://myserver:8000");
      expect(localStorage.getItem("sejfa-voice-server-url")).toBe(
        "http://myserver:8000",
      );
    });
  });

  describe("setClarification / clearClarification", () => {
    it("should set clarification state and switch status to clarifying", () => {
      usePipelineStore.getState().setClarification({
        sessionId: "sess-123",
        questions: ["What priority?", "Which component?"],
        partialSummary: "A bug in the login page",
        round: 1,
      });

      const state = usePipelineStore.getState();
      expect(state.status).toBe("clarifying");
      expect(state.clarification).not.toBeNull();
      expect(state.clarification!.sessionId).toBe("sess-123");
      expect(state.clarification!.questions).toHaveLength(2);
      expect(state.clarification!.round).toBe(1);
    });

    it("should clear clarification state", () => {
      usePipelineStore.getState().setClarification({
        sessionId: "sess-1",
        questions: ["Q1"],
        partialSummary: "Summary",
        round: 1,
      });
      usePipelineStore.getState().clearClarification();
      expect(usePipelineStore.getState().clarification).toBeNull();
    });
  });

  describe("addLoopEvent", () => {
    it("should add loop events to the array", () => {
      usePipelineStore.getState().addLoopEvent({
        type: "ticket_queued",
        issueKey: "DEV-42",
        summary: "Fix login bug",
        timestamp: "12:00:00",
      });

      const events = usePipelineStore.getState().loopEvents;
      expect(events).toHaveLength(1);
      expect(events[0].issueKey).toBe("DEV-42");
      expect(events[0].type).toBe("ticket_queued");
    });

    it("should accumulate multiple events", () => {
      usePipelineStore.getState().addLoopEvent({
        type: "ticket_queued",
        issueKey: "DEV-1",
        timestamp: "12:00:00",
      });
      usePipelineStore.getState().addLoopEvent({
        type: "loop_started",
        issueKey: "DEV-1",
        timestamp: "12:01:00",
      });
      usePipelineStore.getState().addLoopEvent({
        type: "loop_completed",
        issueKey: "DEV-1",
        success: true,
        timestamp: "12:05:00",
      });
      expect(usePipelineStore.getState().loopEvents).toHaveLength(3);
    });
  });

  describe("addToast / removeToast", () => {
    it("should add a toast with auto-generated id", () => {
      usePipelineStore.getState().addToast("success", "Operation complete");
      const toasts = usePipelineStore.getState().toasts;
      expect(toasts).toHaveLength(1);
      expect(toasts[0].type).toBe("success");
      expect(toasts[0].message).toBe("Operation complete");
      expect(toasts[0].id).toMatch(/^toast-/);
    });

    it("should add multiple toasts", () => {
      usePipelineStore.getState().addToast("success", "Done");
      usePipelineStore.getState().addToast("error", "Failed");
      usePipelineStore.getState().addToast("info", "Note");
      expect(usePipelineStore.getState().toasts).toHaveLength(3);
    });

    it("should remove a toast by id", () => {
      usePipelineStore.getState().addToast("info", "Test toast");
      const toastId = usePipelineStore.getState().toasts[0].id;
      usePipelineStore.getState().removeToast(toastId);
      expect(usePipelineStore.getState().toasts).toHaveLength(0);
    });

    it("should only remove the specified toast", () => {
      usePipelineStore.getState().addToast("success", "First");
      usePipelineStore.getState().addToast("error", "Second");
      const firstId = usePipelineStore.getState().toasts[0].id;
      usePipelineStore.getState().removeToast(firstId);
      const remaining = usePipelineStore.getState().toasts;
      expect(remaining).toHaveLength(1);
      expect(remaining[0].message).toBe("Second");
    });
  });

  describe("processing and samples", () => {
    it("should set processing step", () => {
      usePipelineStore.getState().setProcessingStep("Transcribing audio...");
      expect(usePipelineStore.getState().processingStep).toBe(
        "Transcribing audio...",
      );
    });

    it("should set pending samples", () => {
      const samples = [100, -200, 300, -400];
      usePipelineStore.getState().setPendingSamples(samples);
      expect(usePipelineStore.getState().pendingSamples).toEqual(samples);
    });

    it("should clear pending samples with null", () => {
      usePipelineStore.getState().setPendingSamples([1, 2, 3]);
      usePipelineStore.getState().setPendingSamples(null);
      expect(usePipelineStore.getState().pendingSamples).toBeNull();
    });
  });

  describe("ticket result", () => {
    it("should set ticket result", () => {
      const ticket = {
        key: "DEV-42",
        url: "https://jira.example.com/DEV-42",
        summary: "Fix the thing",
      };
      usePipelineStore.getState().setTicketResult(ticket);
      expect(usePipelineStore.getState().ticketResult).toEqual(ticket);
    });

    it("should clear ticket result with null", () => {
      usePipelineStore.getState().setTicketResult({
        key: "DEV-1",
        url: "https://jira.example.com/DEV-1",
        summary: "Test",
      });
      usePipelineStore.getState().setTicketResult(null);
      expect(usePipelineStore.getState().ticketResult).toBeNull();
    });
  });

  describe("wsConnected", () => {
    it("should set WebSocket connected state", () => {
      usePipelineStore.getState().setWsConnected(true);
      expect(usePipelineStore.getState().wsConnected).toBe(true);
      usePipelineStore.getState().setWsConnected(false);
      expect(usePipelineStore.getState().wsConnected).toBe(false);
    });
  });
});
