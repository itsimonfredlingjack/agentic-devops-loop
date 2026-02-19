import { useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { usePipelineStore } from "./stores/pipelineStore";
import { connectWebSocket, disconnectWebSocket } from "./lib/ws";

function App() {
  const {
    status,
    transcription,
    log,
    serverUrl,
    clarification,
    setStatus,
    setTranscription,
    appendLog,
    setServerUrl,
    setClarification,
    clearClarification,
  } = usePipelineStore();

  const [clarifyInput, setClarifyInput] = useState("");
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
    );
    return () => disconnectWebSocket();
  }, [appendLog]);

  const handleToggle = async () => {
    if (status === "recording") {
      // Stop recording, send audio
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
      // Start recording
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

  const handleClarifySubmit = async () => {
    if (!clarification || !clarifyInput.trim()) return;

    appendLog(`[client] Sending clarification: ${clarifyInput}`);
    setStatus("processing");

    try {
      const resp = await fetch(`${serverUrl}/api/pipeline/clarify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: clarification.sessionId,
          text: clarifyInput,
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

      setClarifyInput("");
    } catch (err) {
      appendLog(`[client] Clarification error: ${err}`);
      setStatus("error");
    }
  };

  const buttonLabel =
    status === "recording"
      ? "Stop Recording"
      : status === "processing"
        ? "Processing..."
        : "Start Recording";

  return (
    <div>
      <h3>SEJFA Voice Pipeline</h3>

      <div>
        <label>
          Server URL:{" "}
          <input
            type="text"
            value={serverUrl}
            onChange={(e) => setServerUrl(e.target.value)}
            style={{ width: 300 }}
          />
        </label>
      </div>

      <div>
        <button
          onClick={handleToggle}
          disabled={status === "processing" || status === "clarifying"}
        >
          {buttonLabel}
        </button>
        <span> Status: {status}</span>
      </div>

      <div>
        <strong>Transcription:</strong>
        <pre>{transcription || "(none)"}</pre>
      </div>

      {clarification && (
        <div style={{ border: "1px solid #666", padding: 8, margin: "8px 0" }}>
          <strong>Clarification needed (round {clarification.round}):</strong>
          <p>Partial summary: {clarification.partialSummary}</p>
          <ul>
            {clarification.questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
          <input
            type="text"
            value={clarifyInput}
            onChange={(e) => setClarifyInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleClarifySubmit()}
            placeholder="Type your answer..."
            style={{ width: 400 }}
          />
          <button
            onClick={handleClarifySubmit}
            disabled={status === "processing"}
          >
            Send
          </button>
        </div>
      )}

      <div>
        <strong>Pipeline Log:</strong>
        <pre style={{ maxHeight: 300, overflow: "auto" }}>
          {log.join("\n") || "(no events)"}
        </pre>
      </div>
    </div>
  );
}

export default App;
