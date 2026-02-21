"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  fetchProduct,
  fetchStock,
  addToCart,
  getSessionId,
  formatSEK,
  type Product,
  type Stock,
  type Variant,
} from "@/lib/api";
import { useCart } from "@/lib/cart-store";

export default function ProductPage() {
  const { id } = useParams();
  const router = useRouter();
  const { setCart, setOpen } = useCart();

  const [product, setProduct] = useState<Product | null>(null);
  const [stocks, setStocks] = useState<Record<number, Stock>>({});
  const [selectedVariant, setSelectedVariant] = useState<Variant | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetchProduct(Number(id))
      .then((p) => {
        setProduct(p);
        if (p.variants?.length) {
          setSelectedVariant(p.variants[0]);
          Promise.all(
            p.variants.map((v) =>
              fetchStock(v.id)
                .then((s) => [v.id, s] as const)
                .catch(() => [v.id, null] as const),
            ),
          ).then((results) => {
            const map: Record<number, Stock> = {};
            for (const [vid, stock] of results) {
              if (stock) map[vid] = stock;
            }
            setStocks(map);
          });
        }
      })
      .catch(() => router.push("/"));
  }, [id, router]);

  if (!product) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <span className="font-mono text-sm text-text-muted animate-pulse">
          Loading...
        </span>
      </div>
    );
  }

  const variant = selectedVariant;
  const stock = variant ? stocks[variant.id] : null;
  const available = stock
    ? stock.quantity_on_hand - stock.quantity_reserved
    : 0;

  const handleAdd = async () => {
    if (!variant) return;
    setAdding(true);
    try {
      const updated = await addToCart(getSessionId(), variant.id, quantity);
      setCart(updated);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto px-6 py-12 fade-in">
      {/* Breadcrumb */}
      <nav className="mb-12">
        <button
          onClick={() => router.push("/")}
          className="label hover:text-text-secondary transition-colors"
        >
          &larr; Back to catalog
        </button>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
        {/* Product image */}
        <div className="aspect-square bg-surface-raised border border-surface-border relative">
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="font-mono text-[120px] text-surface-border">
              {product.name.charAt(0)}
            </span>
          </div>
        </div>

        {/* Product info */}
        <div className="space-y-8 py-4">
          <div>
            <p className="label mb-3">{product.slug}</p>
            <h1 className="text-4xl font-sans font-light tracking-tight">
              {product.name}
            </h1>
          </div>

          {product.description && (
            <p className="text-text-secondary leading-relaxed">
              {product.description}
            </p>
          )}

          {variant && (
            <p className="price text-3xl">{formatSEK(variant.price_cents)}</p>
          )}

          {/* Variant selector */}
          {product.variants && product.variants.length > 1 && (
            <div>
              <p className="label mb-3">Variant</p>
              <div className="flex gap-2">
                {product.variants.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => {
                      setSelectedVariant(v);
                      setQuantity(1);
                    }}
                    className={`px-5 py-3 border font-mono text-xs tracking-[0.1em] uppercase transition-colors ${
                      selectedVariant?.id === v.id
                        ? "border-accent text-accent"
                        : "border-surface-border text-text-secondary hover:border-text-muted hover:text-text-primary"
                    }`}
                  >
                    {v.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Stock indicator */}
          {stock && (
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 ${
                  available > 5
                    ? "bg-green-500"
                    : available > 0
                      ? "bg-yellow-500"
                      : "bg-red-500"
                }`}
              />
              <span className="font-mono text-xs text-text-secondary">
                {available > 0 ? `${available} in stock` : "Out of stock"}
              </span>
            </div>
          )}

          {/* Quantity + Add to cart */}
          <div className="flex items-center gap-4">
            <div className="flex items-center border border-surface-border">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-12 h-12 flex items-center justify-center text-text-secondary hover:text-text-primary transition-colors font-mono"
              >
                −
              </button>
              <span className="w-12 h-12 flex items-center justify-center font-mono text-sm border-x border-surface-border">
                {quantity}
              </span>
              <button
                onClick={() =>
                  setQuantity(Math.min(available || 99, quantity + 1))
                }
                className="w-12 h-12 flex items-center justify-center text-text-secondary hover:text-text-primary transition-colors font-mono"
              >
                +
              </button>
            </div>

            <button
              onClick={handleAdd}
              disabled={adding || available === 0}
              className="btn-primary flex-1 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {added
                ? "Added ✓"
                : adding
                  ? "Adding..."
                  : available === 0
                    ? "Out of stock"
                    : "Add to cart"}
            </button>
          </div>

          {/* SKU */}
          {variant && (
            <div className="pt-8 border-t border-surface-border">
              <div className="flex justify-between text-xs">
                <span className="font-mono text-text-muted">SKU</span>
                <span className="font-mono text-text-secondary">
                  {variant.sku}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
