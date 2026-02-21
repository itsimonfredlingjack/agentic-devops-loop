"use client";

import { timestamp } from "@/lib/api";

interface LogLineProps {
  message: string;
  level?: "info" | "ok" | "warn" | "err";
}

export function LogLine({ message, level = "info" }: LogLineProps) {
  const colorMap = {
    info: "text-terminal-green",
    ok: "text-terminal-green glow-green",
    warn: "text-terminal-amber glow-amber",
    err: "text-terminal-red",
  };

  const prefixMap = {
    info: "INFO",
    ok: "  OK",
    warn: "WARN",
    err: " ERR",
  };

  return (
    <div className={`${colorMap[level]} whitespace-pre text-xs opacity-80`}>
      <span className="text-terminal-gray">[{timestamp()}]</span>{" "}
      <span className="font-bold">{prefixMap[level]}</span> {message}
    </div>
  );
}
