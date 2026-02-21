"use client";

import { useEffect, useState } from "react";
import {
  fetchProducts,
  fetchCategories,
  type Product,
  type Category,
} from "@/lib/api";
import { ProductCard } from "@/components/product-card";

export default function CatalogPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [activeCategory, setActiveCategory] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchProducts(), fetchCategories()])
      .then(([p, c]) => {
        setProducts(p);
        setCategories(c);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = activeCategory
    ? products.filter((p) => p.category_id === activeCategory)
    : products;

  return (
    <div className="fade-in">
      {/* Hero */}
      <section className="max-w-[1400px] mx-auto px-6 py-20">
        <div className="max-w-2xl space-y-6">
          <p className="label">Product catalog</p>
          <h1 className="text-5xl md:text-7xl font-sans font-light leading-[0.95] tracking-tight">
            Engineered
            <br />
            <span className="text-accent">essentials</span>
          </h1>
          <p className="text-text-secondary text-lg leading-relaxed max-w-md">
            Precision-crafted products for people who appreciate the details
            that matter.
          </p>
        </div>
      </section>

      {/* Category filter */}
      <section className="border-t border-surface-border">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex gap-1 overflow-x-auto">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-4 py-2 font-mono text-xs tracking-[0.15em] uppercase transition-colors whitespace-nowrap ${
              activeCategory === null
                ? "bg-text-primary text-surface"
                : "text-text-secondary hover:text-text-primary"
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`px-4 py-2 font-mono text-xs tracking-[0.15em] uppercase transition-colors whitespace-nowrap ${
                activeCategory === cat.id
                  ? "bg-text-primary text-surface"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
      </section>

      {/* Product grid */}
      <section className="border-t border-surface-border">
        {loading ? (
          <div className="flex items-center justify-center py-32">
            <span className="font-mono text-sm text-text-muted animate-pulse">
              Loading...
            </span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex items-center justify-center py-32">
            <span className="font-mono text-sm text-text-muted">
              No products found
            </span>
          </div>
        ) : (
          <div className="product-grid">
            {filtered.map((product, i) => (
              <ProductCard key={product.id} product={product} index={i} />
            ))}
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-surface-border mt-20">
        <div className="max-w-[1400px] mx-auto px-6 py-12 flex items-center justify-between">
          <span className="font-mono text-xs text-text-muted tracking-[0.2em] uppercase">
            StoreIt &copy; 2026
          </span>
          <span className="font-mono text-xs text-text-muted">
            PostgreSQL + FastAPI + Next.js
          </span>
        </div>
      </footer>
    </div>
  );
}
