"use client";

import Link from "next/link";
import { formatSEK, type Product } from "@/lib/api";

export function ProductCard({
  product,
  index,
}: {
  product: Product;
  index: number;
}) {
  const minPrice = product.variants?.length
    ? Math.min(...product.variants.map((v) => v.price_cents))
    : null;

  return (
    <Link
      href={`/product/${product.id}`}
      className="group block p-6 hover:bg-surface-raised transition-colors duration-300"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Image placeholder */}
      <div className="aspect-square bg-surface-raised border border-surface-border mb-6 relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-mono text-6xl text-surface-border group-hover:text-text-muted transition-colors duration-500">
            {product.name.charAt(0)}
          </span>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-accent scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left" />
      </div>

      {/* Info */}
      <div className="space-y-2">
        <p className="label">{product.slug}</p>
        <h3 className="text-lg font-sans text-text-primary group-hover:text-accent transition-colors duration-300">
          {product.name}
        </h3>
        {product.description && (
          <p className="text-sm text-text-secondary line-clamp-2">
            {product.description}
          </p>
        )}
        {minPrice !== null && (
          <p className="price text-lg text-text-primary mt-3">
            {formatSEK(minPrice)}
          </p>
        )}
        {product.variants && product.variants.length > 1 && (
          <p className="text-text-muted text-xs font-mono">
            {product.variants.length} variants
          </p>
        )}
      </div>
    </Link>
  );
}
