import { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { EventCard } from "../components/EventCard";
import { listPublishedEvents, listTiers } from "../lib/api";
import type { EventRead, TierRead } from "../lib/api";

export function EventGridPage() {
  const [events, setEvents] = useState<EventRead[]>([]);
  const [tiersByEvent, setTiersByEvent] = useState<Record<number, TierRead[]>>(
    {},
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const evts = await listPublishedEvents();
        if (cancelled) return;
        setEvents(evts);

        // Fetch tiers for price ranges
        const tierResults = await Promise.all(
          evts.map((e) => listTiers(e.id).then((t) => [e.id, t] as const)),
        );
        if (cancelled) return;
        const map: Record<number, TierRead[]> = {};
        for (const [id, tiers] of tierResults) {
          map[id] = tiers;
        }
        setTiersByEvent(map);
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : "Kunde inte ladda evenemang",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const getPriceRange = (eventId: number) => {
    const tiers = tiersByEvent[eventId];
    if (!tiers || tiers.length === 0) return null;
    const prices = tiers.map((t) => t.price_cents);
    return { min: Math.min(...prices), max: Math.max(...prices) };
  };

  return (
    <div>
      <Header />

      {/* Hero */}
      <section
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "80px 24px 64px",
        }}
      >
        <h1
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: 48,
            fontWeight: 300,
            lineHeight: 1.1,
            marginBottom: 16,
          }}
        >
          Event<span style={{ color: "var(--color-accent)" }}>It</span>
        </h1>
        <p
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 13,
            color: "var(--color-text-secondary)",
            letterSpacing: "0.05em",
          }}
        >
          Curated experiences, seamless ticketing.
        </p>
      </section>

      {/* Grid */}
      {loading && (
        <p
          style={{
            textAlign: "center",
            padding: 64,
            color: "var(--color-text-muted)",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
          }}
        >
          Laddar evenemang...
        </p>
      )}

      {error && (
        <p
          style={{
            textAlign: "center",
            padding: 64,
            color: "var(--color-status-cancelled)",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
          }}
        >
          {error}
        </p>
      )}

      {!loading && !error && events.length === 0 && (
        <p
          style={{
            textAlign: "center",
            padding: 64,
            color: "var(--color-text-muted)",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
          }}
        >
          Inga publicerade evenemang just nu.
        </p>
      )}

      {!loading && !error && events.length > 0 && (
        <section className="event-grid">
          {events.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              priceRange={getPriceRange(event.id)}
            />
          ))}
        </section>
      )}

      {/* Footer */}
      <footer
        style={{
          borderTop: "1px solid var(--color-surface-border)",
          padding: "32px 24px",
          textAlign: "center",
          marginTop: 64,
        }}
      >
        <span className="label">
          EventIt 2026 — FastAPI + PostgreSQL + React
        </span>
      </footer>
    </div>
  );
}
