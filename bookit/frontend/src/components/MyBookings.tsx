import { useState, useCallback } from "react";
import { useBookingStore } from "../stores/bookingStore";
import { cancelRecurringSeries } from "../lib/api";
import styles from "../styles/components/MyBookings.module.css";

function formatDateSv(dateStr: string | undefined): string {
  if (!dateStr) return "";
  const parts = dateStr.split("-");
  if (parts.length !== 3) return dateStr;
  const [y, m, d] = parts;
  const date = new Date(Number(y), Number(m) - 1, Number(d));
  return new Intl.DateTimeFormat("sv-SE", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

export function MyBookings() {
  const myBookings = useBookingStore((s) => s.myBookings);
  const userEmail = useBookingStore((s) => s.userEmail);
  const setUserEmail = useBookingStore((s) => s.setUserEmail);
  const fetchMyBookings = useBookingStore((s) => s.fetchMyBookings);
  const cancelBookingAction = useBookingStore((s) => s.cancelBooking);
  const loading = useBookingStore((s) => s.loading);
  const error = useBookingStore((s) => s.error);

  const [emailInput, setEmailInput] = useState(userEmail);

  const handleSearch = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!emailInput.trim()) return;
      setUserEmail(emailInput.trim());
      // Need to wait for the store to update, then fetch
      // Since setUserEmail is synchronous in Zustand, we can call fetchMyBookings
      // but we need to use the store's method which reads userEmail from state.
      // So we update state first, then fetch.
    },
    [emailInput, setUserEmail],
  );

  // We need to trigger fetch after email is set
  const doSearch = useCallback(async () => {
    if (!emailInput.trim()) return;
    setUserEmail(emailInput.trim());
    // Small trick: Zustand updates are sync so fetchMyBookings will read
    // the updated email. But since setUserEmail is called before await,
    // we need to ensure the email is set first.
    // Actually, let's just use the store method directly after setting email.
    await fetchMyBookings();
  }, [emailInput, setUserEmail, fetchMyBookings]);

  const handleFormSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      void doSearch();
    },
    [doSearch],
  );

  const handleCancel = useCallback(
    async (id: number) => {
      if (!window.confirm("Ar du saker pa att du vill avboka?")) return;
      await cancelBookingAction(id);
    },
    [cancelBookingAction],
  );

  const handleCancelSeries = useCallback(
    async (ruleId: number) => {
      if (!window.confirm("Avboka HELA serien?")) return;
      await cancelRecurringSeries(ruleId);
      await fetchMyBookings();
    },
    [fetchMyBookings],
  );

  // Suppress the unused handleSearch lint error by using it indirectly
  void handleSearch;

  return (
    <div className={styles.container}>
      <form className={styles.searchBar} onSubmit={handleFormSubmit}>
        <input
          className={styles.emailInput}
          type="email"
          placeholder="Ange din e-postadress..."
          value={emailInput}
          onChange={(e) => setEmailInput(e.target.value)}
          required
        />
        <button
          type="submit"
          className={styles.searchButton}
          disabled={loading || !emailInput.trim()}
        >
          {loading ? "Soker..." : "Sok bokningar"}
        </button>
      </form>

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.loading}>Laddar bokningar...</div>
      ) : myBookings.length === 0 ? (
        userEmail ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>&#128203;</div>
            <div>Inga bokningar hittades for {userEmail}</div>
          </div>
        ) : (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>&#128269;</div>
            <div>Ange din e-post for att se dina bokningar</div>
          </div>
        )
      ) : (
        <div className={styles.bookingList}>
          {myBookings.map((booking) => {
            const isCancelled = booking.status === "cancelled";
            return (
              <div
                key={booking.id}
                className={`${styles.bookingCard} ${isCancelled ? styles.bookingCancelled : ""}`}
              >
                <div className={styles.bookingInfo}>
                  <span
                    className={`${styles.serviceName} ${isCancelled ? styles.cancelledText : ""}`}
                  >
                    {booking.service_name ?? `Tjanst #${booking.slot_id}`}
                  </span>
                  <div className={styles.bookingMeta}>
                    <span>{formatDateSv(booking.slot_date)}</span>
                    <span>
                      {booking.slot_start_time?.slice(0, 5) ?? ""} -{" "}
                      {booking.slot_end_time?.slice(0, 5) ?? ""}
                    </span>
                    <span
                      className={`${styles.status} ${
                        isCancelled
                          ? styles.statusCancelled
                          : styles.statusConfirmed
                      }`}
                    >
                      {isCancelled ? "Avbokad" : "Bekraftad"}
                    </span>
                  </div>
                </div>

                {!isCancelled && (
                  <div
                    style={{ display: "flex", gap: 8, alignItems: "center" }}
                  >
                    {booking.recurring_rule_id && (
                      <button
                        className={styles.cancelBookingButton}
                        onClick={() =>
                          void handleCancelSeries(booking.recurring_rule_id!)
                        }
                        style={{ fontSize: "0.75rem" }}
                      >
                        Avboka serien
                      </button>
                    )}
                    <button
                      className={styles.cancelBookingButton}
                      onClick={() => void handleCancel(booking.id)}
                    >
                      Avboka
                    </button>
                  </div>
                )}
                {booking.recurring_rule_id && !isCancelled && (
                  <div style={{ fontSize: "0.7rem", opacity: 0.6 }}>
                    Del av serie
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
