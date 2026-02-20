import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { GlassCard } from "../components/GlassCard";
import { getCheckoutStatus } from "../lib/api";
import styles from "../styles/components/PublicBookingPage.module.css";

export function BookingSuccess() {
  const { slug } = useParams<{ slug: string }>();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");

  const [paymentStatus, setPaymentStatus] = useState<string | null>(null);
  const [polling, setPolling] = useState(!!sessionId);

  useEffect(() => {
    if (!sessionId) return;

    let cancelled = false;
    const poll = async () => {
      for (let i = 0; i < 10; i++) {
        if (cancelled) return;
        try {
          const status = await getCheckoutStatus(sessionId);
          if (status.payment_status === "paid") {
            setPaymentStatus("paid");
            setPolling(false);
            return;
          }
        } catch {
          // ignore polling errors
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
      setPaymentStatus("timeout");
      setPolling(false);
    };
    void poll();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  return (
    <AppShell>
      <div className={styles.container}>
        <div className={styles.header}>
          <span className={styles.logo}>
            Book<span className={styles.logoAccent}>It</span>
          </span>
        </div>

        <GlassCard>
          <div className={styles.successSection}>
            {polling ? (
              <>
                <div className={styles.successIcon}>&#8987;</div>
                <h2 className={styles.successTitle}>Bekraftar betalning...</h2>
                <p className={styles.successText}>
                  Vanligen bekraftas din betalning.
                </p>
              </>
            ) : paymentStatus === "timeout" ? (
              <>
                <div className={styles.successIcon}>&#9888;</div>
                <h2 className={styles.successTitle}>
                  Betalning under behandling
                </h2>
                <p className={styles.successText}>
                  Din betalning behandlas fortfarande. Du far en bekraftelse via
                  e-post.
                </p>
              </>
            ) : (
              <>
                <div className={styles.successIcon}>&#10003;</div>
                <h2 className={styles.successTitle}>Bokningen ar bekraftad!</h2>
                <p className={styles.successText}>
                  Du kommer att fa en bekraftelse via e-post.
                </p>
              </>
            )}
            <Link to={`/book/${slug}`} className={styles.backLink}>
              Boka en ny tid
            </Link>
          </div>
        </GlassCard>
      </div>
    </AppShell>
  );
}
