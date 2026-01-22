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

        <section className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-zinc-200 text-left text-xs uppercase tracking-wide text-zinc-500 dark:border-zinc-800">
                <tr>
                  <th scope="col" className="px-4 py-3">Ticket</th>
                  <th scope="col" className="px-4 py-3">Vertical</th>
                  <th scope="col" className="px-4 py-3">Product</th>
                  <th scope="col" className="px-4 py-3">Status</th>
                  <th scope="col" className="px-4 py-3">Priority</th>
                  <th scope="col" className="px-4 py-3">Patterns</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-900">
                {items.map((t) => (
                  <tr key={t.ticketId} className="hover:bg-zinc-50 dark:hover:bg-zinc-900/40">
                    <td className="px-4 py-3">
                      <Link
                        className="font-medium text-zinc-900 underline hover:text-zinc-700 dark:text-zinc-50"
                        href={`/tickets/${t.ticketId}?dataset=${encodeURIComponent(dataset.id)}`}
                      >
                        {t.ticketId}
                      </Link>
                      <div className="mt-1 text-xs text-zinc-500">
                        {t.source ? `source: ${t.source}` : null}
                        {t.isSev1 ? " • SEV1" : null}
                      </div>
                    </td>
                    <td className="px-4 py-3">{t.vertical || "-"}</td>
                    <td className="px-4 py-3">{t.product || "-"}</td>
                    <td className="px-4 py-3">{t.status || "-"}</td>
                    <td className="px-4 py-3">{t.priority || "-"}</td>
                    <td className="px-4 py-3">
                      <PatternBadges patterns={t.predictedLabels} />
                      <div className="mt-1 text-xs text-zinc-500">{t.detectedCount} flagged</div>
                    </td>
                  </tr>
                ))}
                {!items.length ? (
                  <tr>
                    <td className="px-4 py-8 text-center text-sm text-zinc-500" colSpan={6}>
                      No tickets match these filters.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>

          <div className="border-t border-zinc-200 px-4 py-4 dark:border-zinc-800">
            <Pagination total={total} offset={offset} limit={limit} />
          </div>
        </section>
      </div>
    </main>
  );
}


