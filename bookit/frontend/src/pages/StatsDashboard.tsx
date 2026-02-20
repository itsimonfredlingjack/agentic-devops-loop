import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import styles from "../styles/components/StatsDashboard.module.css";

interface ServiceStats {
  service_id: number;
  service_name: string;
  booking_count: number;
  revenue_cents: number;
}

interface StatsResponse {
  total_bookings: number;
  confirmed_bookings: number;
  cancelled_bookings: number;
  total_revenue_cents: number;
  services: ServiceStats[];
  period: string;
}

const API_BASE = "/api";

export function StatsDashboard() {
  const { slug } = useParams<{ slug: string }>();
  const [period, setPeriod] = useState<"week" | "month" | "year">("month");
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/tenants/${slug}/stats?period=${period}`,
      );
      if (!res.ok) throw new Error("Kunde inte hamta statistik");
      const data = (await res.json()) as StatsResponse;
      setStats(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fel");
    } finally {
      setLoading(false);
    }
  }, [slug, period]);

  useEffect(() => {
    void fetchStats();
  }, [fetchStats]);

  const maxBookings = stats
    ? Math.max(...stats.services.map((s) => s.booking_count), 1)
    : 1;

  const periodLabel: Record<string, string> = {
    week: "Senaste veckan",
    month: "Senaste manaden",
    year: "Senaste aret",
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Statistik</h2>
        <div className={styles.periodPicker}>
          {(["week", "month", "year"] as const).map((p) => (
            <button
              key={p}
              className={`${styles.periodButton} ${period === p ? styles.periodActive : ""}`}
              onClick={() => setPeriod(p)}
            >
              {periodLabel[p]}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className={styles.loading}>Laddar...</div>}
      {error && <div className={styles.error}>{error}</div>}

      {stats && !loading && (
        <>
          {/* KPI Cards */}
          <div className={styles.kpiGrid}>
            <div className={styles.kpiCard}>
              <div className={styles.kpiValue}>{stats.total_bookings}</div>
              <div className={styles.kpiLabel}>Totalt bokningar</div>
            </div>
            <div className={styles.kpiCard}>
              <div className={styles.kpiValue}>{stats.confirmed_bookings}</div>
              <div className={styles.kpiLabel}>Bekraftade</div>
            </div>
            <div className={styles.kpiCard}>
              <div className={styles.kpiValue}>{stats.cancelled_bookings}</div>
              <div className={styles.kpiLabel}>Avbokade</div>
            </div>
            <div className={styles.kpiCard}>
              <div className={styles.kpiValue}>
                {(stats.total_revenue_cents / 100).toFixed(0)} kr
              </div>
              <div className={styles.kpiLabel}>Intakter</div>
            </div>
          </div>

          {/* Service Breakdown */}
          {stats.services.length > 0 && (
            <div className={styles.chartSection}>
              <h3 className={styles.chartTitle}>Tjänstefördelning</h3>
              <div className={styles.barChart}>
                {stats.services.map((svc) => (
                  <div key={svc.service_id} className={styles.barRow}>
                    <span className={styles.barLabel}>{svc.service_name}</span>
                    <div className={styles.barTrack}>
                      <div
                        className={styles.barFill}
                        style={{
                          width: `${(svc.booking_count / maxBookings) * 100}%`,
                        }}
                      />
                    </div>
                    <span className={styles.barValue}>{svc.booking_count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {stats.services.length === 0 && (
            <div className={styles.empty}>
              Inga bokningar under {periodLabel[stats.period]?.toLowerCase()}.
            </div>
          )}
        </>
      )}
    </div>
  );
}
