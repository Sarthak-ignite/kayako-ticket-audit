import Link from "next/link";
import { UserButton } from "@clerk/nextjs";

import { DATASETS, getDataset } from "@/lib/datasets";
import { computeAnalytics, type AnalyticsFilters } from "@/lib/analytics";
import { OUR_PATTERNS, type PatternId } from "@/lib/types";
import { SummaryCards } from "@/components/SummaryCards";
import { ProductTable } from "@/components/ProductTable";
import { HardMetricsAnalytics } from "@/components/HardMetricsAnalytics";
import { AnalyticsFilters as AnalyticsFiltersComponent } from "@/components/AnalyticsFilters";
import { AnalyticsCharts } from "./AnalyticsCharts";

export const metadata = {
  title: "Analytics | Ticket Review Dashboard",
  description: "Aggregate analytics and reports for support ticket quality patterns",
};

export default async function AnalyticsPage(props: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const searchParams = await props.searchParams;
  const datasetId = (searchParams.dataset as string) || "v6_sample";
  const dataset = getDataset(datasetId);

  // Parse filter parameters
  const filters: AnalyticsFilters = {
    vertical: (searchParams.vertical as string) || undefined,
    product: (searchParams.product as string) || undefined,
    status: (searchParams.status as string) || undefined,
    priority: (searchParams.priority as string) || undefined,
    onlySev1: searchParams.onlySev1 === "true",
    patterns: (Array.isArray(searchParams.pattern)
      ? searchParams.pattern
      : searchParams.pattern
        ? [searchParams.pattern]
        : []
    ).filter((p) => (OUR_PATTERNS as readonly string[]).includes(p)) as PatternId[],
  };

  // Check if any filters are active
  const hasActiveFilters =
    filters.vertical ||
    filters.product ||
    filters.status ||
    filters.priority ||
    filters.onlySev1 ||
    (filters.patterns && filters.patterns.length > 0);

  const analytics = await computeAnalytics(dataset, filters);
  const datasetOptions = Object.values(DATASETS).map((d) => ({ id: d.id, label: d.label }));

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-black dark:text-zinc-50">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 p-8">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Analytics Dashboard</h1>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              Aggregate views for <span className="font-medium">{dataset.label}</span>
              {hasActiveFilters && (
                <span className="ml-2 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
                  Filtered
                </span>
              )}
              {" "}({analytics.summary.totalTickets} tickets)
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              className="text-sm underline text-zinc-700 hover:text-zinc-900 dark:text-zinc-300"
              href="/tickets"
            >
              Tickets
            </Link>
            <Link
              className="text-sm underline text-zinc-700 hover:text-zinc-900 dark:text-zinc-300"
              href="/"
            >
              Home
            </Link>
            <UserButton />
          </div>
        </header>

        <AnalyticsFiltersComponent
          datasets={datasetOptions}
          verticals={analytics.filterOptions.verticals}
          products={analytics.filterOptions.products}
          statuses={analytics.filterOptions.statuses}
          priorities={analytics.filterOptions.priorities}
        />

        <SummaryCards summary={analytics.summary} />

        <HardMetricsAnalytics
          metrics={analytics.hardMetricsSummary}
          totalTickets={analytics.summary.totalTickets}
        />

        <AnalyticsCharts
          patternStats={analytics.patternStats}
          verticalStats={analytics.verticalStats}
          sourceBreakdown={analytics.sourceBreakdown}
          ticketsByPatternCount={analytics.ticketsByPatternCount}
        />

        <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <div className="border-b border-zinc-100 bg-gradient-to-r from-zinc-50 to-white px-6 py-4 dark:border-zinc-800/50 dark:from-zinc-900/50 dark:to-zinc-950">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-zinc-100 p-2 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
                </svg>
              </div>
              <div>
                <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">Products by Issue Rate</h2>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Products ranked by percentage of tickets with detected issues</p>
              </div>
            </div>
          </div>
          <div className="p-6">
            <ProductTable data={analytics.productStats} limit={15} />
          </div>
        </section>

        <section className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <div className="border-b border-zinc-100 bg-gradient-to-r from-zinc-50 to-white px-6 py-4 dark:border-zinc-800/50 dark:from-zinc-900/50 dark:to-zinc-950">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-100 p-2 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
                </svg>
              </div>
              <div>
                <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">Pattern Co-occurrence</h2>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Tickets where multiple patterns appear together</p>
              </div>
            </div>
          </div>
          <div className="p-6">
            {analytics.patternCoOccurrence.length > 0 ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {analytics.patternCoOccurrence.slice(0, 9).map((co) => (
                  <div
                    key={`${co.pattern1}-${co.pattern2}`}
                    className="group flex items-center justify-between rounded-xl border border-zinc-200 bg-gradient-to-br from-zinc-50 to-white px-4 py-3 transition-all hover:border-zinc-300 hover:shadow-sm dark:border-zinc-800 dark:from-zinc-900 dark:to-zinc-950 dark:hover:border-zinc-700"
                  >
                    <div className="flex items-center gap-2 text-sm">
                      <PatternPill pattern={co.pattern1} />
                      <span className="text-zinc-300 dark:text-zinc-600">+</span>
                      <PatternPill pattern={co.pattern2} />
                    </div>
                    <span className="rounded-full bg-zinc-900 px-2.5 py-1 text-xs font-semibold text-white dark:bg-zinc-100 dark:text-zinc-900">
                      {co.count}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 py-8 text-center">
                <svg className="h-8 w-8 text-zinc-300 dark:text-zinc-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
                </svg>
                <span className="text-sm text-zinc-500">No pattern co-occurrences found</span>
              </div>
            )}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
            <div className="border-b border-zinc-100 bg-gradient-to-r from-blue-50 to-white px-6 py-4 dark:border-zinc-800/50 dark:from-blue-950/20 dark:to-zinc-950">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-blue-100 p-2 text-blue-600 dark:bg-blue-900/50 dark:text-blue-400">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                </div>
                <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">Status Breakdown</h2>
              </div>
            </div>
            <div className="p-6">
              {analytics.statusBreakdown.length > 0 ? (
                <div className="space-y-4">
                  {analytics.statusBreakdown.map((status) => (
                    <div key={status.status} className="group">
                      <div className="mb-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-zinc-700 dark:text-zinc-300">
                            {status.status || "Unknown"}
                          </span>
                          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500 dark:bg-zinc-800">
                            {status.avgPatterns.toFixed(1)} avg
                          </span>
                        </div>
                        <span className="text-sm font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
                          {status.count} <span className="font-normal text-zinc-500">({status.percentage.toFixed(0)}%)</span>
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-500"
                          style={{ width: `${status.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-500">No data available.</p>
              )}
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
            <div className="border-b border-zinc-100 bg-gradient-to-r from-purple-50 to-white px-6 py-4 dark:border-zinc-800/50 dark:from-purple-950/20 dark:to-zinc-950">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-purple-100 p-2 text-purple-600 dark:bg-purple-900/50 dark:text-purple-400">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 4.5h14.25M3 9h9.75M3 13.5h9.75m4.5-4.5v12m0 0-3.75-3.75M17.25 21l3.75-3.75" />
                  </svg>
                </div>
                <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">Priority Breakdown</h2>
              </div>
            </div>
            <div className="p-6">
              {analytics.priorityBreakdown.length > 0 ? (
                <div className="space-y-4">
                  {analytics.priorityBreakdown.map((priority) => (
                    <div key={priority.priority} className="group">
                      <div className="mb-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-zinc-700 dark:text-zinc-300">
                            {priority.priority || "Unknown"}
                          </span>
                          <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500 dark:bg-zinc-800">
                            {priority.avgPatterns.toFixed(1)} avg
                          </span>
                        </div>
                        <span className="text-sm font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
                          {priority.count} <span className="font-normal text-zinc-500">({priority.percentage.toFixed(0)}%)</span>
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-purple-400 transition-all duration-500"
                          style={{ width: `${priority.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-500">No data available.</p>
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

const PATTERN_LABELS: Record<string, string> = {
  AI_QUALITY_FAILURES: "AI Quality",
  AI_WALL_LOOPING: "AI Wall",
  IGNORING_CONTEXT: "Ignore Ctx",
  RESPONSE_DELAYS: "Delays",
  PREMATURE_CLOSURE: "Premature",
  P1_SEV1_MISHANDLING: "P1/SEV1",
};

const PATTERN_COLORS: Record<string, { bg: string; text: string }> = {
  AI_QUALITY_FAILURES: { bg: "bg-purple-100 dark:bg-purple-900/50", text: "text-purple-700 dark:text-purple-300" },
  AI_WALL_LOOPING: { bg: "bg-orange-100 dark:bg-orange-900/50", text: "text-orange-700 dark:text-orange-300" },
  IGNORING_CONTEXT: { bg: "bg-blue-100 dark:bg-blue-900/50", text: "text-blue-700 dark:text-blue-300" },
  RESPONSE_DELAYS: { bg: "bg-amber-100 dark:bg-amber-900/50", text: "text-amber-700 dark:text-amber-300" },
  PREMATURE_CLOSURE: { bg: "bg-rose-100 dark:bg-rose-900/50", text: "text-rose-700 dark:text-rose-300" },
  P1_SEV1_MISHANDLING: { bg: "bg-red-100 dark:bg-red-900/50", text: "text-red-700 dark:text-red-300" },
};

function PatternPill({ pattern }: { pattern: string }) {
  const colors = PATTERN_COLORS[pattern] || { bg: "bg-zinc-100 dark:bg-zinc-800", text: "text-zinc-700 dark:text-zinc-300" };
  return (
    <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${colors.bg} ${colors.text}`}>
      {PATTERN_LABELS[pattern] || pattern}
    </span>
  );
}

function formatPattern(pattern: string): string {
  return PATTERN_LABELS[pattern] || pattern;
}
