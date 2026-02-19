import { useBookingStore } from "./stores/bookingStore";
import { AppShell } from "./components/AppShell";
import { Header } from "./components/Header";
import { Calendar } from "./components/Calendar";
import { MyBookings } from "./components/MyBookings";
import { AdminPanel } from "./components/AdminPanel";

export function App() {
  const view = useBookingStore((s) => s.view);

  return (
    <AppShell>
      <Header />
      {view === "calendar" && <Calendar />}
      {view === "my-bookings" && <MyBookings />}
      {view === "admin" && <AdminPanel />}
    </AppShell>
  );
}
