import { useBookingStore } from "../stores/bookingStore";
import styles from "../styles/components/Header.module.css";

type View = "calendar" | "my-bookings" | "admin";

interface NavItem {
  key: View;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { key: "calendar", label: "Kalender" },
  { key: "my-bookings", label: "Mina Bokningar" },
  { key: "admin", label: "Administration" },
];

export function Header() {
  const view = useBookingStore((s) => s.view);
  const setView = useBookingStore((s) => s.setView);
  const currentTenant = useBookingStore((s) => s.currentTenant);

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.logo}>
          Book<span className={styles.logoAccent}>It</span>
        </span>
        <span className={styles.tenant}>{currentTenant}</span>
      </div>

      <nav className={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.key}
            className={`${styles.navButton} ${
              view === item.key ? styles.navButtonActive : ""
            }`}
            onClick={() => setView(item.key)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
