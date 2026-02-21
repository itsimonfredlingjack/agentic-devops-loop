import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { useEventStore } from "../stores/eventStore";
import { formatDateTime } from "../lib/api";
import type { EventCreate } from "../lib/api";

export function AdminEventsPage() {
  const { slug } = useParams<{ slug: string }>();
  const {
    events,
    loading,
    error,
    fetchTenantEvents,
    createEvent,
    transitionEvent,
  } = useEventStore();
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchTenantEvents();
  }, [fetchTenantEvents]);

  const handleCreate = async (data: EventCreate) => {
    await createEvent(data);
    setShowForm(false);
  };

  return (
    <div>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 32,
        }}
      >
        <h2
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: 24,
            fontWeight: 300,
          }}
        >
          Evenemang
        </h2>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Avbryt" : "Skapa Event"}
        </button>
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

      {/* Create form */}
      {showForm && (
        <CreateEventForm loading={loading} onSubmit={handleCreate} />
      )}

      {/* Events list */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 1,
          background: "var(--color-surface-border)",
        }}
      >
        {events.map((event) => (
          <div
            key={event.id}
            style={{
              background: "var(--color-surface)",
              padding: 24,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
            }}
          >
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  marginBottom: 8,
                }}
              >
                <Link
                  to={`/admin/${slug}/events/${event.id}`}
                  style={{
                    fontSize: 16,
                    fontWeight: 500,
                    color: "var(--color-text-primary)",
                    transition: "color 150ms ease",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.color = "var(--color-accent)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.color = "var(--color-text-primary)")
                  }
                >
                  {event.title}
                </Link>
                <StatusBadge status={event.status} />
              </div>
              <span className="label">
                {formatDateTime(event.start_time)}
                {event.venue ? ` — ${event.venue}` : ""}
              </span>
            </div>

            {/* Quick actions */}
            <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
              {event.status === "draft" && (
                <button
                  className="btn-ghost"
                  onClick={() => transitionEvent(event.id, "published")}
                >
                  Publicera
                </button>
              )}
              {event.status === "published" && (
                <>
                  <Link
                    to={`/admin/${slug}/events/${event.id}/attendees`}
                    className="btn-ghost"
                    style={{ display: "inline-block" }}
                  >
                    Deltagare
                  </Link>
                  <Link
                    to={`/admin/${slug}/events/${event.id}/checkin`}
                    className="btn-ghost"
                    style={{ display: "inline-block" }}
                  >
                    Check-in
                  </Link>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {!loading && events.length === 0 && (
        <p
          style={{
            textAlign: "center",
            padding: 48,
            color: "var(--color-text-muted)",
            fontSize: 14,
          }}
        >
          Inga evenemang. Klicka "Skapa Event" för att börja.
        </p>
      )}
    </div>
  );
}

function CreateEventForm({
  loading,
  onSubmit,
}: {
  loading: boolean;
  onSubmit: (data: EventCreate) => void;
}) {
  const [title, setTitle] = useState("");
  const [venue, setVenue] = useState("");
  const [description, setDescription] = useState("");
  const [capacity, setCapacity] = useState("100");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !startDate || !endDate) return;
    const slug = title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    onSubmit({
      title: title.trim(),
      slug,
      description: description.trim() || undefined,
      venue: venue.trim() || undefined,
      start_time: new Date(startDate).toISOString(),
      end_time: new Date(endDate).toISOString(),
      capacity: parseInt(capacity) || 100,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        border: "1px solid var(--color-surface-border)",
        padding: 32,
        marginBottom: 32,
      }}
    >
      <div className="label" style={{ marginBottom: 24 }}>
        Nytt evenemang
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 16,
        }}
      >
        <input
          className="input-field"
          placeholder="Titel"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          style={{ gridColumn: "1 / -1" }}
        />
        <input
          className="input-field"
          placeholder="Plats"
          value={venue}
          onChange={(e) => setVenue(e.target.value)}
        />
        <input
          className="input-field"
          placeholder="Kapacitet"
          type="number"
          value={capacity}
          onChange={(e) => setCapacity(e.target.value)}
        />
        <input
          className="input-field"
          type="datetime-local"
          placeholder="Start"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          required
        />
        <input
          className="input-field"
          type="datetime-local"
          placeholder="Slut"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          required
        />
        <textarea
          className="input-field"
          placeholder="Beskrivning (valfritt)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          style={{
            gridColumn: "1 / -1",
            resize: "vertical",
            border: "1px solid var(--color-surface-border)",
            padding: 12,
          }}
        />
      </div>

      <button
        type="submit"
        className="btn-primary"
        disabled={loading || !title.trim() || !startDate || !endDate}
        style={{ marginTop: 24 }}
      >
        {loading ? "Skapar..." : "Skapa evenemang"}
      </button>
    </form>
  );
}
