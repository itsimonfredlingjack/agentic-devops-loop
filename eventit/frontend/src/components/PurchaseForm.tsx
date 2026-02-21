import { useState } from "react";
import type { TierRead } from "../lib/api";
import { formatSEK } from "../lib/api";

export function PurchaseForm({
  tier,
  loading,
  onSubmit,
}: {
  tier: TierRead;
  loading: boolean;
  onSubmit: (name: string, email: string) => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    onSubmit(name.trim(), email.trim());
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        border: "1px solid var(--color-surface-border)",
        padding: 32,
      }}
    >
      <div className="label" style={{ marginBottom: 24 }}>
        Köp biljett — {tier.name} — {formatSEK(tier.price_cents)}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <input
          className="input-field"
          placeholder="Namn"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="input-field"
          type="email"
          placeholder="E-post"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>

      <button
        type="submit"
        className="btn-primary"
        disabled={loading || !name.trim() || !email.trim()}
        style={{ marginTop: 24, width: "100%" }}
      >
        {loading ? "Bearbetar..." : "Köp biljett"}
      </button>
    </form>
  );
}
