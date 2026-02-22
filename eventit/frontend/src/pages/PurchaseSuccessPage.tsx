import { Link, useLocation } from "react-router-dom";
import { Header } from "../components/Header";
import type { TicketRead } from "../lib/api";

export function PurchaseSuccessPage() {
  const location = useLocation();
  const ticket = (location.state as { ticket?: TicketRead } | null)?.ticket;

  return (
    <div>
      <Header />

      <div
        style={{
          maxWidth: 600,
          margin: "0 auto",
          padding: "80px 24px",
          textAlign: "center",
        }}
      >
        {/* Success indicator */}
        <div
          style={{
            width: 64,
            height: 64,
            margin: "0 auto 24px",
            background: "var(--color-accent)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 32,
          }}
        >
          <span style={{ color: "var(--color-surface)" }}>&#10003;</span>
        </div>

        <h1
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: 28,
            fontWeight: 300,
            marginBottom: 12,
          }}
        >
          Biljett bekräftad
        </h1>

        <p
          style={{
            color: "var(--color-text-secondary)",
            fontSize: 14,
            marginBottom: 48,
          }}
        >
          Din biljett har skapats. Visa QR-koden vid entrén.
        </p>

        {/* QR Code */}
        {ticket?.qr_image_b64 && (
          <div
            style={{
              display: "inline-block",
              padding: 24,
              background: "white",
              marginBottom: 32,
            }}
          >
            <img
              src={`data:image/png;base64,${ticket.qr_image_b64}`}
              alt="QR-kod"
              style={{ width: 200, height: 200 }}
            />
          </div>
        )}

        {/* Ticket details */}
        {ticket && (
          <div
            style={{
              border: "1px solid var(--color-surface-border)",
              padding: 24,
              textAlign: "left",
              marginBottom: 32,
            }}
          >
            <div className="label" style={{ marginBottom: 16 }}>
              Biljettdetaljer
            </div>
            <DetailRow label="Namn" value={ticket.attendee_name} />
            <DetailRow label="E-post" value={ticket.attendee_email} />
            <DetailRow label="Status" value={ticket.status} />
            <DetailRow label="QR-kod" value={ticket.qr_code} mono />
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", gap: 16, justifyContent: "center" }}>
          {ticket?.qr_image_b64 && (
            <a
              href={`data:image/png;base64,${ticket.qr_image_b64}`}
              download={`ticket-${ticket.qr_code.slice(0, 8)}.png`}
              className="btn-ghost"
            >
              Spara QR
            </a>
          )}
          <Link
            to="/"
            className="btn-primary"
            style={{ display: "inline-block" }}
          >
            Tillbaka
          </Link>
        </div>
      </div>
    </div>
  );
}

function DetailRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        padding: "8px 0",
        borderBottom: "1px solid var(--color-surface-border)",
      }}
    >
      <span className="label">{label}</span>
      <span
        style={{
          fontSize: mono ? 11 : 13,
          color: "var(--color-text-primary)",
          fontFamily: mono ? "var(--font-mono)" : "var(--font-sans)",
        }}
      >
        {value}
      </span>
    </div>
  );
}
