"use client";

import Link from "next/link";
import { useCart } from "@/lib/cart-store";

export function Header() {
  const { cart, setOpen } = useCart();
  const itemCount = cart?.items.reduce((sum, i) => sum + i.quantity, 0) ?? 0;

  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-surface/80 backdrop-blur-xl border-b border-surface-border">
      <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-7 h-7 bg-accent flex items-center justify-center">
            <span className="text-surface text-[10px] font-mono font-bold">
              S
            </span>
          </div>
          <span className="font-mono text-sm tracking-[0.3em] uppercase text-text-primary group-hover:text-accent transition-colors">
            StoreIt
          </span>
        </Link>

        <button
          onClick={() => setOpen(true)}
          className="relative font-mono text-xs tracking-[0.15em] uppercase text-text-secondary hover:text-text-primary transition-colors px-4 py-2"
        >
          Cart
          {itemCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-accent text-surface text-[10px] font-mono flex items-center justify-center">
              {itemCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
