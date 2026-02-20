import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { PublicBookingPage } from "./pages/PublicBookingPage";
import { BookingSuccess } from "./pages/BookingSuccess";
import { AdminLayout } from "./pages/AdminLayout";
import { Calendar } from "./components/Calendar";
import { MyBookings } from "./components/MyBookings";
import { AdminPanel } from "./components/AdminPanel";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/book/:slug" element={<PublicBookingPage />} />
        <Route path="/book/:slug/success" element={<BookingSuccess />} />
        <Route path="/admin/:slug" element={<AdminLayout />}>
          <Route index element={<Calendar />} />
          <Route path="bookings" element={<MyBookings />} />
          <Route path="manage" element={<AdminPanel />} />
        </Route>
        <Route path="/" element={<Navigate to="/admin/demo" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
