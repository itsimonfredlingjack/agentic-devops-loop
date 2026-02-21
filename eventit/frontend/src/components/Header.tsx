import { Link, useLocation } from "react-router-dom";

export function Header() {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith("/admin");

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        borderBottom: "1px solid var(--color-surface-border)",
        background: "rgba(10, 10, 10, 0.85)",
        backdropFilter: "blur(12px)",
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "0 24px",
          height: 64,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Link to="/" style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span
            style={{
              width: 32,
              height: 32,
              background: "var(--color-accent)",
              color: "var(--color-surface)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: "var(--font-mono)",
              fontWeight: 700,
              fontSize: 16,
            }}
          >
            E
          </span>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 14,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--color-text-primary)",
            }}
          >
            Event<span style={{ color: "var(--color-accent)" }}>It</span>
          </span>
        </Link>

        <nav style={{ display: "flex", gap: 24, alignItems: "center" }}>
          {isAdmin ? (
            <>
              <NavLink to={location.pathname.replace(/\/events\/.*/, "")}>
                Events
              </NavLink>
              <NavLink to="/">Public</NavLink>
            </>
          ) : (
            <>
              <NavLink to="/">Events</NavLink>
              <NavLink to="/admin/demo-events">Admin</NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        textTransform: "uppercase",
        letterSpacing: "0.15em",
        color: "var(--color-text-secondary)",
        transition: "color 150ms ease",
      }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.color = "var(--color-text-primary)")
      }
      onMouseLeave={(e) =>
        (e.currentTarget.style.color = "var(--color-text-secondary)")
      }
    >
      {children}
    </Link>
  );
}
