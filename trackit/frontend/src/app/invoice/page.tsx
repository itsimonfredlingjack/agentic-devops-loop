"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  getInvoice,
  finalizeInvoice,
  formatSEK,
  formatDuration,
  formatRate,
  type InvoiceData,
} from "@/lib/api";
import { AsciiBox, AsciiDivider, AsciiRow } from "@/components/ascii-box";
import { LogLine } from "@/components/log-line";

function InvoiceContent() {
  const params = useSearchParams();
  const router = useRouter();
  const slug = params.get("slug") ?? "";
  const year = Number(params.get("year")) || new Date().getFullYear();
  const month = Number(params.get("month")) || new Date().getMonth() + 1;

  const [invoice, setInvoice] = useState<InvoiceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [finalizing, setFinalizing] = useState(false);
  const [finalized, setFinalized] = useState(false);
  const [logs, setLogs] = useState<
    { msg: string; level: "info" | "ok" | "warn" | "err" }[]
  >([]);

  const addLog = (
    msg: string,
    level: "info" | "ok" | "warn" | "err" = "info",
  ) => {
    setLogs((l) => [...l.slice(-10), { msg, level }]);
  };

  useEffect(() => {
    if (!slug) return;
    addLog(
      `Fetching invoice for ${slug} ${year}-${String(month).padStart(2, "0")}...`,
    );
    getInvoice(slug, year, month)
      .then((inv) => {
        setInvoice(inv);
        addLog(`Invoice loaded: ${inv.invoice_number}`, "ok");
      })
      .catch((err) => addLog(`ERR: ${err.message}`, "err"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, year, month]);

  const handleFinalize = async () => {
    if (!slug || finalized) return;
    setFinalizing(true);
    addLog("Finalizing invoice...", "warn");
    try {
      const result = await finalizeInvoice(slug, year, month);
      addLog(`FINALIZED — ${result.entries_locked} entries locked`, "ok");
      setFinalized(true);
      // Refresh invoice
      const inv = await getInvoice(slug, year, month);
      setInvoice(inv);
    } catch (err) {
      addLog(`ERR: ${err instanceof Error ? err.message : "unknown"}`, "err");
    } finally {
      setFinalizing(false);
    }
  };

  if (!slug) {
    return (
      <div className="text-terminal-red">ERR: No tenant slug provided</div>
    );
  }

  if (loading) {
    return (
      <div className="text-terminal-green glow-green animate-pulse">
        Loading invoice data...
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-6">
      <button
        onClick={() => router.back()}
        className="text-terminal-gray hover:text-terminal-green transition-colors text-xs"
      >
        {"<"} BACK TO DASHBOARD
      </button>

      <AsciiBox title="INVOICE" color="amber">
        <AsciiRow>
          <span className="text-terminal-white glow-white font-bold text-base">
            {invoice?.invoice_number ?? "---"}
          </span>
        </AsciiRow>
        <AsciiRow>
          <span className="text-terminal-gray">
            Tenant: {slug} // Period: {year}-{String(month).padStart(2, "0")}
          </span>
        </AsciiRow>
        <AsciiRow>
          <span className="text-terminal-gray">
            Generated: {new Date().toISOString()}
          </span>
        </AsciiRow>

        <AsciiDivider label="LINE ITEMS" />

        <AsciiRow>
          <span className="text-terminal-white font-bold">
            {"PROJECT".padEnd(18)}
            {"HOURS".padStart(8)}
            {"RATE".padStart(10)}
            {"AMOUNT".padStart(14)}
          </span>
        </AsciiRow>
        <AsciiDivider />

        {!invoice || invoice.line_items.length === 0 ? (
          <AsciiRow>
            <span className="text-terminal-gray">
              No billable entries for this period
            </span>
          </AsciiRow>
        ) : (
          <>
            {invoice.line_items.map((item) => (
              <AsciiRow key={item.project_id}>
                <span>
                  {item.project_name.slice(0, 18).padEnd(18)}
                  <span className="text-terminal-green">
                    {formatDuration(item.total_minutes).padStart(8)}
                  </span>
                  <span className="text-terminal-gray">
                    {formatRate(item.hourly_rate_cents).padStart(10)}
                  </span>
                  <span className="text-terminal-amber glow-amber">
                    {formatSEK(item.amount_cents).padStart(14)}
                  </span>
                </span>
              </AsciiRow>
            ))}
          </>
        )}

        <AsciiDivider label="SUMMARY" />

        <AsciiRow>
          <span>
            {"Subtotal (exkl. moms)".padEnd(30)}
            <span className="text-terminal-amber">
              {formatSEK(invoice?.subtotal_cents ?? 0).padStart(14)}
            </span>
          </span>
        </AsciiRow>
        <AsciiRow>
          <span>
            {"Moms 25%".padEnd(30)}
            <span className="text-terminal-amber">
              {formatSEK(invoice?.tax_amount_cents ?? 0).padStart(14)}
            </span>
          </span>
        </AsciiRow>
        <AsciiDivider />
        <AsciiRow>
          <span className="text-terminal-white font-bold glow-white text-base">
            {"ATT BETALA".padEnd(30)}
            {formatSEK(invoice?.total_cents ?? 0).padStart(14)}
          </span>
        </AsciiRow>

        <AsciiDivider />

        <AsciiRow>
          {finalized ? (
            <span className="text-terminal-green glow-green font-bold">
              FINALIZED — All entries locked
            </span>
          ) : (
            <button
              onClick={handleFinalize}
              disabled={
                finalizing || !invoice || invoice.line_items.length === 0
              }
              className="btn-terminal-amber text-xs disabled:opacity-30"
            >
              {finalizing ? "FINALIZING..." : "FINALIZE INVOICE"}
            </button>
          )}
        </AsciiRow>
      </AsciiBox>

      {/* Log */}
      <div className="space-y-0 text-xs">
        {logs.map((l, i) => (
          <LogLine key={i} message={l.msg} level={l.level} />
        ))}
      </div>
    </div>
  );
}

export default function InvoicePage() {
  return (
    <Suspense
      fallback={
        <div className="text-terminal-green glow-green animate-pulse">
          Loading...
        </div>
      }
    >
      <InvoiceContent />
    </Suspense>
  );
}
