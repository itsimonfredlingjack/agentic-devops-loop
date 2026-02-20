import { Link, useLocation, useParams } from "react-router-dom";
import { useBookingStore } from "../stores/bookingStore";
import styles from "../styles/components/Header.module.css";

interface NavItem {
  to: string;
  label: string;
  end?: boolean; // match exact path
}

export function Header() {
  const { slug } = useParams<{ slug: string }>();
  const location = useLocation();
  const currentTenant = useBookingStore((s) => s.currentTenant);

  const navItems: NavItem[] = [
    { to: `/admin/${slug}`, label: "Kalender", end: true },
    { to: `/admin/${slug}/bookings`, label: "Mina Bokningar" },
    { to: `/admin/${slug}/manage`, label: "Administration" },
  ];

  function isActive(item: NavItem): boolean {
    if (item.end) {
      return location.pathname === item.to;
    }
    return location.pathname.startsWith(item.to);
  }

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <span className={styles.logo}>
          Book<span className={styles.logoAccent}>It</span>
        </span>
        <span className={styles.tenant}>{currentTenant}</span>
      </div>

      <nav className={styles.nav}>
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={`${styles.navButton} ${
              isActive(item) ? styles.navButtonActive : ""
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
