"use client";

import { useRouter } from "next/navigation";
import { useCart } from "@/lib/cart-store";
import {
  formatSEK,
  getSessionId,
  removeCartItem,
  updateCartItem,
} from "@/lib/api";

export function CartDrawer() {
  const { cart, isOpen, setOpen, setCart, loading, setLoading } = useCart();
  const router = useRouter();

  if (!isOpen) return null;

  const items = cart?.items ?? [];
  const isEmpty = items.length === 0;

  const handleRemove = async (itemId: number) => {
    setLoading(true);
    try {
      const updated = await removeCartItem(getSessionId(), itemId);
      setCart(updated);
    } finally {
      setLoading(false);
    }
  };

  const handleQuantity = async (itemId: number, qty: number) => {
    if (qty < 1) return handleRemove(itemId);
    setLoading(true);
    try {
      const updated = await updateCartItem(getSessionId(), itemId, qty);
      setCart(updated);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckout = () => {
    setOpen(false);
    router.push("/checkout");
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
        style={{ animation: "fadeOverlay 0.2s ease-out both" }}
        onClick={() => setOpen(false)}
      />

      {/* Drawer */}
      <div
        className="fixed top-0 right-0 bottom-0 z-50 w-full max-w-md bg-surface border-l border-surface-border flex flex-col"
        style={{
          animation: "slideInRight 0.3s cubic-bezier(0.16, 1, 0.3, 1) both",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 h-16 border-b border-surface-border">
          <span className="label">Cart ({items.length})</span>
          <button
            onClick={() => setOpen(false)}
            className="text-text-muted hover:text-text-primary transition-colors font-mono text-xs"
          >
            Close
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto">
          {isEmpty ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-text-muted font-mono text-sm">Empty</p>
            </div>
          ) : (
            <div className="divide-y divide-surface-border">
              {items.map((item) => (
                <div key={item.id} className="px-6 py-5 flex gap-4">
                  {/* Placeholder image */}
                  <div className="w-16 h-16 bg-surface-raised border border-surface-border flex-shrink-0 flex items-center justify-center">
                    <span className="text-text-muted text-[10px] font-mono">
                      {item.variant_id}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-text-primary truncate">
                      Variant #{item.variant_id}
                    </p>
                    <div className="flex items-center gap-3 mt-2">
                      <button
                        onClick={() =>
                          handleQuantity(item.id, item.quantity - 1)
                        }
                        disabled={loading}
                        className="w-7 h-7 border border-surface-border text-text-secondary hover:text-text-primary hover:border-text-muted transition-colors font-mono text-xs flex items-center justify-center"
                      >
                        −
                      </button>
                      <span className="font-mono text-sm w-6 text-center">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() =>
                          handleQuantity(item.id, item.quantity + 1)
                        }
                        disabled={loading}
                        className="w-7 h-7 border border-surface-border text-text-secondary hover:text-text-primary hover:border-text-muted transition-colors font-mono text-xs flex items-center justify-center"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  <button
                    onClick={() => handleRemove(item.id)}
                    disabled={loading}
                    className="text-text-muted hover:text-accent transition-colors text-xs font-mono self-start"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {!isEmpty && (
          <div className="border-t border-surface-border px-6 py-5 space-y-4">
            <button
              onClick={handleCheckout}
              className="btn-primary w-full text-center"
            >
              Checkout
            </button>
          </div>
        )}
      </div>
    </>
  );
}
