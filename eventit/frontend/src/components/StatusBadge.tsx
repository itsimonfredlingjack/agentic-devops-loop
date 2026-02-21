import type { EventStatus } from "../lib/api";

const STATUS_COLORS: Record<EventStatus, string> = {
  draft: "var(--color-status-draft)",
  published: "var(--color-status-published)",
  cancelled: "var(--color-status-cancelled)",
  completed: "var(--color-status-completed)",
};

const STATUS_LABELS: Record<EventStatus, string> = {
  draft: "Draft",
  published: "Live",
  cancelled: "Cancelled",
  completed: "Completed",
};

export function StatusBadge({ status }: { status: EventStatus }) {
  const color = STATUS_COLORS[status];
  return (
    <span
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        textTransform: "uppercase",
        letterSpacing: "0.15em",
        color,
        border: `1px solid ${color}`,
        padding: "4px 10px",
        display: "inline-block",
      }}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
