import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { CartProvider } from "@/components/cart-provider";
import { Header } from "@/components/header";
import { CartDrawer } from "@/components/cart-drawer";

export const metadata: Metadata = {
  title: "StoreIt",
  description: "Premium e-commerce storefront",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sv" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="font-sans bg-surface text-text-primary">
        <CartProvider>
          <Header />
          <main className="min-h-screen pt-16">{children}</main>
          <CartDrawer />
        </CartProvider>
      </body>
    </html>
  );
}
