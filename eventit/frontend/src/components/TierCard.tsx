import type { TierRead } from "../lib/api";
import { formatSEK } from "../lib/api";

export function TierCard({
  tier,
  selected,
  onSelect,
}: {
  tier: TierRead;
  selected: boolean;
  onSelect: () => void;
}) {
  const available = tier.capacity - tier.sold_count;
  const soldOut = available <= 0;
  const pct = Math.round((tier.sold_count / tier.capacity) * 100);

  return (
    <button
      onClick={onSelect}
      disabled={soldOut}
      style={{
        display: "block",
        width: "100%",
        textAlign: "left",
        padding: 24,
        background: selected
          ? "var(--color-surface-raised)"
          : "var(--color-surface)",
        border: `1px solid ${selected ? "var(--color-accent)" : "var(--color-surface-border)"}`,
        cursor: soldOut ? "not-allowed" : "pointer",
        opacity: soldOut ? 0.5 : 1,
        transition: "all 150ms ease",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: 12,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-sans)",
            fontSize: 16,
            fontWeight: 500,
            color: "var(--color-text-primary)",
          }}
        >
          {tier.name}
        </span>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 16,
            color: "var(--color-accent)",
          }}
        >
          {formatSEK(tier.price_cents)}
        </span>
      </div>

      {/* Capacity bar */}
      <div
        style={{
          height: 4,
          background: "var(--color-surface-border)",
          marginBottom: 8,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: soldOut
              ? "var(--color-status-cancelled)"
              : "var(--color-accent)",
            transition: "width 300ms ease",
          }}
        />
      </div>

      {/* Availability label */}
      <span className="label">
        {soldOut ? "Slutsålt" : `${available} av ${tier.capacity} kvar`}
      </span>
    </button>
  );
}
