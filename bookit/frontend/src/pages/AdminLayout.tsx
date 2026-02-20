import { useEffect } from "react";
import { Outlet, useParams } from "react-router-dom";
import { useBookingStore } from "../stores/bookingStore";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";

export function AdminLayout() {
  const { slug } = useParams<{ slug: string }>();
  const setTenant = useBookingStore((s) => s.setTenant);

  useEffect(() => {
    if (slug) {
      setTenant(slug);
    }
  }, [slug, setTenant]);

  return (
    <AppShell>
      <Header />
      <Outlet />
    </AppShell>
  );
}
