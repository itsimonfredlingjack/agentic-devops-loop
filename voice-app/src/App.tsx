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
    setPendingSamples(null);
    setStatus("processing");
    setProcessingStep("Sending audio...");
    appendLog(`[client] Sending ${samples.length} samples...`);

    try {
      const result: { text: string; job_id: string } = await invoke(
        "send_audio",
        { samples, serverUrl },
      );

      setTranscription(result.text);
      appendLog(`[client] Transcription received (job: ${result.job_id})`);
      // Don't set "done" here — wait for WS pipeline completion
      // But set done as fallback if no WS update comes
      setStatus("done");
    } catch (err) {
      appendLog(`[client] Error: ${err}`);
      setStatus("error");
      addToast("error", `Failed to send audio: ${err}`);
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
  ]);

  const handleDiscardAudio = useCallback(() => {
    setPendingSamples(null);
    setStatus("idle");
    appendLog("[client] Recording discarded");
    addToast("info", "Recording discarded");
  }, [setPendingSamples, setStatus, appendLog, addToast]);

  const handleClarifySubmit = async (answer: string) => {
    if (!clarification) return;

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
            summary: data.ticket_summary || data.ticket_key,
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
      addToast("error", `Clarification failed: ${err}`);
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
