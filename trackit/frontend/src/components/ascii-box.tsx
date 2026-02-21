"use client";

interface AsciiBoxProps {
  title?: string;
  children: React.ReactNode;
  width?: string;
  color?: "green" | "amber" | "white";
}

export function AsciiBox({
  title,
  children,
  width = "w-full",
  color = "green",
}: AsciiBoxProps) {
  const colorClass =
    color === "amber"
      ? "text-terminal-amber glow-amber"
      : color === "white"
        ? "text-terminal-white glow-white"
        : "text-terminal-green glow-green";

  return (
    <div className={`${width} ${colorClass}`}>
      <div className="whitespace-pre">
        {title ? (
          <>
            <span>
              {"┌─ "}
              <span className="font-bold">{title}</span>{" "}
              {"─".repeat(Math.max(0, 40 - title.length))}
              {"┐"}
            </span>
          </>
        ) : (
          <span>{"┌" + "─".repeat(44) + "┐"}</span>
        )}
      </div>
      <div className="pl-0">{children}</div>
      <div className="whitespace-pre">
        <span>{"└" + "─".repeat(44) + "┘"}</span>
      </div>
    </div>
  );
}

export function AsciiDivider({ label }: { label?: string }) {
  if (label) {
    return (
      <div className="text-terminal-gray whitespace-pre my-1">
        {"├─ "}
        {label} {"─".repeat(Math.max(0, 40 - label.length))}
        {"┤"}
      </div>
    );
  }
  return (
    <div className="text-terminal-gray whitespace-pre my-1">
      {"├" + "─".repeat(44) + "┤"}
    </div>
  );
}

export function AsciiRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="whitespace-pre px-0">
      <span className="text-terminal-gray">│</span>
      <span className="px-1">{children}</span>
    </div>
  );
}
