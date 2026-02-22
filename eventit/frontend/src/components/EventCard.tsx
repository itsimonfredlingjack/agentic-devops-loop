import { Link } from "react-router-dom";
import type { EventRead } from "../lib/api";
import { formatDate, formatSEK } from "../lib/api";

export function EventCard({
  event,
  priceRange,
}: {
  event: EventRead;
  priceRange?: { min: number; max: number } | null;
}) {
  return (
    <Link
      to={`/events/${event.id}`}
      style={{
        display: "block",
        padding: 32,
        transition: "background 150ms ease",
        cursor: "pointer",
        position: "relative",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "var(--color-surface-raised)";
        const bar = e.currentTarget.querySelector(
          "[data-accent-bar]",
        ) as HTMLElement | null;
        if (bar) bar.style.width = "100%";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "var(--color-surface)";
        const bar = e.currentTarget.querySelector(
          "[data-accent-bar]",
        ) as HTMLElement | null;
        if (bar) bar.style.width = "0";
      }}
    >
      {/* Placeholder square with first letter */}
      <div
        style={{
          width: "100%",
          aspectRatio: "16/9",
          background: "var(--color-surface-overlay)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 24,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 64,
            color: "var(--color-surface-border)",
            fontWeight: 700,
          }}
        >
          {event.title.charAt(0).toUpperCase()}
        </span>
      </div>

      {/* Slug label */}
      <div className="label" style={{ marginBottom: 8 }}>
        {event.slug}
      </div>

      {/* Title */}
      <h3
        style={{
          fontFamily: "var(--font-sans)",
          fontSize: 18,
          fontWeight: 400,
          marginBottom: 8,
          color: "var(--color-text-primary)",
          lineHeight: 1.3,
        }}
      >
        {event.title}
      </h3>

      {/* Description */}
      {event.description && (
        <p
          style={{
            fontSize: 13,
            color: "var(--color-text-secondary)",
            lineHeight: 1.5,
            marginBottom: 16,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {event.description}
        </p>
      )}

      {/* Meta row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          gap: 16,
        }}
      >
        <span className="label">
          {formatDate(event.start_time)}
          {event.venue ? ` — ${event.venue}` : ""}
        </span>
        {priceRange && (
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 14,
              color: "var(--color-accent)",
            }}
          >
            {priceRange.min === priceRange.max
              ? formatSEK(priceRange.min)
              : `${formatSEK(priceRange.min)} – ${formatSEK(priceRange.max)}`}
          </span>
        )}
      </div>

      {/* Accent underline bar */}
      <div
        data-accent-bar
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          height: 2,
          width: 0,
          background: "var(--color-accent)",
          transition: "width 300ms ease",
        }}
      />
    </Link>
  );
}
