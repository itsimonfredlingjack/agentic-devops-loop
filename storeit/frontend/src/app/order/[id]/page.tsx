"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchOrder, formatSEK, type Order } from "@/lib/api";

const STATUS_STEPS = ["pending", "paid", "processing", "shipped", "delivered"];

function StatusTracker({ status }: { status: string }) {
  const currentIdx = STATUS_STEPS.indexOf(status);
  const isCancelled = status === "cancelled";
  const isRefunded = status === "refunded";

  if (isCancelled || isRefunded) {
    return (
      <div className="flex items-center gap-3 py-4">
        <div className="w-3 h-3 bg-red-500" />
        <span className="font-mono text-sm uppercase tracking-[0.1em] text-red-400">
          {status}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1 py-4">
      {STATUS_STEPS.map((step, i) => (
        <div key={step} className="flex items-center gap-1 flex-1">
          <div className="flex flex-col items-center gap-2 flex-1">
            <div
              className={`w-full h-1 transition-colors duration-500 ${
                i <= currentIdx ? "bg-accent" : "bg-surface-border"
              }`}
            />
            <span
              className={`font-mono text-[9px] uppercase tracking-[0.15em] ${
                i <= currentIdx ? "text-accent" : "text-text-muted"
              }`}
            >
              {step}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function OrderPage() {
  const { id } = useParams();
  const router = useRouter();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    fetchOrder(Number(id))
      .then(setOrder)
      .catch(() => router.push("/"))
      .finally(() => setLoading(false));
  }, [id, router]);

  if (loading || !order) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <span className="font-mono text-sm text-text-muted animate-pulse">
          Loading...
        </span>
      </div>
    );
  }

  return (
    <div className="max-w-[700px] mx-auto px-6 py-16 fade-in">
      {/* Header */}
      <div className="text-center mb-16">
        <div className="w-16 h-16 mx-auto mb-6 border border-accent flex items-center justify-center">
          <span className="text-accent text-2xl">✓</span>
        </div>
        <p className="label mb-3">Order confirmed</p>
        <h1 className="text-3xl font-sans font-light tracking-tight">
          Thank you, {order.customer_name}
        </h1>
        <p className="text-text-secondary mt-3">
          Order #{order.id} &middot;{" "}
          {new Date(order.created_at).toLocaleDateString("sv-SE")}
        </p>
      </div>

      {/* Status tracker */}
      <div className="mb-12">
        <StatusTracker status={order.status} />
      </div>

      {/* Order items */}
      <div className="border border-surface-border divide-y divide-surface-border mb-8">
        {order.items.map((item) => (
          <div
            key={item.id}
            className="px-6 py-5 flex items-center justify-between"
          >
            <div>
              <p className="text-sm text-text-primary">{item.product_name}</p>
              <p className="font-mono text-xs text-text-muted mt-1">
                {item.sku} &middot; ×{item.quantity}
              </p>
            </div>
            <p className="price text-sm">{formatSEK(item.line_total_cents)}</p>
          </div>
        ))}
      </div>

      {/* Total */}
      <div className="flex items-center justify-between px-6 py-5 border border-accent">
        <span className="font-mono text-xs uppercase tracking-[0.15em] text-accent">
          Total
        </span>
        <span className="price text-xl text-accent">
          {formatSEK(order.total_cents)}
        </span>
      </div>

      {/* Actions */}
      <div className="mt-12 text-center">
        <button onClick={() => router.push("/")} className="btn-ghost">
          Continue shopping
        </button>
      </div>
    </div>
  );
}
