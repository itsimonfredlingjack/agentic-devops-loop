import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { scanCheckIn } from "../lib/api";
import type { CheckInResponse } from "../lib/api";
import { useEventStore } from "../stores/eventStore";

export function AdminCheckInPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const { selectedEvent, fetchEvent } = useEventStore();
  const [qrInput, setQrInput] = useState("");
  const [result, setResult] = useState<CheckInResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [recentCheckins, setRecentCheckins] = useState<CheckInResponse[]>([]);

  useEffect(() => {
    const id = Number(eventId);
    if (id) fetchEvent(id);
  }, [eventId, fetchEvent]);

  const handleScan = async (qrCode: string) => {
    if (!qrCode.trim()) return;
    setScanning(true);
    setResult(null);
    setError(null);

    try {
      const res = await scanCheckIn(qrCode.trim());
      setResult(res);
      setRecentCheckins((prev) => [res, ...prev].slice(0, 10));
      setQrInput("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Check-in misslyckades");
    } finally {
      setScanning(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleScan(qrInput);
  };

  return (
    <div>
      <h2
        style={{
          fontFamily: "var(--font-sans)",
          fontSize: 24,
          fontWeight: 300,
          marginBottom: 8,
        }}
      >
        Check-in
      </h2>
      {selectedEvent && (
        <p className="label" style={{ marginBottom: 32 }}>
          {selectedEvent.title}
        </p>
      )}

      {/* QR input */}
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          gap: 16,
          marginBottom: 32,
        }}
      >
        <input
          className="input-field"
          placeholder="Skriv eller klistra in QR-kod..."
          value={qrInput}
          onChange={(e) => setQrInput(e.target.value)}
          autoFocus
          style={{ flex: 1 }}
        />
        <button
          type="submit"
          className="btn-primary"
          disabled={scanning || !qrInput.trim()}
        >
          {scanning ? "Söker..." : "Checka in"}
        </button>
      </form>

      {/* Result */}
      {result && (
        <div
          style={{
            border: "2px solid var(--color-accent)",
            padding: 32,
            marginBottom: 32,
            textAlign: "center",
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              background: "var(--color-accent)",
              margin: "0 auto 16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 24,
              color: "var(--color-surface)",
            }}
          >
            &#10003;
          </div>
          <p
            style={{
              fontSize: 18,
              fontWeight: 500,
              marginBottom: 4,
            }}
          >
            {result.attendee_name}
          </p>
          <span className="label">
            {result.tier_name} — {result.attendee_email}
          </span>
        </div>
      )}

      {error && (
        <div
          style={{
            border: "2px solid var(--color-status-cancelled)",
            padding: 32,
            marginBottom: 32,
            textAlign: "center",
          }}
        >
          <p
            style={{
              color: "var(--color-status-cancelled)",
              fontFamily: "var(--font-mono)",
              fontSize: 13,
            }}
          >
            {error}
          </p>
        </div>
      )}

      {/* Recent check-ins */}
      {recentCheckins.length > 0 && (
        <div>
          <div className="label" style={{ marginBottom: 16 }}>
            Senaste inchecningar
          </div>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 1,
              background: "var(--color-surface-border)",
            }}
          >
            {recentCheckins.map((ci, i) => (
              <div
                key={`${ci.ticket_id}-${i}`}
                style={{
                  background: "var(--color-surface)",
                  padding: "12px 16px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span style={{ fontSize: 14 }}>{ci.attendee_name}</span>
                <span className="label">{ci.tier_name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
