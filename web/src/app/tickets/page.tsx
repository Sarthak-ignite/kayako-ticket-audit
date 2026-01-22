import Link from "next/link";
import { UserButton } from "@clerk/nextjs";

import { DATASETS, getDataset } from "@/lib/datasets";
import { loadSummaryRows, queryTickets } from "@/lib/data";
import { PatternBadges } from "@/components/PatternBadges";
import { TicketsFilters } from "@/components/TicketsFilters";
import { Pagination } from "@/components/Pagination";
import { OUR_PATTERNS, type PatternId } from "@/lib/types";

function uniqSorted(values: string[]) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b));
}

function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  let colorClasses = "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400";

  if (normalized.includes("closed") || normalized.includes("resolved")) {
    colorClasses = "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400";
  } else if (normalized.includes("open") || normalized.includes("new")) {
    colorClasses = "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400";
  } else if (normalized.includes("pending") || normalized.includes("hold")) {
    colorClasses = "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400";
  }

  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${colorClasses}`}>
      {status}
    </span>
  );
}

function PriorityBadge({ priority, isSev1 }: { priority: string; isSev1: boolean }) {
  if (isSev1) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 dark:bg-red-950/50 dark:text-red-400">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-500" />
        SEV1
      </span>
    );
  }

  const normalized = priority.toLowerCase();
  let colorClasses = "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400";

  if (normalized.includes("high") || normalized.includes("urgent") || normalized === "1") {
    colorClasses = "bg-orange-100 text-orange-700 dark:bg-orange-950/50 dark:text-orange-400";
  } else if (normalized.includes("medium") || normalized === "2") {
    colorClasses = "bg-yellow-100 text-yellow-700 dark:bg-yellow-950/50 dark:text-yellow-400";
  } else if (normalized.includes("low") || normalized === "3" || normalized === "4") {
    colorClasses = "bg-green-100 text-green-700 dark:bg-green-950/50 dark:text-green-400";
  }

  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${colorClasses}`}>
      {priority}
    </span>
  );
}

export default async function TicketsPage(props: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const searchParams = await props.searchParams;
  const datasetId = (searchParams.dataset as string) || "v6_sample";
  const dataset = getDataset(datasetId);

  const q = (searchParams.q as string) || undefined;
  const vertical = (searchParams.vertical as string) || undefined;
  const product = (searchParams.product as string) || undefined;
  const status = (searchParams.status as string) || undefined;
  const source = (searchParams.source as string) || undefined;
  const onlySev1 = ((searchParams.onlySev1 as string) || "").toLowerCase() === "true";

  const patternsRaw = searchParams.pattern;
  const patternsList = (Array.isArray(patternsRaw) ? patternsRaw : patternsRaw ? [patternsRaw] : [])
    .filter((p) => (OUR_PATTERNS as readonly string[]).includes(p)) as PatternId[];

  const offsetRaw = Number.parseInt((searchParams.offset as string) || "0", 10);
  const limitRaw = Number.parseInt((searchParams.limit as string) || "50", 10);
  const offset = Number.isFinite(offsetRaw) && offsetRaw >= 0 ? offsetRaw : 0;
  const limit = Number.isFinite(limitRaw) && limitRaw >= 1 && limitRaw <= 100 ? limitRaw : 50;

  const rows = await loadSummaryRows(dataset);
  const verticals = uniqSorted(rows.map((r) => r.vertical || r.Brand || ""));
  const products = uniqSorted(rows.map((r) => r.Product || ""));
  const statuses = uniqSorted(rows.map((r) => r.Status || ""));
  const sources = uniqSorted(rows.map((r) => r.source || ""));

  const { total, items } = await queryTickets(dataset, {
    datasetId,
    q,
    vertical,
    product,
    status,
    source,
    onlySev1,
    patterns: patternsList,
    sort: "patterns_desc",
    offset,
    limit,
  });

  const datasetOptions = Object.values(DATASETS).map((d) => ({ id: d.id, label: d.label }));

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-black dark:text-zinc-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 p-8">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Tickets</h1>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              <span className="font-medium">{total}</span> tickets found (dataset:{" "}
              <span className="font-medium">{dataset.label}</span>)
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link className="text-sm underline text-zinc-700 hover:text-zinc-900 dark:text-zinc-300" href="/analytics">
              Analytics
            </Link>
            <Link className="text-sm underline text-zinc-700 hover:text-zinc-900 dark:text-zinc-300" href="/">
              Home
            </Link>
            <UserButton />
          </div>
        </header>

        <TicketsFilters
          datasets={datasetOptions}
          verticals={verticals}
          products={products}
          statuses={statuses}
          sources={sources}
        />

        <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50/50 text-left text-xs uppercase tracking-wider text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900/50">
                <tr>
                  <th scope="col" className="px-5 py-4 font-semibold">Ticket</th>
                  <th scope="col" className="px-5 py-4 font-semibold">Vertical</th>
                  <th scope="col" className="px-5 py-4 font-semibold">Product</th>
                  <th scope="col" className="px-5 py-4 font-semibold">Status</th>
                  <th scope="col" className="px-5 py-4 font-semibold">Priority</th>
                  <th scope="col" className="px-5 py-4 font-semibold">Detected Patterns</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/50">
                {items.map((t, idx) => (
                  <tr
                    key={t.ticketId}
                    className={`group transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-900/60 ${
                      t.detectedCount > 0 ? "bg-red-50/30 dark:bg-red-950/10" : ""
                    }`}
                  >
                    <td className="px-5 py-4">
                      <Link
                        className="inline-flex items-center gap-2 font-mono font-semibold text-zinc-900 transition-colors hover:text-blue-600 dark:text-zinc-50 dark:hover:text-blue-400"
                        href={`/tickets/${t.ticketId}?dataset=${encodeURIComponent(dataset.id)}`}
                      >
                        <span className="text-zinc-400 dark:text-zinc-600">#</span>
                        {t.ticketId}
                        <svg className="h-4 w-4 opacity-0 transition-opacity group-hover:opacity-100" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                        </svg>
                      </Link>
                      {t.source && (
                        <div className="mt-1.5 text-xs text-zinc-400 dark:text-zinc-500">
                          via {t.source}
                        </div>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-zinc-700 dark:text-zinc-300">{t.vertical || "-"}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-zinc-700 dark:text-zinc-300">{t.product || "-"}</span>
                    </td>
                    <td className="px-5 py-4">
                      {t.status ? <StatusPill status={t.status} /> : <span className="text-zinc-400">-</span>}
                    </td>
                    <td className="px-5 py-4">
                      {t.priority || t.isSev1 ? (
                        <PriorityBadge priority={t.priority || ""} isSev1={t.isSev1} />
                      ) : (
                        <span className="text-zinc-400">-</span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <PatternBadges patterns={t.predictedLabels} compact />
                    </td>
                  </tr>
                ))}
                {!items.length ? (
                  <tr>
                    <td className="px-5 py-12 text-center" colSpan={6}>
                      <div className="flex flex-col items-center gap-2">
                        <svg className="h-8 w-8 text-zinc-300 dark:text-zinc-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                        </svg>
                        <span className="text-sm text-zinc-500">No tickets match these filters</span>
                      </div>
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>

          <div className="border-t border-zinc-200 bg-zinc-50/50 px-5 py-4 dark:border-zinc-800 dark:bg-zinc-900/30">
            <Pagination total={total} offset={offset} limit={limit} />
          </div>
        </section>
      </div>
    </main>
  );
}


