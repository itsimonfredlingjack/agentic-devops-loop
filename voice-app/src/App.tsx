import { useCallback, useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { usePipelineStore } from "./stores/pipelineStore";
import { connectWebSocket, disconnectWebSocket } from "./lib/ws";
import type { LoopEvent } from "./lib/ws";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { useMicLevel } from "./hooks/useMicLevel";

import { AppShell } from "./components/AppShell";
import { Header } from "./components/Header";
import { RecordButton } from "./components/RecordButton";
import { TranscriptionCard } from "./components/TranscriptionCard";
import { ClarificationDialog } from "./components/ClarificationDialog";
import { AudioPreview } from "./components/AudioPreview";
import { SuccessCard } from "./components/SuccessCard";
import { LoopEventsTimeline } from "./components/LoopEventsTimeline";
import { LogPanel } from "./components/LogPanel";
import { SettingsDrawer } from "./components/SettingsDrawer";
import { ToastContainer } from "./components/Toast";

function normalizeUrl(url: string): string {
  return url.trim().replace(/\/+$/, "");
}

function buildConnectionHelpMessage(serverUrl: string): string {
  const target = normalizeUrl(serverUrl) || "<empty>";
  return `Cannot reach backend at ${target}. Check Settings -> Server URL and ensure the backend is reachable from this Mac.`;
}

function formatRequestError(err: unknown, serverUrl: string): string {
  const raw = String(err);
  if (
    raw.includes("HTTP request failed") ||
    raw.includes("error sending request for url") ||
    raw.includes("Connection refused") ||
    raw.includes("timed out")
  ) {
    return buildConnectionHelpMessage(serverUrl);
  }
  return `Request failed: ${raw}`;
}

async function checkBackendHealth(serverUrl: string): Promise<{ ok: boolean; detail: string }> {
  const base = normalizeUrl(serverUrl);
  if (!base) {
    return { ok: false, detail: "Server URL is empty" };
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const resp = await fetch(`${base}/health`, {
      method: "GET",
      signal: controller.signal,
    });
    if (!resp.ok) {
      return { ok: false, detail: `Health check returned HTTP ${resp.status}` };
    }
    return { ok: true, detail: "ok" };
  } catch (err) {
    return { ok: false, detail: String(err) };
  } finally {
    clearTimeout(timeout);
  }
}

function App() {
  const {
    status,
    transcription,
    log,
    serverUrl,
    clarification,
    loopEvents,
    toasts,
    processingStep,
    pendingSamples,
    ticketResult,
    wsConnected,
    setStatus,
    setTranscription,
    appendLog,
    setServerUrl,
    clearClarification,
    setClarification,
    addToast,
    removeToast,
    setProcessingStep,
    setPendingSamples,
    setTicketResult,
  } = usePipelineStore();

  const [settingsOpen, setSettingsOpen] = useState(false);
  const serverUrlRef = useRef(serverUrl);
  const wasBackendReachableRef = useRef<boolean | null>(null);
  const lastHealthCheckUrlRef = useRef("");
  serverUrlRef.current = serverUrl;

  // Mic level visualization
  const micLevels = useMicLevel(status === "recording");

  useEffect(() => {
    connectWebSocket(
      () => serverUrlRef.current,
      appendLog,
      (s) => {
        const store = usePipelineStore.getState();
        store.setStatus(s);

        // Trigger toast on completion/error from WS
        if (s === "done") {
          store.addToast("success", "Pipeline completed successfully");
        } else if (s === "error") {
          store.addToast("error", "Pipeline encountered an error");
        }
      },
      (step) => {
        usePipelineStore.getState().setProcessingStep(step);
      },
      (connected) => {
        usePipelineStore.getState().setWsConnected(connected);
      },
      (data) => {
        usePipelineStore.getState().setClarification({
          sessionId: data.session_id,
          questions: data.questions,
          partialSummary: data.partial_summary,
          round: data.round,
        });
      },
      (event: LoopEvent) => {
        usePipelineStore.getState().addLoopEvent({
          type: event.type,
          issueKey: event.issue_key,
          summary: event.summary,
          success: event.success,
          timestamp: new Date().toLocaleTimeString(),
        });
      },
    );
    return () => disconnectWebSocket();
  }, [appendLog]);

  useEffect(() => {
    if (settingsOpen) return;
    const normalized = normalizeUrl(serverUrl);
    if (!normalized || normalized === lastHealthCheckUrlRef.current) return;

    const timer = setTimeout(async () => {
      const result = await checkBackendHealth(serverUrl);
      lastHealthCheckUrlRef.current = normalized;

      if (result.ok) {
        if (wasBackendReachableRef.current === false) {
          addToast("success", `Connected to backend: ${normalized}`);
        }
        wasBackendReachableRef.current = true;
        appendLog(`[client] Backend reachable: ${normalized}`);
      } else {
        if (wasBackendReachableRef.current !== false) {
          addToast("error", buildConnectionHelpMessage(serverUrl));
        }
        wasBackendReachableRef.current = false;
        appendLog(`[client] Backend health check failed: ${result.detail}`);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [serverUrl, settingsOpen, addToast, appendLog]);

  const ensureBackendAvailable = useCallback(
    async (operation: string): Promise<boolean> => {
      const result = await checkBackendHealth(serverUrl);
      if (result.ok) return true;

      const msg = buildConnectionHelpMessage(serverUrl);
      appendLog(`[client] Backend unavailable while ${operation}: ${result.detail}`);
      addToast("error", msg);
      return false;
    },
    [serverUrl, appendLog, addToast],
  );

  const handleToggle = useCallback(async () => {
    if (status === "recording") {
      try {
        appendLog("[client] Stopping mic...");
        const samples: number[] = await invoke("stop_mic");
        appendLog(`[client] Captured ${samples.length} samples`);

        // Show preview instead of sending immediately
        setPendingSamples(samples);
        setStatus("previewing");
      } catch (err) {
        appendLog(`[client] Error: ${err}`);
        setStatus("error");
        addToast("error", `Recording failed: ${err}`);
      }
    } else if (status === "idle" || status === "done" || status === "error") {
      try {
        // Reset state for new recording
        setTicketResult(null);
        setProcessingStep("");
        appendLog("[client] Starting mic...");
        await invoke("start_mic");
        setStatus("recording");
        appendLog("[client] Recording...");
      } catch (err) {
        appendLog(`[client] Error: ${err}`);
        setStatus("error");
        addToast("error", `Failed to start recording: ${err}`);
      }
    }
  }, [
    status,
    appendLog,
    setStatus,
    setPendingSamples,
    addToast,
    setTicketResult,
    setProcessingStep,
  ]);

  const handleSendAudio = useCallback(async () => {
    if (!pendingSamples) return;

    const samples = pendingSamples;
    setStatus("processing");
    setProcessingStep("Sending audio...");
    appendLog(`[client] Sending ${samples.length} samples...`);

    try {
      const backendOk = await ensureBackendAvailable("sending audio");
      if (!backendOk) {
        setStatus("previewing");
        setProcessingStep("");
        return;
      }

      setPendingSamples(null);

      const result = await invoke<Record<string, unknown>>(
        "send_audio",
        { samples, serverUrl },
      );

      const endpointUsed =
        typeof result._endpoint_used === "string"
          ? result._endpoint_used
          : "unknown";

      const transcribedText =
        typeof result.transcribed_text === "string"
          ? result.transcribed_text
          : typeof result.text === "string"
            ? result.text
            : "";
      if (transcribedText) {
        setTranscription(transcribedText);
      }

      if (result.status === "clarification_needed") {
        const sessionId =
          typeof result.session_id === "string" ? result.session_id : "";
        const questions = Array.isArray(result.questions)
          ? result.questions.filter((q): q is string => typeof q === "string")
          : [];
        const partialSummary =
          typeof result.partial_summary === "string"
            ? result.partial_summary
            : "";
        const round = typeof result.round === "number" ? result.round : 1;

        if (!sessionId || questions.length === 0) {
          appendLog(
            `[client] Invalid clarification payload (${endpointUsed}): ${JSON.stringify(result)}`,
          );
          setStatus("error");
          addToast("error", "Invalid clarification response from server");
          return;
        }

        setClarification({
          sessionId,
          questions,
          partialSummary,
          round,
        });
        appendLog(`[client] Clarification needed (${endpointUsed})`);
        return;
      }

      const ticketKey =
        typeof result.ticket_key === "string" ? result.ticket_key : "";
      const ticketUrl =
        typeof result.ticket_url === "string" ? result.ticket_url : "";
      const summary =
        typeof result.summary === "string" ? result.summary : ticketKey;

      if (ticketKey && ticketUrl) {
        clearClarification();
        setProcessingStep("");
        setTicketResult({
          key: ticketKey,
          url: ticketUrl,
          summary: summary || ticketKey,
        });
        appendLog(`[client] Ticket created: ${ticketKey} — ${ticketUrl}`);
        setStatus("done");
        addToast("success", `Ticket ${ticketKey} created`);
        return;
      }

      if (typeof result.text === "string") {
        appendLog(`[client] Transcription received (${endpointUsed})`);
        // Don't set "done" here in pipeline mode — wait for WS completion.
        // In fallback mode (/api/transcribe), this is our completion signal.
        setStatus("done");
        return;
      }

      appendLog(
        `[client] Unexpected response payload (${endpointUsed}): ${JSON.stringify(result)}`,
      );
      setStatus("error");
      addToast("error", "Unexpected server response");
    } catch (err) {
      appendLog(`[client] Error: ${err}`);
      setStatus("error");
      addToast("error", formatRequestError(err, serverUrl));
    }
  }, [
    pendingSamples,
    serverUrl,
    appendLog,
    setStatus,
    setTranscription,
    setPendingSamples,
    setProcessingStep,
    addToast,
    setClarification,
    clearClarification,
    setTicketResult,
    ensureBackendAvailable,
  ]);

  const handleDiscardAudio = useCallback(() => {
    setPendingSamples(null);
    setStatus("idle");
    appendLog("[client] Recording discarded");
    addToast("info", "Recording discarded");
  }, [setPendingSamples, setStatus, appendLog, addToast]);

  const handleClarifySubmit = async (answer: string) => {
    if (!clarification) return;

    const backendOk = await ensureBackendAvailable("sending clarification");
    if (!backendOk) {
      setStatus("clarifying");
      return;
    }

    appendLog(`[client] Sending clarification: ${answer}`);
    setStatus("processing");
    setProcessingStep("Sending clarification...");

    try {
      const resp = await fetch(`${serverUrl}/api/pipeline/clarify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: clarification.sessionId,
          text: answer,
        }),
      });

      const data = await resp.json();

      if (data.status === "clarification_needed") {
        setClarification({
          sessionId: data.session_id,
          questions: data.questions,
          partialSummary: data.partial_summary,
          round: data.round,
        });
        appendLog(`[client] More clarification needed (round ${data.round})`);
      } else {
        clearClarification();
        setProcessingStep("");

        // Store ticket result
        if (data.ticket_key && data.ticket_url) {
          setTicketResult({
            key: data.ticket_key,
            url: data.ticket_url,
            summary: data.summary || data.ticket_summary || data.ticket_key,
          });
        }

        appendLog(
          `[client] Ticket created: ${data.ticket_key} — ${data.ticket_url}`,
        );
        setStatus("done");
        addToast("success", `Ticket ${data.ticket_key} created`);
      }
    } catch (err) {
      appendLog(`[client] Clarification error: ${err}`);
      setStatus("error");
      addToast("error", formatRequestError(err, serverUrl));
    }
  };

  const handleClarifySkip = () => {
    clearClarification();
    setStatus("idle");
    appendLog("[client] Clarification skipped");
    addToast("info", "Clarification skipped");
  };

  const handleRecordAnother = () => {
    setTicketResult(null);
    setTranscription("");
    setStatus("idle");
  };

  // Keyboard shortcuts
  useKeyboardShortcuts({
    onToggleRecord: handleToggle,
    onEscape: () => {
      if (settingsOpen) {
        setSettingsOpen(false);
      } else if (clarification) {
        handleClarifySkip();
      }
    },
  });

  return (
    <AppShell>
      <Header
        status={status}
        wsConnected={wsConnected}
        onSettingsClick={() => setSettingsOpen(true)}
      />

      <TranscriptionCard text={transcription} />

      <RecordButton
        status={status}
        processingStep={processingStep}
        micLevels={micLevels}
        onClick={handleToggle}
      />

      {/* Audio preview (Fas 3) */}
      {status === "previewing" && pendingSamples && (
        <AudioPreview
          samples={pendingSamples}
          onSend={handleSendAudio}
          onDiscard={handleDiscardAudio}
        />
      )}

      {/* Clarification dialog */}
      {clarification && (
        <ClarificationDialog
          questions={clarification.questions}
          partialSummary={clarification.partialSummary}
          round={clarification.round}
          disabled={status === "processing"}
          onSubmit={handleClarifySubmit}
          onSkip={handleClarifySkip}
        />
      )}

      {/* Success card (Fas 4) */}
      {status === "done" && ticketResult && (
        <SuccessCard
          ticket={ticketResult}
          onRecordAnother={handleRecordAnother}
        />
      )}

      <LoopEventsTimeline events={loopEvents} />

      <LogPanel entries={log} />

      <SettingsDrawer
        open={settingsOpen}
        serverUrl={serverUrl}
        onServerUrlChange={setServerUrl}
        onClose={() => setSettingsOpen(false)}
      />

      {/* Toast overlay */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </AppShell>
  );
}

export default App;
