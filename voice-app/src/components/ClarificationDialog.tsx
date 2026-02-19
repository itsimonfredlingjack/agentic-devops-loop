import { useEffect, useRef, useState } from "react";
import { GlassCard } from "./GlassCard";
import styles from "../styles/components/ClarificationDialog.module.css";

interface ClarificationDialogProps {
  questions: string[];
  partialSummary: string;
  round: number;
  disabled: boolean;
  onSubmit: (answer: string) => void;
}

export function ClarificationDialog({
  questions,
  partialSummary,
  round,
  disabled,
  onSubmit,
}: ClarificationDialogProps) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [questions]);

  const handleSubmit = () => {
    if (!input.trim() || disabled) return;
    onSubmit(input);
    setInput("");
  };

  return (
    <GlassCard className={styles.card}>
      <div className={styles.header}>
        <span className={styles.title}>Clarification Needed</span>
        <span className={styles.round}>Round {round}</span>
      </div>
      <div className={styles.summary}>{partialSummary}</div>
      <ul className={styles.questions}>
        {questions.map((q, i) => (
          <li key={i} className={styles.question}>
            {q}
          </li>
        ))}
      </ul>
      <div className={styles.inputRow}>
        <input
          ref={inputRef}
          className={styles.input}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Type your answer..."
          disabled={disabled}
        />
        <button
          className={styles.submitBtn}
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
        >
          Send
        </button>
      </div>
    </GlassCard>
  );
}
