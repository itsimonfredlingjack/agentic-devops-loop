"use client";

import { createContext, useContext } from "react";
import type { Cart } from "./api";

export interface CartState {
  cart: Cart | null;
  isOpen: boolean;
  loading: boolean;
}

export interface CartActions {
  setCart: (cart: Cart | null) => void;
  setOpen: (open: boolean) => void;
  setLoading: (loading: boolean) => void;
}

export type CartStore = CartState & CartActions;

export const CartContext = createContext<CartStore | null>(null);

export function useCart(): CartStore {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be inside CartProvider");
  return ctx;
}
