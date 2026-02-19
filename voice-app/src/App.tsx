import { useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { usePipelineStore } from "./stores/pipelineStore";
import { connectWebSocket, disconnectWebSocket } from "./lib/ws";
import type { LoopEvent } from "./lib/ws";

import { AppShell } from "./components/AppShell";
import { Header } from "./components/Header";
import { RecordButton } from "./components/RecordButton";
import { TranscriptionCard } from "./components/TranscriptionCard";
import { ClarificationDialog } from "./components/ClarificationDialog";
import { LoopEventsTimeline } from "./components/LoopEventsTimeline";
import { LogPanel } from "./components/LogPanel";
import { SettingsDrawer } from "./components/SettingsDrawer";

function App() {
  const {
    status,
    transcription,
    log,
    serverUrl,
    clarification,
    loopEvents,
    setStatus,
    setTranscription,
    appendLog,
    setServerUrl,
    clearClarification,
    setClarification,
  } = usePipelineStore();

  const [settingsOpen, setSettingsOpen] = useState(false);
  const serverUrlRef = useRef(serverUrl);
  serverUrlRef.current = serverUrl;

  useEffect(() => {
    connectWebSocket(
      () => serverUrlRef.current,
      appendLog,
      (s) => {
        usePipelineStore.getState().setStatus(s);
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

  const handleToggle = async () => {
    if (status === "recording") {
      try {
        setStatus("processing");
        appendLog("[client] Stopping mic...");
        const samples: number[] = await invoke("stop_mic");
        appendLog(`[client] Captured ${samples.length} samples, sending...`);

        const result: { text: string; job_id: string } = await invoke(
          "send_audio",
          {
            samples,
            serverUrl,
          },
        );

        setTranscription(result.text);
        appendLog(`[client] Transcription received (job: ${result.job_id})`);
        setStatus("done");
      } catch (err) {
        appendLog(`[client] Error: ${err}`);
        setStatus("error");
      }
    } else {
      try {
        appendLog("[client] Starting mic...");
        await invoke("start_mic");
        setStatus("recording");
        appendLog("[client] Recording...");
      } catch (err) {
        appendLog(`[client] Error: ${err}`);
        setStatus("error");
      }
    }
  };

  const handleClarifySubmit = async (answer: string) => {
    if (!clarification) return;

    appendLog(`[client] Sending clarification: ${answer}`);
    setStatus("processing");

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
        appendLog(
          `[client] Ticket created: ${data.ticket_key} — ${data.ticket_url}`,
        );
        setStatus("done");
      }
    } catch (err) {
      appendLog(`[client] Clarification error: ${err}`);
      setStatus("error");
    }
  };

  return (
    <AppShell>
      <Header status={status} onSettingsClick={() => setSettingsOpen(true)} />

      <TranscriptionCard text={transcription} />

      <RecordButton status={status} onClick={handleToggle} />

      {clarification && (
        <ClarificationDialog
          questions={clarification.questions}
          partialSummary={clarification.partialSummary}
          round={clarification.round}
          disabled={status === "processing"}
          onSubmit={handleClarifySubmit}
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
    </AppShell>
  );
}

export default App;
