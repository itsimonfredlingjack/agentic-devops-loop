import type { TicketRead } from "../lib/api";

export function AttendeeTable({
  attendees,
  onExportCSV,
}: {
  attendees: TicketRead[];
  onExportCSV?: () => void;
}) {
  return (
    <div>
      {/* Toolbar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <span className="label">{attendees.length} deltagare</span>
        {onExportCSV && (
          <button className="btn-ghost" onClick={onExportCSV}>
            Exportera CSV
          </button>
        )}
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontFamily: "var(--font-sans)",
            fontSize: 13,
          }}
        >
          <thead>
            <tr>
              {["Namn", "E-post", "Status", "QR-kod"].map((h) => (
                <th
                  key={h}
                  className="label"
                  style={{
                    textAlign: "left",
                    padding: "12px 16px",
                    borderBottom: "1px solid var(--color-surface-border)",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {attendees.map((a) => (
              <tr
                key={a.id}
                style={{
                  borderBottom: "1px solid var(--color-surface-border)",
                }}
              >
                <td
                  style={{
                    padding: "12px 16px",
                    color: "var(--color-text-primary)",
                  }}
                >
                  {a.attendee_name}
                </td>
                <td
                  style={{
                    padding: "12px 16px",
                    color: "var(--color-text-secondary)",
                  }}
                >
                  {a.attendee_email}
                </td>
                <td style={{ padding: "12px 16px" }}>
                  <StatusDot status={a.status} />
                </td>
                <td
                  style={{
                    padding: "12px 16px",
                    fontFamily: "var(--font-mono)",
                    fontSize: 11,
                    color: "var(--color-text-muted)",
                  }}
                >
                  {a.qr_code.slice(0, 8)}...
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {attendees.length === 0 && (
        <p
          style={{
            textAlign: "center",
            padding: 48,
            color: "var(--color-text-muted)",
            fontSize: 14,
          }}
        >
          Inga deltagare ännu.
        </p>
      )}
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    confirmed: "var(--color-accent)",
    checked_in: "var(--color-status-completed)",
    cancelled: "var(--color-status-cancelled)",
  };
  return (
    <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: colors[status] ?? "var(--color-text-muted)",
        }}
      />
      <span
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          textTransform: "uppercase",
          letterSpacing: "0.1em",
          color: "var(--color-text-secondary)",
        }}
      >
        {status.replace("_", " ")}
      </span>
    </span>
  );
}
