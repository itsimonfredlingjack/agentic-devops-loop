"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCart } from "@/lib/cart-store";
import { createOrder, getSessionId } from "@/lib/api";

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, setCart } = useCart();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const items = cart?.items ?? [];
  const isEmpty = items.length === 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) {
      setError("All fields are required");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const order = await createOrder(
        getSessionId(),
        email.trim(),
        name.trim(),
      );
      setCart(null);
      // Clear session for new cart
      localStorage.removeItem("storeit_session");
      router.push(`/order/${order.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  if (isEmpty) {
    return (
      <div className="max-w-[600px] mx-auto px-6 py-32 text-center fade-in">
        <p className="label mb-4">Checkout</p>
        <p className="text-text-secondary text-lg">Your cart is empty</p>
        <button onClick={() => router.push("/")} className="btn-ghost mt-8">
          Browse products
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-[600px] mx-auto px-6 py-16 fade-in">
      <p className="label mb-3">Checkout</p>
      <h1 className="text-3xl font-sans font-light tracking-tight mb-12">
        Complete your order
      </h1>

      {/* Cart summary */}
      <div className="border border-surface-border p-6 mb-10 space-y-3">
        <p className="label">Order summary</p>
        {items.map((item) => (
          <div
            key={item.id}
            className="flex justify-between text-sm text-text-secondary"
          >
            <span>Variant #{item.variant_id}</span>
            <span className="font-mono">×{item.quantity}</span>
          </div>
        ))}
      </div>

      {/* Customer form */}
      <form onSubmit={handleSubmit} className="space-y-8">
        <div>
          <label className="label block mb-2">Full name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Simon Fredling"
            className="input-field"
            required
          />
        </div>

        <div>
          <label className="label block mb-2">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="simon@example.com"
            className="input-field"
            required
          />
        </div>

        {error && <p className="text-accent text-sm font-mono">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="btn-primary w-full text-center disabled:opacity-50"
        >
          {submitting ? "Placing order..." : "Place order"}
        </button>
      </form>
    </div>
  );
}
