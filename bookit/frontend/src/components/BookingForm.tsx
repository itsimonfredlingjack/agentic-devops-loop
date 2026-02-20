import { useState, useCallback } from "react";
import { useBookingStore } from "../stores/bookingStore";
import { createCheckoutSession } from "../lib/api";
import type { Slot } from "../lib/api";
import styles from "../styles/components/BookingForm.module.css";

interface BookingFormProps {
  slot: Slot;
  serviceName: string;
  priceCents?: number;
  tenantSlug?: string;
  onClose: () => void;
  onBooked: () => void;
}

function formatDateSv(dateStr: string): string {
  const parts = dateStr.split("-");
  if (parts.length !== 3) return dateStr;
  const [y, m, d] = parts;
  const date = new Date(Number(y), Number(m) - 1, Number(d));
  return new Intl.DateTimeFormat("sv-SE", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(date);
}

export function BookingForm({
  slot,
  serviceName,
  priceCents = 0,
  tenantSlug,
  onClose,
  onBooked,
}: BookingFormProps) {
  const isPaid = priceCents > 0;
  const bookSlot = useBookingStore((s) => s.bookSlot);
  const storedEmail = useBookingStore((s) => s.userEmail);

  const [name, setName] = useState("");
  const [email, setEmail] = useState(storedEmail);
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!name.trim() || !email.trim()) return;

      setSubmitting(true);
      setError(null);
      try {
        if (isPaid && tenantSlug) {
          const checkout = await createCheckoutSession({
            slot_id: slot.id,
            customer_name: name.trim(),
            customer_email: email.trim(),
            customer_phone: phone.trim() || undefined,
            tenant_slug: tenantSlug,
          });
          window.location.href = checkout.checkout_url;
          return;
        }
        await bookSlot(
          slot.id,
          name.trim(),
          email.trim(),
          phone.trim() || undefined,
        );
        setSuccess(true);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Ett fel uppstod vid bokning",
        );
      } finally {
        setSubmitting(false);
      }
    },
    [name, email, phone, slot.id, bookSlot],
  );

  // Click outside to close
  const handleOverlayClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) {
        if (success) {
          onBooked();
        } else {
          onClose();
        }
      }
    },
    [success, onBooked, onClose],
  );

  return (
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <div className={styles.modal}>
        {success ? (
          <div className={styles.success}>
            <div className={styles.successMessage}>Bokning bekraftad!</div>
            <div className={styles.successDetail}>
              {serviceName} den {formatDateSv(slot.date)} kl{" "}
              {slot.start_time.slice(0, 5)}
            </div>
            <div className={styles.successDetail}>
              Bekraftelse skickad till {email}
            </div>
            <button className={styles.closeButton} onClick={onBooked}>
              Stang
            </button>
          </div>
        ) : (
          <>
            <h2 className={styles.title}>Boka tid</h2>

            <div className={styles.info}>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Tjanst</span>
                <span className={styles.infoValue}>{serviceName}</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Datum</span>
                <span className={styles.infoValue}>
                  {formatDateSv(slot.date)}
                </span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>Tid</span>
                <span className={styles.infoValue}>
                  {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                </span>
              </div>
              {isPaid && (
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>Pris</span>
                  <span className={styles.infoValue}>
                    {(priceCents / 100).toFixed(0)} kr
                  </span>
                </div>
              )}
            </div>

            <form className={styles.form} onSubmit={handleSubmit}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="booking-name">
                  Namn
                </label>
                <input
                  id="booking-name"
                  className={styles.input}
                  type="text"
                  placeholder="Ditt namn"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoFocus
                  required
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="booking-email">
                  E-post
                </label>
                <input
                  id="booking-email"
                  className={styles.input}
                  type="email"
                  placeholder="din@email.se"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="booking-phone">
                  Telefon (valfritt)
                </label>
                <input
                  id="booking-phone"
                  className={styles.input}
                  type="tel"
                  placeholder="+46701234567"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>

              {error && <div className={styles.error}>{error}</div>}

              <div className={styles.actions}>
                <button
                  type="submit"
                  className={styles.bookButton}
                  disabled={submitting || !name.trim() || !email.trim()}
                >
                  {submitting
                    ? "Bokar..."
                    : isPaid
                      ? `Betala ${(priceCents / 100).toFixed(0)} kr`
                      : "Boka"}
                </button>
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={onClose}
                  disabled={submitting}
                >
                  Avbryt
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
