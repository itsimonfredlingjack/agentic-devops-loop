const BASE = "";

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  created_at: string;
}

export interface Variant {
  id: number;
  product_id: number;
  sku: string;
  name: string;
  price_cents: number;
  weight_grams: number | null;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  category_id: number | null;
  is_active: boolean;
  created_at: string;
  variants?: Variant[];
}

export interface Stock {
  id: number;
  variant_id: number;
  quantity_on_hand: number;
  quantity_reserved: number;
}

export interface CartItem {
  id: number;
  variant_id: number;
  quantity: number;
}

export interface Cart {
  id: number;
  session_id: string;
  items: CartItem[];
}

export interface OrderItem {
  id: number;
  variant_id: number;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price_cents: number;
  line_total_cents: number;
}

export interface Order {
  id: number;
  customer_email: string;
  customer_name: string;
  status: string;
  total_cents: number;
  created_at: string;
  items: OrderItem[];
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const fetchProducts = () => api<Product[]>("/api/products");
export const fetchProduct = (id: number) => api<Product>(`/api/products/${id}`);
export const fetchCategories = () => api<Category[]>("/api/categories");
export const fetchStock = (variantId: number) =>
  api<Stock>(`/api/inventory/${variantId}`);

export const fetchCart = (sessionId: string) =>
  api<Cart>(`/api/cart/${sessionId}`);
export const addToCart = (
  sessionId: string,
  variantId: number,
  quantity: number,
) =>
  api<Cart>(`/api/cart/${sessionId}/items`, {
    method: "POST",
    body: JSON.stringify({ variant_id: variantId, quantity }),
  });
export const updateCartItem = (
  sessionId: string,
  itemId: number,
  quantity: number,
) =>
  api<Cart>(`/api/cart/${sessionId}/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify({ quantity }),
  });
export const removeCartItem = (sessionId: string, itemId: number) =>
  api<Cart>(`/api/cart/${sessionId}/items/${itemId}`, {
    method: "DELETE",
  });

export const createOrder = (sessionId: string, email: string, name: string) =>
  api<Order>("/api/orders", {
    method: "POST",
    body: JSON.stringify({
      cart_session_id: sessionId,
      customer_email: email,
      customer_name: name,
    }),
  });
export const fetchOrder = (id: number) => api<Order>(`/api/orders/${id}`);

export function formatSEK(cents: number): string {
  const kr = Math.floor(cents / 100);
  return `${kr.toLocaleString("sv-SE")} kr`;
}

export function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem("storeit_session");
  if (!id) {
    id = `s-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    localStorage.setItem("storeit_session", id);
  }
  return id;
}
