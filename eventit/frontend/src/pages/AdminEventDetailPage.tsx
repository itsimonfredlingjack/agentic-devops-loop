import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { useEventStore } from "../stores/eventStore";
import { formatDateTime, formatSEK } from "../lib/api";
import type { TierCreate } from "../lib/api";

export function AdminEventDetailPage() {
  const { slug, eventId } = useParams<{ slug: string; eventId: string }>();
  const {
    selectedEvent,
    tiers,
    loading,
    error,
    fetchEvent,
    fetchTiers,
    createTier,
    transitionEvent,
  } = useEventStore();
  const [showTierForm, setShowTierForm] = useState(false);

  useEffect(() => {
    const id = Number(eventId);
    if (id) {
      fetchEvent(id);
      fetchTiers(id);
    }
  }, [eventId, fetchEvent, fetchTiers]);

  const handleCreateTier = async (data: TierCreate) => {
    if (!selectedEvent) return;
    await createTier(selectedEvent.id, data);
    setShowTierForm(false);
  };

  if (!selectedEvent) {
    return (
      <p
        style={{
          color: "var(--color-text-muted)",
          fontFamily: "var(--font-mono)",
          fontSize: 12,
          padding: 48,
          textAlign: "center",
        }}
      >
        {loading ? "Laddar..." : "Evenemang hittades inte"}
      </p>
    );
  }

  const totalSold = tiers.reduce((s, t) => s + t.sold_count, 0);
  const totalRevenue = tiers.reduce(
    (s, t) => s + t.sold_count * t.price_cents,
    0,
  );

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 8,
          }}
        >
          <StatusBadge status={selectedEvent.status} />
        </div>
        <h2
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: 28,
            fontWeight: 300,
            marginBottom: 8,
          }}
        >
          {selectedEvent.title}
        </h2>
        <span className="label">
          {formatDateTime(selectedEvent.start_time)}
          {selectedEvent.venue ? ` — ${selectedEvent.venue}` : ""}
        </span>
      </div>

      {error && (
        <p
          style={{
            color: "var(--color-status-cancelled)",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            marginBottom: 16,
          }}
        >
          {error}
        </p>
      )}

      {/* Quick stats */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 1,
          background: "var(--color-surface-border)",
          marginBottom: 32,
        }}
      >
        <StatCard label="Sålda biljetter" value={totalSold.toString()} />
        <StatCard label="Intäkter" value={formatSEK(totalRevenue)} />
        <StatCard label="Kapacitet" value={selectedEvent.capacity.toString()} />
      </div>

      {/* Actions */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 32,
          flexWrap: "wrap",
        }}
      >
        {selectedEvent.status === "draft" && (
          <button
            className="btn-primary"
            onClick={() => transitionEvent(selectedEvent.id, "published")}
          >
            Publicera
          </button>
        )}
        {selectedEvent.status === "published" && (
          <>
            <button
              className="btn-ghost"
              onClick={() => transitionEvent(selectedEvent.id, "completed")}
            >
              Markera klar
            </button>
            <button
              className="btn-ghost"
              onClick={() => transitionEvent(selectedEvent.id, "cancelled")}
              style={{ color: "var(--color-status-cancelled)" }}
            >
              Avbryt
            </button>
          </>
        )}
        <Link
          to={`/admin/${slug}/events/${selectedEvent.id}/attendees`}
          className="btn-ghost"
          style={{ display: "inline-block" }}
        >
          Deltagarlista
        </Link>
        <Link
          to={`/admin/${slug}/events/${selectedEvent.id}/checkin`}
          className="btn-ghost"
          style={{ display: "inline-block" }}
        >
          Check-in
        </Link>
      </div>

      {/* Tiers */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <div className="label">Biljetttyper</div>
        <button
          className="btn-ghost"
          onClick={() => setShowTierForm(!showTierForm)}
        >
          {showTierForm ? "Avbryt" : "Ny biljettyp"}
        </button>
      </div>

      {showTierForm && (
        <CreateTierForm loading={loading} onSubmit={handleCreateTier} />
      )}

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 1,
          background: "var(--color-surface-border)",
        }}
      >
        {tiers.map((tier) => {
          const pct = Math.round((tier.sold_count / tier.capacity) * 100);
          return (
            <div
              key={tier.id}
              style={{
                background: "var(--color-surface)",
                padding: 20,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: 15,
                    fontWeight: 500,
                    marginRight: 12,
                  }}
                >
                  {tier.name}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 14,
                    color: "var(--color-accent)",
                  }}
                >
                  {formatSEK(tier.price_cents)}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <div
                  style={{
                    width: 100,
                    height: 4,
                    background: "var(--color-surface-border)",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${pct}%`,
                      background:
                        pct >= 100
                          ? "var(--color-status-cancelled)"
                          : "var(--color-accent)",
                    }}
                  />
                </div>
                <span className="label">
                  {tier.sold_count}/{tier.capacity}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {tiers.length === 0 && (
        <p
          style={{
            textAlign: "center",
            padding: 32,
            color: "var(--color-text-muted)",
            fontSize: 13,
            border: "1px solid var(--color-surface-border)",
          }}
        >
          Inga biljetttyper. Klicka "Ny biljettyp" för att lägga till.
        </p>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        background: "var(--color-surface)",
        padding: 24,
        textAlign: "center",
      }}
    >
      <div className="label" style={{ marginBottom: 8 }}>
        {label}
      </div>
      <span
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 24,
          color: "var(--color-text-primary)",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function CreateTierForm({
  loading,
  onSubmit,
}: {
  loading: boolean;
  onSubmit: (data: TierCreate) => void;
}) {
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [capacity, setCapacity] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !capacity) return;
    onSubmit({
      name: name.trim(),
      price_cents: Math.round(parseFloat(price || "0") * 100),
      capacity: parseInt(capacity),
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        border: "1px solid var(--color-surface-border)",
        padding: 24,
        marginBottom: 16,
        display: "flex",
        gap: 16,
        alignItems: "end",
      }}
    >
      <div style={{ flex: 2 }}>
        <div className="label" style={{ marginBottom: 4 }}>
          Namn
        </div>
        <input
          className="input-field"
          placeholder="t.ex. VIP"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>
      <div style={{ flex: 1 }}>
        <div className="label" style={{ marginBottom: 4 }}>
          Pris (kr)
        </div>
        <input
          className="input-field"
          type="number"
          step="0.01"
          placeholder="0"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />
      </div>
      <div style={{ flex: 1 }}>
        <div className="label" style={{ marginBottom: 4 }}>
          Kapacitet
        </div>
        <input
          className="input-field"
          type="number"
          placeholder="100"
          value={capacity}
          onChange={(e) => setCapacity(e.target.value)}
          required
        />
      </div>
      <button type="submit" className="btn-primary" disabled={loading}>
        Lägg till
      </button>
    </form>
  );
}
