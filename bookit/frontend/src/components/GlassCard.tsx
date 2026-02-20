import type { ReactNode } from "react";
import styles from "../styles/components/GlassCard.module.css";

interface GlassCardProps {
  children: ReactNode;
  variant?: "default" | "compact" | "noPadding";
  className?: string;
}

export function GlassCard({
  children,
  variant = "default",
  className,
}: GlassCardProps) {
  const classes = [
    styles.card,
    variant === "compact" ? styles.compact : undefined,
    variant === "noPadding" ? styles.noPadding : undefined,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return <div className={classes}>{children}</div>;
}
