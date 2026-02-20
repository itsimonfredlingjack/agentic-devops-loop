import type { ReactNode } from "react";
import styles from "../styles/components/AppShell.module.css";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className={styles.shell}>
      {/* Animated background blobs */}
      <div className={styles.blobContainer}>
        <div className={`${styles.blob} ${styles.blobCoral}`} />
        <div className={`${styles.blob} ${styles.blobBlue}`} />
        <div className={`${styles.blob} ${styles.blobGreen}`} />
      </div>

      {/* Main content */}
      <div className={styles.content}>{children}</div>
    </div>
  );
}
