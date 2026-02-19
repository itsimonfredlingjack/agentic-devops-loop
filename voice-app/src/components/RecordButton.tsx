import type { PipelineStatus } from "../stores/pipelineStore";
import styles from "../styles/components/RecordButton.module.css";

interface RecordButtonProps {
  status: PipelineStatus;
  onClick: () => void;
}

const MIC_ICON = (
  <svg
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    aria-hidden="true"
  >
    <path
      d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

function getAriaLabel(status: PipelineStatus): string {
  switch (status) {
    case "recording":
      return "Stop recording";
    case "processing":
      return "Processing audio";
    default:
      return "Start recording";
  }
}

function getLabel(status: PipelineStatus): string {
  switch (status) {
    case "recording":
      return "Tap to Stop";
    case "processing":
      return "Processing...";
    default:
      return "Tap to Record";
  }
}

export function RecordButton({ status, onClick }: RecordButtonProps) {
  const isRecording = status === "recording";
  const isProcessing = status === "processing";
  const isDisabled = isProcessing || status === "clarifying";

  const buttonClass = [styles.button, isRecording && styles.recording]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.wrapper}>
      <div className={styles.buttonOuter}>
        {isRecording && (
          <>
            <div className={styles.ring} />
            <div className={`${styles.ring} ${styles.ring2}`} />
          </>
        )}
        <button
          className={buttonClass}
          onClick={onClick}
          disabled={isDisabled}
          aria-label={getAriaLabel(status)}
        >
          {isRecording ? (
            <div className={styles.waveform}>
              <div className={styles.bar} />
              <div className={styles.bar} />
              <div className={styles.bar} />
              <div className={styles.bar} />
              <div className={styles.bar} />
            </div>
          ) : isProcessing ? (
            <div className={styles.spinner} />
          ) : (
            MIC_ICON
          )}
        </button>
      </div>
      <span className={styles.label}>{getLabel(status)}</span>
    </div>
  );
}
