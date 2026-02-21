"use client";

import { useState, useCallback, useEffect } from "react";
import { CartContext, type CartState } from "@/lib/cart-store";
import { fetchCart, getSessionId, type Cart } from "@/lib/api";

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<CartState>({
    cart: null,
    isOpen: false,
    loading: false,
  });

  const setCart = useCallback((cart: Cart | null) => {
    setState((s) => ({ ...s, cart }));
  }, []);

  const setOpen = useCallback((isOpen: boolean) => {
    setState((s) => ({ ...s, isOpen }));
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState((s) => ({ ...s, loading }));
  }, []);

  useEffect(() => {
    const sid = getSessionId();
    if (sid) {
      fetchCart(sid)
        .then(setCart)
        .catch(() => {});
    }
  }, [setCart]);

  return (
    <CartContext.Provider value={{ ...state, setCart, setOpen, setLoading }}>
      {children}
    </CartContext.Provider>
  );
}
