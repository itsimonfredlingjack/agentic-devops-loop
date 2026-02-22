import { useEffect } from "react";
import { Outlet, useParams, Link, useLocation } from "react-router-dom";
import { Header } from "../components/Header";
import { useEventStore } from "../stores/eventStore";

export function AdminLayout() {
  const { slug } = useParams<{ slug: string }>();
  const setTenant = useEventStore((s) => s.setTenant);
  const location = useLocation();

  useEffect(() => {
    if (slug) setTenant(slug);
  }, [slug, setTenant]);

  const basePath = `/admin/${slug}`;

  const tabs = [{ label: "Events", path: basePath }];

  return (
    <div>
      <Header />

      {/* Admin tabs */}
      <nav
        style={{
          borderBottom: "1px solid var(--color-surface-border)",
          maxWidth: 1200,
          margin: "0 auto",
          padding: "0 24px",
          display: "flex",
          gap: 0,
        }}
      >
        {tabs.map((tab) => {
          const active = location.pathname === tab.path;
          return (
            <Link
              key={tab.path}
              to={tab.path}
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                textTransform: "uppercase",
                letterSpacing: "0.15em",
                padding: "16px 24px",
                color: active
                  ? "var(--color-accent)"
                  : "var(--color-text-secondary)",
                borderBottom: active
                  ? "2px solid var(--color-accent)"
                  : "2px solid transparent",
                transition: "all 150ms ease",
              }}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>

      {/* Page content */}
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "32px 24px",
        }}
      >
        <Outlet />
      </div>
    </div>
  );
}
