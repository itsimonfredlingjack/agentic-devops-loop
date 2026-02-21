"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  getTenant,
  createTenant,
  listProjects,
  createProject,
  logTime,
  getInvoice,
  formatSEK,
  formatDuration,
  formatRate,
  type Tenant,
  type Project,
  type InvoiceData,
} from "@/lib/api";
import { AsciiBox, AsciiDivider, AsciiRow } from "@/components/ascii-box";
import { LogLine } from "@/components/log-line";

export default function Dashboard() {
  const [slug, setSlug] = useState("");
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [invoice, setInvoice] = useState<InvoiceData | null>(null);
  const [logs, setLogs] = useState<
    { msg: string; level: "info" | "ok" | "warn" | "err" }[]
  >([]);

  // New project form
  const [newProjName, setNewProjName] = useState("");
  const [newProjRate, setNewProjRate] = useState("");

  // Time log form
  const [logProjectId, setLogProjectId] = useState<number | null>(null);
  const [logDate, setLogDate] = useState(
    new Date().toISOString().split("T")[0],
  );
  const [logMinutes, setLogMinutes] = useState("60");
  const [logBillable, setLogBillable] = useState(true);

  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  const addLog = useCallback(
    (msg: string, level: "info" | "ok" | "warn" | "err" = "info") => {
      setLogs((l) => [...l.slice(-15), { msg, level }]);
    },
    [],
  );

  const loadTenant = useCallback(
    async (s: string) => {
      try {
        const t = await getTenant(s);
        setTenant(t);
        addLog(`Connected to tenant: ${t.name} (${t.slug})`, "ok");
        const p = await listProjects(s);
        setProjects(p);
        addLog(`Loaded ${p.length} project(s)`, "info");
        try {
          const inv = await getInvoice(s, currentYear, currentMonth);
          setInvoice(inv);
          addLog(
            `Invoice preview: ${inv.invoice_number} — ${formatSEK(inv.total_cents)}`,
            "info",
          );
        } catch {
          setInvoice(null);
        }
      } catch {
        addLog(`Tenant "${s}" not found`, "err");
      }
    },
    [addLog, currentYear, currentMonth],
  );

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!slug.trim()) return;
    addLog(`Connecting to tenant: ${slug}...`, "info");
    await loadTenant(slug.trim());
  };

  const handleCreateTenant = async () => {
    if (!slug.trim()) return;
    addLog(`Creating tenant: ${slug}...`, "info");
    try {
      const t = await createTenant(slug.trim(), slug.trim().replace(/-/g, " "));
      setTenant(t);
      addLog(`Tenant created: ${t.name}`, "ok");
      setProjects([]);
      setInvoice(null);
    } catch (err) {
      addLog(
        `Failed: ${err instanceof Error ? err.message : "unknown"}`,
        "err",
      );
    }
  };

  const handleAddProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tenant || !newProjName.trim() || !newProjRate.trim()) return;
    try {
      const rateCents = Math.round(parseFloat(newProjRate) * 100);
      const p = await createProject(tenant.slug, newProjName.trim(), rateCents);
      addLog(
        `Project created: ${p.name} @ ${formatRate(p.hourly_rate_cents)}`,
        "ok",
      );
      setProjects((prev) => [...prev, p]);
      setNewProjName("");
      setNewProjRate("");
    } catch (err) {
      addLog(
        `Failed: ${err instanceof Error ? err.message : "unknown"}`,
        "err",
      );
    }
  };

  const handleLogTime = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tenant || !logProjectId || !logMinutes.trim()) return;
    try {
      const mins = parseInt(logMinutes);
      await logTime(tenant.slug, logProjectId, logDate, mins, logBillable);
      const proj = projects.find((p) => p.id === logProjectId);
      addLog(
        `Logged ${formatDuration(mins)} on ${proj?.name ?? "?"} (${logDate}) ${logBillable ? "[BILLABLE]" : "[NON-BILLABLE]"}`,
        "ok",
      );
      // Refresh invoice
      const inv = await getInvoice(tenant.slug, currentYear, currentMonth);
      setInvoice(inv);
    } catch (err) {
      addLog(
        `Failed: ${err instanceof Error ? err.message : "unknown"}`,
        "err",
      );
    }
  };

  // If no tenant connected, show connect prompt
  if (!tenant) {
    return (
      <div className="max-w-2xl space-y-6">
        <AsciiBox title="CONNECT" color="green">
          <AsciiRow>
            <span className="text-terminal-gray">
              Enter tenant slug to connect
            </span>
          </AsciiRow>
          <AsciiRow>
            <form onSubmit={handleConnect} className="flex gap-2 items-center">
              <span className="text-terminal-amber">{">"}</span>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="acme-consulting"
                className="terminal-input flex-1"
                autoFocus
              />
              <button type="submit" className="btn-terminal text-xs">
                CONNECT
              </button>
            </form>
          </AsciiRow>
          <AsciiRow>
            <button
              onClick={handleCreateTenant}
              className="text-terminal-gray hover:text-terminal-amber text-xs transition-colors"
            >
              or CREATE new tenant
            </button>
          </AsciiRow>
        </AsciiBox>

        {/* Log output */}
        <div className="space-y-0">
          {logs.map((l, i) => (
            <LogLine key={i} message={l.msg} level={l.level} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Tenant header */}
      <div className="flex items-center gap-4 text-xs">
        <span className="status-dot" />
        <span className="text-terminal-white glow-white font-bold uppercase tracking-widest">
          {tenant.name}
        </span>
        <span className="text-terminal-gray">({tenant.slug})</span>
        <button
          onClick={() => {
            setTenant(null);
            setProjects([]);
            setInvoice(null);
            setSlug("");
            addLog("Disconnected", "warn");
          }}
          className="text-terminal-gray hover:text-terminal-red ml-auto transition-colors"
        >
          [DISCONNECT]
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Projects table */}
        <AsciiBox title="PROJECTS" color="green">
          <AsciiRow>
            <span className="text-terminal-white font-bold">
              {"NAME".padEnd(20)}
              {"RATE".padStart(12)}
            </span>
          </AsciiRow>
          <AsciiDivider />
          {projects.length === 0 ? (
            <AsciiRow>
              <span className="text-terminal-gray">No projects yet</span>
            </AsciiRow>
          ) : (
            projects.map((p) => (
              <AsciiRow key={p.id}>
                <span>
                  {p.name.padEnd(20)}
                  <span className="text-terminal-amber">
                    {formatRate(p.hourly_rate_cents).padStart(12)}
                  </span>
                </span>
              </AsciiRow>
            ))
          )}
          <AsciiDivider label="ADD PROJECT" />
          <AsciiRow>
            <form
              onSubmit={handleAddProject}
              className="flex gap-2 items-center"
            >
              <span className="text-terminal-amber">{">"}</span>
              <input
                type="text"
                value={newProjName}
                onChange={(e) => setNewProjName(e.target.value)}
                placeholder="name"
                className="terminal-input w-28"
              />
              <input
                type="text"
                value={newProjRate}
                onChange={(e) => setNewProjRate(e.target.value)}
                placeholder="kr/h"
                className="terminal-input w-16 text-right"
              />
              <button type="submit" className="btn-terminal text-xs">
                ADD
              </button>
            </form>
          </AsciiRow>
        </AsciiBox>

        {/* Invoice preview */}
        <AsciiBox
          title={`INVOICE ${currentYear}-${String(currentMonth).padStart(2, "0")}`}
          color="amber"
        >
          {!invoice || invoice.line_items.length === 0 ? (
            <AsciiRow>
              <span className="text-terminal-gray">
                No billable time this month
              </span>
            </AsciiRow>
          ) : (
            <>
              <AsciiRow>
                <span className="text-terminal-white font-bold">
                  {"PROJECT".padEnd(16)}
                  {"HOURS".padStart(8)}
                  {"AMOUNT".padStart(14)}
                </span>
              </AsciiRow>
              <AsciiDivider />
              {invoice.line_items.map((item) => (
                <AsciiRow key={item.project_id}>
                  <span>
                    {item.project_name.slice(0, 16).padEnd(16)}
                    <span className="text-terminal-green">
                      {formatDuration(item.total_minutes).padStart(8)}
                    </span>
                    <span className="text-terminal-amber">
                      {formatSEK(item.amount_cents).padStart(14)}
                    </span>
                  </span>
                </AsciiRow>
              ))}
              <AsciiDivider />
              <AsciiRow>
                <span>
                  {"Subtotal".padEnd(24)}
                  <span className="text-terminal-amber">
                    {formatSEK(invoice.subtotal_cents).padStart(14)}
                  </span>
                </span>
              </AsciiRow>
              <AsciiRow>
                <span>
                  {"Moms 25%".padEnd(24)}
                  <span className="text-terminal-amber">
                    {formatSEK(invoice.tax_amount_cents).padStart(14)}
                  </span>
                </span>
              </AsciiRow>
              <AsciiDivider />
              <AsciiRow>
                <span className="text-terminal-white font-bold glow-white">
                  {"TOTAL".padEnd(24)}
                  {formatSEK(invoice.total_cents).padStart(14)}
                </span>
              </AsciiRow>
            </>
          )}
          <AsciiDivider />
          <AsciiRow>
            <Link
              href={`/invoice?slug=${tenant.slug}&year=${currentYear}&month=${currentMonth}`}
              className="text-terminal-amber hover:text-terminal-white transition-colors text-xs"
            >
              [VIEW FULL INVOICE]
            </Link>
          </AsciiRow>
        </AsciiBox>
      </div>

      {/* Log time */}
      <AsciiBox title="LOG TIME" color="green">
        <AsciiRow>
          <form
            onSubmit={handleLogTime}
            className="flex flex-wrap gap-3 items-center"
          >
            <span className="text-terminal-amber">{">"}</span>
            <select
              value={logProjectId ?? ""}
              onChange={(e) => setLogProjectId(Number(e.target.value) || null)}
              className="bg-terminal-black text-terminal-green border border-terminal-green-dim px-2 py-1 text-xs"
            >
              <option value="">project</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <input
              type="date"
              value={logDate}
              onChange={(e) => setLogDate(e.target.value)}
              className="bg-terminal-black text-terminal-green border border-terminal-green-dim px-2 py-1 text-xs"
            />
            <input
              type="number"
              value={logMinutes}
              onChange={(e) => setLogMinutes(e.target.value)}
              placeholder="min"
              className="terminal-input w-16 border border-terminal-green-dim px-2 py-1"
              min={1}
            />
            <span className="text-terminal-gray text-xs">min</span>
            <label className="flex items-center gap-1 text-xs cursor-pointer">
              <input
                type="checkbox"
                checked={logBillable}
                onChange={(e) => setLogBillable(e.target.checked)}
                className="accent-terminal-green"
              />
              <span
                className={
                  logBillable ? "text-terminal-green" : "text-terminal-gray"
                }
              >
                BILLABLE
              </span>
            </label>
            <button type="submit" className="btn-terminal text-xs">
              LOG
            </button>
          </form>
        </AsciiRow>
      </AsciiBox>

      {/* System log */}
      <AsciiBox title="SYSTEM LOG" color="white">
        <div className="max-h-40 overflow-y-auto">
          {logs.length === 0 ? (
            <AsciiRow>
              <span className="text-terminal-gray">Awaiting input...</span>
            </AsciiRow>
          ) : (
            logs.map((l, i) => (
              <AsciiRow key={i}>
                <LogLine message={l.msg} level={l.level} />
              </AsciiRow>
            ))
          )}
          <AsciiRow>
            <span className="cursor-blink text-terminal-green"> </span>
          </AsciiRow>
        </div>
      </AsciiBox>
    </div>
  );
}
