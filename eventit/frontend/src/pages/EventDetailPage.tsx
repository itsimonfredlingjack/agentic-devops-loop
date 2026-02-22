import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { TierCard } from "../components/TierCard";
import { PurchaseForm } from "../components/PurchaseForm";
import { StatusBadge } from "../components/StatusBadge";
import { useEventStore } from "../stores/eventStore";
import { formatDateTime } from "../lib/api";

export function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const [selectedTierId, setSelectedTierId] = useState<number | null>(null);

  const {
    selectedEvent,
    tiers,
    loading,
    error,
    fetchEvent,
    fetchTiers,
    purchaseTicket,
  } = useEventStore();

  useEffect(() => {
    const id = Number(eventId);
    if (id) {
      fetchEvent(id);
      fetchTiers(id);
    }
  }, [eventId, fetchEvent, fetchTiers]);

  const selectedTier = tiers.find((t) => t.id === selectedTierId) ?? null;

  const handlePurchase = async (name: string, email: string) => {
    if (!selectedTier || !selectedEvent) return;
    try {
      const ticket = await purchaseTicket(selectedEvent.id, {
        tier_id: selectedTier.id,
        attendee_name: name,
        attendee_email: email,
      });
      navigate(`/events/${selectedEvent.id}/success`, {
        state: { ticket },
      });
    } catch {
      // Error is set in store
    }
  };

  if (loading && !selectedEvent) {
    return (
      <div>
        <Header />
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
      </div>
    );
  }

  if (error || !selectedEvent) {
    return (
      <div>
        <Header />
        <p
          style={{
            textAlign: "center",
            padding: 64,
            color: "var(--color-status-cancelled)",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
          }}
        >
          {error ?? "Evenemang hittades inte"}
        </p>
      </div>
    );
  }

  return (
    <div>
      <Header />

      <div
        style={{
          maxWidth: 800,
          margin: "0 auto",
          padding: "48px 24px",
        }}
      >
        {/* Event header */}
        <div style={{ marginBottom: 8 }}>
          <StatusBadge status={selectedEvent.status} />
        </div>

        <h1
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: 36,
            fontWeight: 300,
            lineHeight: 1.2,
            marginBottom: 24,
          }}
        >
          {selectedEvent.title}
        </h1>

        {/* Meta */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 24,
            marginBottom: 32,
            paddingBottom: 32,
            borderBottom: "1px solid var(--color-surface-border)",
          }}
        >
          <MetaItem
            label="Datum"
            value={formatDateTime(selectedEvent.start_time)}
          />
          {selectedEvent.venue && (
            <MetaItem label="Plats" value={selectedEvent.venue} />
          )}
          <MetaItem
            label="Kapacitet"
            value={`${selectedEvent.capacity} platser`}
          />
        </div>

        {/* Description */}
        {selectedEvent.description && (
          <p
            style={{
              fontSize: 15,
              lineHeight: 1.7,
              color: "var(--color-text-secondary)",
              marginBottom: 48,
            }}
          >
            {selectedEvent.description}
          </p>
        )}

        {/* Tiers */}
        <div className="label" style={{ marginBottom: 16 }}>
          Välj biljettyp
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 1,
            background: "var(--color-surface-border)",
            marginBottom: 32,
          }}
        >
          {tiers.map((tier) => (
            <TierCard
              key={tier.id}
              tier={tier}
              selected={tier.id === selectedTierId}
              onSelect={() => setSelectedTierId(tier.id)}
            />
          ))}
        </div>

        {tiers.length === 0 && (
          <p
            style={{
              padding: 32,
              textAlign: "center",
              color: "var(--color-text-muted)",
              fontSize: 13,
              border: "1px solid var(--color-surface-border)",
              marginBottom: 32,
            }}
          >
            Inga biljetttyper tillgängliga ännu.
          </p>
        )}

        {/* Purchase form */}
        {selectedTier && (
          <PurchaseForm
            tier={selectedTier}
            loading={loading}
            onSubmit={handlePurchase}
          />
        )}
      </div>
    </div>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="label" style={{ marginBottom: 4 }}>
        {label}
      </div>
      <span
        style={{
          fontSize: 14,
          color: "var(--color-text-primary)",
        }}
      >
        {value}
      </span>
    </div>
  );
}
