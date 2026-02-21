import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { EventGridPage } from "./pages/EventGridPage";
import { EventDetailPage } from "./pages/EventDetailPage";
import { PurchaseSuccessPage } from "./pages/PurchaseSuccessPage";
import { AdminLayout } from "./pages/AdminLayout";
import { AdminEventsPage } from "./pages/AdminEventsPage";
import { AdminEventDetailPage } from "./pages/AdminEventDetailPage";
import { AdminAttendeesPage } from "./pages/AdminAttendeesPage";
import { AdminCheckInPage } from "./pages/AdminCheckInPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<EventGridPage />} />
        <Route path="/events/:eventId" element={<EventDetailPage />} />
        <Route
          path="/events/:eventId/success"
          element={<PurchaseSuccessPage />}
        />

        {/* Admin routes */}
        <Route path="/admin/:slug" element={<AdminLayout />}>
          <Route index element={<AdminEventsPage />} />
          <Route path="events/:eventId" element={<AdminEventDetailPage />} />
          <Route
            path="events/:eventId/attendees"
            element={<AdminAttendeesPage />}
          />
          <Route
            path="events/:eventId/checkin"
            element={<AdminCheckInPage />}
          />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
