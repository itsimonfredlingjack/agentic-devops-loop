import { useEffect, useState, useMemo, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { GlassCard } from "../components/GlassCard";
import * as api from "../lib/api";
import type { PublicSlot, PublicTenantView, Service } from "../lib/api";
import styles from "../styles/components/PublicBookingPage.module.css";

// -----------------------------------------------------------------------
// Date helpers
// -----------------------------------------------------------------------

const DAY_NAMES = ["Mon", "Tis", "Ons", "Tor", "Fre", "Lor", "Son"];

function getMonday(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function addDays(date: Date, days: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

function toISO(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function formatDateSv(date: Date): string {
  return new Intl.DateTimeFormat("sv-SE", {
    day: "numeric",
    month: "short",
  }).format(date);
}

function formatDateLong(dateStr: string): string {
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

function isToday(date: Date): boolean {
  const now = new Date();
  return toISO(date) === toISO(now);
}

// -----------------------------------------------------------------------
// Component
// -----------------------------------------------------------------------

export function PublicBookingPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const [tenantView, setTenantView] = useState<PublicTenantView | null>(null);
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<PublicSlot | null>(null);
  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Booking form state
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [bookError, setBookError] = useState<string | null>(null);

  // Fetch public tenant view
  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    void api.getPublicTenantView(slug).then(
      (data) => {
        setTenantView(data);
        if (data.services.length > 0 && data.services[0]) {
          setSelectedService(data.services[0]);
        }
        setLoading(false);
      },
      (err: unknown) => {
        setError(
          err instanceof Error ? err.message : "Kunde inte ladda bokningssidan",
        );
        setLoading(false);
      },
    );
  }, [slug]);

  // Get slots for selected service
  const serviceSlots = useMemo(() => {
    if (!tenantView || !selectedService) return [];
    return tenantView.slots_by_service[selectedService.id] ?? [];
  }, [tenantView, selectedService]);

  // Build week days
  const weekDays = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  }, [weekStart]);

  // Group slots by date (only for current week)
  const slotsByDate = useMemo(() => {
    const map = new Map<string, PublicSlot[]>();
    for (const slot of serviceSlots) {
      const existing = map.get(slot.date);
      if (existing) {
        existing.push(slot);
      } else {
        map.set(slot.date, [slot]);
      }
    }
    return map;
  }, [serviceSlots]);

  const prevWeek = () => setWeekStart((w) => addDays(w, -7));
  const nextWeek = () => setWeekStart((w) => addDays(w, 7));

  const weekLabel = useMemo(() => {
    const start = weekDays[0];
    const end = weekDays[6];
    if (!start || !end) return "";
    const fmt = new Intl.DateTimeFormat("sv-SE", {
      day: "numeric",
      month: "long",
    });
    return `${fmt.format(start)} - ${fmt.format(end)}`;
  }, [weekDays]);

  const handleServiceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = Number(e.target.value);
    const service = tenantView?.services.find((s) => s.id === id) ?? null;
    setSelectedService(service);
    setSelectedSlot(null);
  };

  const handleBook = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!selectedSlot || !name.trim() || !email.trim()) return;

      setSubmitting(true);
      setBookError(null);
      try {
        await api.createBooking({
          slot_id: selectedSlot.id,
          customer_name: name.trim(),
          customer_email: email.trim(),
        });
        navigate(`/book/${slug}/success`);
      } catch (err) {
        setBookError(
          err instanceof Error ? err.message : "Kunde inte boka tiden",
        );
      } finally {
        setSubmitting(false);
      }
    },
    [selectedSlot, name, email, slug, navigate],
  );

  if (loading) {
    return (
      <AppShell>
        <div className={styles.container}>
          <div className={styles.loading}>Laddar...</div>
        </div>
      </AppShell>
    );
  }

  if (error || !tenantView) {
    return (
      <AppShell>
        <div className={styles.container}>
          <GlassCard>
            <div className={styles.errorMessage}>
              {error ?? "Bokningssidan kunde inte hittas"}
            </div>
          </GlassCard>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className={styles.container}>
        {/* Brand header */}
        <div className={styles.header}>
          <span className={styles.logo}>
            Book<span className={styles.logoAccent}>It</span>
          </span>
          <span className={styles.tenantName}>{tenantView.name}</span>
        </div>

        {/* Service selector */}
        <GlassCard variant="compact">
          <div className={styles.serviceSelector}>
            <label className={styles.serviceLabel} htmlFor="public-service">
              Valj tjanst
            </label>
            <select
              id="public-service"
              className={styles.serviceSelect}
              value={selectedService?.id ?? ""}
              onChange={handleServiceChange}
            >
              <option value="" disabled>
                Valj tjanst...
              </option>
              {tenantView.services.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.duration_minutes} min)
                </option>
              ))}
            </select>
          </div>
        </GlassCard>

        {/* Calendar */}
        {selectedService && (
          <GlassCard>
            <div className={styles.weekNav}>
              <button className={styles.arrowButton} onClick={prevWeek}>
                &#8249;
              </button>
              <span className={styles.weekLabel}>{weekLabel}</span>
              <button className={styles.arrowButton} onClick={nextWeek}>
                &#8250;
              </button>
            </div>

            <div className={styles.grid}>
              {weekDays.map((day, idx) => {
                const dateKey = toISO(day);
                const daySlots = slotsByDate.get(dateKey) ?? [];
                const dayName = DAY_NAMES[idx];
                return (
                  <div key={dateKey} className={styles.dayColumn}>
                    <div
                      className={`${styles.dayHeader} ${isToday(day) ? styles.todayHeader : ""}`}
                    >
                      <span className={styles.dayName}>{dayName}</span>
                      <span className={styles.dayDate}>
                        {formatDateSv(day)}
                      </span>
                    </div>
                    <div className={styles.slotList}>
                      {daySlots.length === 0 ? (
                        <div className={styles.emptyDay}>Inga tider</div>
                      ) : (
                        daySlots.map((slot) => {
                          const isFull = slot.available <= 0;
                          const isSelected = selectedSlot?.id === slot.id;
                          return (
                            <button
                              key={slot.id}
                              className={`${styles.slot} ${isFull ? styles.slotFull : styles.slotAvailable} ${isSelected ? styles.slotSelected : ""}`}
                              disabled={isFull}
                              onClick={() => {
                                if (!isFull) setSelectedSlot(slot);
                              }}
                            >
                              <div className={styles.slotTime}>
                                {slot.start_time.slice(0, 5)}
                              </div>
                              <div className={styles.slotCount}>
                                {isFull
                                  ? "Fullbokad"
                                  : `${slot.available} lediga`}
                              </div>
                            </button>
                          );
                        })
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </GlassCard>
        )}

        {/* Booking form */}
        {selectedSlot && (
          <GlassCard>
            <h3 className={styles.formTitle}>Boka tid</h3>
            <div className={styles.formInfo}>
              <span>{selectedService?.name}</span>
              <span>{formatDateLong(selectedSlot.date)}</span>
              <span>
                {selectedSlot.start_time.slice(0, 5)} -{" "}
                {selectedSlot.end_time.slice(0, 5)}
              </span>
            </div>

            <form className={styles.form} onSubmit={handleBook}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="public-name">
                  Namn
                </label>
                <input
                  id="public-name"
                  className={styles.input}
                  type="text"
                  placeholder="Ditt namn"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="public-email">
                  E-post
                </label>
                <input
                  id="public-email"
                  className={styles.input}
                  type="email"
                  placeholder="din@email.se"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              {bookError && <div className={styles.error}>{bookError}</div>}

              <button
                type="submit"
                className={styles.bookButton}
                disabled={submitting || !name.trim() || !email.trim()}
              >
                {submitting ? "Bokar..." : "Boka"}
              </button>
            </form>
          </GlassCard>
        )}
      </div>
    </AppShell>
  );
}
