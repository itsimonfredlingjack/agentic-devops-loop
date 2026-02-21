import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TRACKIT TERMINAL v0.1.0",
  description: "Time tracking and invoicing terminal",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sv">
      <body className="font-mono bg-terminal-black text-terminal-green min-h-screen p-4 md:p-8">
        {/* Boot header */}
        <header className="mb-6">
          <div className="text-terminal-gray text-xs mb-1">
            TRACKIT TERMINAL v0.1.0 // {new Date().toISOString().split("T")[0]}{" "}
            // PID {Math.floor(Math.random() * 9000 + 1000)}
          </div>
          <div className="text-terminal-green glow-green text-lg font-bold tracking-wider">
            ████████╗██████╗ █████╗ ██████╗██╗ ██╗██╗████████╗
          </div>
          <div className="text-terminal-green glow-green text-lg font-bold tracking-wider">
            ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║╚══██╔══╝
          </div>
          <div className="text-terminal-green glow-green text-lg font-bold tracking-wider">
            {"   "}██║ ██████╔╝███████║██║ █████╔╝ ██║ ██║
          </div>
          <div className="text-terminal-green glow-green text-lg font-bold tracking-wider">
            {"   "}██║ ██╔══██╗██╔══██║██║ ██╔═██╗ ██║ ██║
          </div>
          <div className="text-terminal-green glow-green text-lg font-bold tracking-wider">
            {"   "}██║ ██║ ██║██║ ██║╚██████╗██║ ██╗██║ ██║
          </div>
          <div className="text-terminal-green glow-green text-lg font-bold tracking-wider">
            {"   "}╚═╝ ╚═╝ ╚═╝╚═╝ ╚═╝ ╚═════╝╚═╝ ╚═╝╚═╝ ╚═╝
          </div>
          <div className="text-terminal-gray text-xs mt-1">
            Time tracking &amp; invoicing for Swedish consultancies // 25% moms
          </div>
          <div className="text-terminal-gray text-xs">
            ═══════════════════════════════════════════════════════════════
          </div>
        </header>

        <main>{children}</main>
      </body>
    </html>
  );
}
