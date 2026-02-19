import { useEffect, useMemo, useState, useCallback } from "react";
import { useBookingStore } from "../stores/bookingStore";
import { BookingForm } from "./BookingForm";
import type { Slot } from "../lib/api";
import styles from "../styles/components/Calendar.module.css";

// -----------------------------------------------------------------------
// Date helpers
// -----------------------------------------------------------------------

const DAY_NAMES = ["Mon", "Tis", "Ons", "Tor", "Fre", "Lor", "Son"];

function getMonday(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay(); // 0=Sun
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

function isToday(date: Date): boolean {
  const now = new Date();
  return toISO(date) === toISO(now);
}

// -----------------------------------------------------------------------
// Component
// -----------------------------------------------------------------------

export function Calendar() {
  const services = useBookingStore((s) => s.services);
  const selectedService = useBookingStore((s) => s.selectedService);
  const setSelectedService = useBookingStore((s) => s.setSelectedService);
  const slots = useBookingStore((s) => s.slots);
  const fetchSlots = useBookingStore((s) => s.fetchSlots);
  const fetchServices = useBookingStore((s) => s.fetchServices);
  const setSelectedDate = useBookingStore((s) => s.setSelectedDate);
  const loading = useBookingStore((s) => s.loading);

  const [weekStart, setWeekStart] = useState(() => getMonday(new Date()));
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);

  // Build the 7 days of the week
  const weekDays = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  }, [weekStart]);

  // Load services on mount
  useEffect(() => {
    void fetchServices();
  }, [fetchServices]);

  // Load slots when service or week changes
  const loadAllSlots = useCallback(async () => {
    if (selectedService === null) return;
    // We fetch slots for the first day of the week; the backend returns the
    // full week when given a date.  If the backend only returns a single day,
    // we would need to fetch 7 times.  For simplicity we set selectedDate to
    // the Monday and fetch once.
    setSelectedDate(toISO(weekStart));
    await fetchSlots(selectedService);
  }, [selectedService, weekStart, setSelectedDate, fetchSlots]);

  useEffect(() => {
    void loadAllSlots();
  }, [loadAllSlots]);

  // Group slots by date
  const slotsByDate = useMemo(() => {
    const map = new Map<string, Slot[]>();
    for (const slot of slots) {
      const dateKey = slot.date;
      const existing = map.get(dateKey);
      if (existing) {
        existing.push(slot);
      } else {
        map.set(dateKey, [slot]);
      }
    }
    return map;
  }, [slots]);

  // Week navigation
  const prevWeek = () => setWeekStart((w) => addDays(w, -7));
  const nextWeek = () => setWeekStart((w) => addDays(w, 7));

  // Service change
  const handleServiceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = Number(e.target.value);
    setSelectedService(val || null);
  };

  // Week label
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

  return (
    <div className={styles.container}>
      {/* Toolbar */}
      <div className={styles.toolbar}>
        <div className={styles.weekNav}>
          <button className={styles.arrowButton} onClick={prevWeek}>
            &#8249;
          </button>
          <span className={styles.weekLabel}>{weekLabel}</span>
          <button className={styles.arrowButton} onClick={nextWeek}>
            &#8250;
          </button>
        </div>

        <select
          className={styles.serviceSelect}
          value={selectedService ?? ""}
          onChange={handleServiceChange}
        >
          <option value="" disabled>
            Valj tjanst...
          </option>
          {services.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.duration_minutes} min)
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {selectedService === null ? (
        <div className={styles.noService}>
          <span className={styles.noServiceIcon}>&#128197;</span>
          <span>Valj en tjanst for att se tillgangliga tider</span>
        </div>
      ) : loading ? (
        <div className={styles.loading}>Laddar tider...</div>
      ) : (
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
                  <span className={styles.dayDate}>{formatDateSv(day)}</span>
                </div>
                <div className={styles.slotList}>
                  {daySlots.length === 0 ? (
                    <div className={styles.emptyDay}>Inga tider</div>
                  ) : (
                    daySlots.map((slot) => {
                      const available = slot.capacity - slot.booked_count;
                      const isFull = available <= 0;
                      return (
                        <button
                          key={slot.id}
                          className={`${styles.slot} ${isFull ? styles.slotFull : styles.slotAvailable}`}
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
                              : `${available} av ${slot.capacity} lediga`}
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
      )}

      {/* Booking modal */}
      {selectedSlot && (
        <BookingForm
          slot={selectedSlot}
          serviceName={
            services.find((s) => s.id === selectedSlot.service_id)?.name ?? ""
          }
          onClose={() => setSelectedSlot(null)}
          onBooked={() => {
            setSelectedSlot(null);
            void loadAllSlots();
          }}
        />
      )}
    </div>
  );
}
