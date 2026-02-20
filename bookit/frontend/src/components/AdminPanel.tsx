import { useEffect, useState, useCallback } from "react";
import { useBookingStore } from "../stores/bookingStore";
import styles from "../styles/components/AdminPanel.module.css";

function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function AdminPanel() {
  const services = useBookingStore((s) => s.services);
  const fetchServices = useBookingStore((s) => s.fetchServices);
  const createServiceAction = useBookingStore((s) => s.createService);
  const generateSlotsAction = useBookingStore((s) => s.generateSlots);
  const loading = useBookingStore((s) => s.loading);

  // Create service form
  const [serviceName, setServiceName] = useState("");
  const [duration, setDuration] = useState("60");
  const [capacity, setCapacity] = useState("1");
  const [priceSek, setPriceSek] = useState("0");
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState<string | null>(null);

  // Generate slots state (per service)
  const [slotDates, setSlotDates] = useState<Record<number, string>>({});
  const [genMessages, setGenMessages] = useState<
    Record<number, { type: "success" | "error"; text: string }>
  >({});

  useEffect(() => {
    void fetchServices();
  }, [fetchServices]);

  const handleCreateService = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setCreateError(null);
      setCreateSuccess(null);

      const durationNum = parseInt(duration, 10);
      const capacityNum = parseInt(capacity, 10);

      if (!serviceName.trim()) {
        setCreateError("Ange ett namn for tjansten");
        return;
      }
      if (isNaN(durationNum) || durationNum < 1) {
        setCreateError("Ange en giltig langd i minuter");
        return;
      }
      if (isNaN(capacityNum) || capacityNum < 1) {
        setCreateError("Ange en giltig kapacitet");
        return;
      }

      const priceNum = parseInt(priceSek, 10);
      if (isNaN(priceNum) || priceNum < 0) {
        setCreateError("Ange ett giltigt pris");
        return;
      }

      try {
        await createServiceAction({
          name: serviceName.trim(),
          duration_minutes: durationNum,
          capacity: capacityNum,
          price_cents: priceNum * 100,
        });
        setCreateSuccess(`Tjanst "${serviceName.trim()}" skapad!`);
        setServiceName("");
        setDuration("60");
        setCapacity("1");
        setPriceSek("0");
      } catch (err) {
        setCreateError(
          err instanceof Error ? err.message : "Kunde inte skapa tjanst",
        );
      }
    },
    [serviceName, duration, capacity, createServiceAction],
  );

  const handleGenerateSlots = useCallback(
    async (serviceId: number) => {
      const date = slotDates[serviceId] ?? todayISO();
      setGenMessages((prev) => {
        const next = { ...prev };
        delete next[serviceId];
        return next;
      });

      try {
        const generated = await generateSlotsAction(serviceId, {
          date,
          start_hour: 8,
          end_hour: 17,
        });
        setGenMessages((prev) => ({
          ...prev,
          [serviceId]: {
            type: "success" as const,
            text: `${generated.length} tider skapade for ${date}`,
          },
        }));
      } catch (err) {
        setGenMessages((prev) => ({
          ...prev,
          [serviceId]: {
            type: "error" as const,
            text:
              err instanceof Error ? err.message : "Kunde inte generera tider",
          },
        }));
      }
    },
    [slotDates, generateSlotsAction],
  );

  const handleSlotDateChange = useCallback(
    (serviceId: number, date: string) => {
      setSlotDates((prev) => ({ ...prev, [serviceId]: date }));
    },
    [],
  );

  return (
    <div className={styles.container}>
      {/* Create Service */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <span className={styles.sectionIcon}>&#9881;</span>
          Skapa ny tjanst
        </h2>

        <form className={styles.createForm} onSubmit={handleCreateService}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="admin-service-name">
              Namn
            </label>
            <input
              id="admin-service-name"
              className={styles.input}
              type="text"
              placeholder="T.ex. Klippning"
              value={serviceName}
              onChange={(e) => setServiceName(e.target.value)}
              required
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="admin-duration">
              Langd (min)
            </label>
            <input
              id="admin-duration"
              className={styles.input}
              type="number"
              min="5"
              max="480"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              required
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="admin-capacity">
              Kapacitet
            </label>
            <input
              id="admin-capacity"
              className={styles.input}
              type="number"
              min="1"
              max="100"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              required
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="admin-price">
              Pris (kr)
            </label>
            <input
              id="admin-price"
              className={styles.input}
              type="number"
              min="0"
              value={priceSek}
              onChange={(e) => setPriceSek(e.target.value)}
            />
          </div>

          <button
            type="submit"
            className={styles.createButton}
            disabled={loading}
          >
            {loading ? "Skapar..." : "Skapa tjanst"}
          </button>
        </form>

        {createError && <div className={styles.error}>{createError}</div>}
        {createSuccess && <div className={styles.success}>{createSuccess}</div>}
      </div>

      {/* Service List */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <span className={styles.sectionIcon}>&#128203;</span>
          Tjanster
        </h2>

        {services.length === 0 ? (
          <div className={styles.empty}>
            Inga tjanster skapade annu. Borja med att skapa en ovan.
          </div>
        ) : (
          <div className={styles.serviceList}>
            {services.map((service) => {
              const msg = genMessages[service.id];
              return (
                <div key={service.id}>
                  <div className={styles.serviceCard}>
                    <div className={styles.serviceInfo}>
                      <span className={styles.serviceName}>{service.name}</span>
                      <div className={styles.serviceMeta}>
                        <span>{service.duration_minutes} min</span>
                        <span>Kapacitet: {service.capacity}</span>
                        <span>
                          {service.price_cents > 0
                            ? `${(service.price_cents / 100).toFixed(0)} kr`
                            : "Gratis"}
                        </span>
                      </div>
                    </div>

                    <div className={styles.serviceActions}>
                      <input
                        className={styles.dateInput}
                        type="date"
                        value={slotDates[service.id] ?? todayISO()}
                        onChange={(e) =>
                          handleSlotDateChange(service.id, e.target.value)
                        }
                      />
                      <button
                        className={styles.generateButton}
                        onClick={() => void handleGenerateSlots(service.id)}
                        disabled={loading}
                      >
                        Generera tider
                      </button>
                    </div>
                  </div>

                  {msg && (
                    <div
                      className={
                        msg.type === "success" ? styles.success : styles.error
                      }
                    >
                      {msg.text}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
