import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { AttendeeTable } from "../components/AttendeeTable";
import { useEventStore } from "../stores/eventStore";

export function AdminAttendeesPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const { selectedEvent, attendees, loading, fetchEvent, fetchAttendees } =
    useEventStore();

  useEffect(() => {
    const id = Number(eventId);
    if (id) {
      fetchEvent(id);
      fetchAttendees(id);
    }
  }, [eventId, fetchEvent, fetchAttendees]);

  const handleExportCSV = () => {
    if (!eventId) return;
    window.open(`/api/events/${eventId}/attendees/export?format=csv`, "_blank");
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
        Deltagare
      </h2>
      {selectedEvent && (
        <p className="label" style={{ marginBottom: 32 }}>
          {selectedEvent.title}
        </p>
      )}

      {loading && !attendees.length ? (
        <p
          style={{
            textAlign: "center",
            padding: 48,
            color: "var(--color-text-muted)",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
          }}
        >
          Laddar deltagarlista...
        </p>
      ) : (
        <AttendeeTable attendees={attendees} onExportCSV={handleExportCSV} />
      )}
    </div>
  );
}
