import { GlassCard } from "./GlassCard";
import styles from "../styles/components/TranscriptionCard.module.css";

interface TranscriptionCardProps {
  text: string;
}

export function TranscriptionCard({ text }: TranscriptionCardProps) {
  return (
    <GlassCard>
      <div className={styles.label}>Transcription</div>
      {text ? (
        <div className={styles.text}>{text}</div>
      ) : (
        <div className={`${styles.text} ${styles.placeholder}`}>
          Record audio to see transcription...
        </div>
      )}
    </GlassCard>
  );
}
