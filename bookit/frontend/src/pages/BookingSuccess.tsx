import { Link, useParams } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { GlassCard } from "../components/GlassCard";
import styles from "../styles/components/PublicBookingPage.module.css";

export function BookingSuccess() {
  const { slug } = useParams<{ slug: string }>();

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
            <div className={styles.successIcon}>&#10003;</div>
            <h2 className={styles.successTitle}>Bokningen ar bekraftad!</h2>
            <p className={styles.successText}>
              Du kommer att fa en bekraftelse via e-post.
            </p>
            <Link to={`/book/${slug}`} className={styles.backLink}>
              Boka en ny tid
            </Link>
          </div>
        </GlassCard>
      </div>
    </AppShell>
  );
}
