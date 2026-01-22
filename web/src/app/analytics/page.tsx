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

        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-4 text-lg font-semibold">Products by Issue Rate</h2>
          <ProductTable data={analytics.productStats} limit={15} />
        </section>

        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-4 text-lg font-semibold">Pattern Co-occurrence</h2>
          <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
            Tickets where multiple patterns appear together
          </p>
          {analytics.patternCoOccurrence.length > 0 ? (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {analytics.patternCoOccurrence.slice(0, 9).map((co) => (
                <div
                  key={`${co.pattern1}-${co.pattern2}`}
                  className="flex items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <div className="text-sm">
                    <span className="font-medium text-zinc-700 dark:text-zinc-300">
                      {formatPattern(co.pattern1)}
                    </span>
                    <span className="mx-2 text-zinc-400">+</span>
                    <span className="font-medium text-zinc-700 dark:text-zinc-300">
                      {formatPattern(co.pattern2)}
                    </span>
                  </div>
                  <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-xs font-medium dark:bg-zinc-700">
                    {co.count}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500">No pattern co-occurrences found.</p>
          )}
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="mb-4 text-lg font-semibold">Status Breakdown</h2>
            {analytics.statusBreakdown.length > 0 ? (
              <div className="space-y-3">
                {analytics.statusBreakdown.map((status) => (
                  <div key={status.status} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-zinc-700 dark:text-zinc-300">
                        {status.status || "Unknown"}
                      </span>
                      <span className="text-sm text-zinc-500">
                        ({status.avgPatterns.toFixed(1)} avg patterns)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-24 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                        <div
                          className="h-full bg-blue-500"
                          style={{ width: `${status.percentage}%` }}
                        />
                      </div>
                      <span className="w-16 text-right text-sm tabular-nums text-zinc-600 dark:text-zinc-400">
                        {status.count} ({status.percentage.toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-zinc-500">No data available.</p>
            )}
          </div>

          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="mb-4 text-lg font-semibold">Priority Breakdown</h2>
            {analytics.priorityBreakdown.length > 0 ? (
              <div className="space-y-3">
                {analytics.priorityBreakdown.map((priority) => (
                  <div key={priority.priority} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="font-medium text-zinc-700 dark:text-zinc-300">
                        {priority.priority || "Unknown"}
                      </span>
                      <span className="text-sm text-zinc-500">
                        ({priority.avgPatterns.toFixed(1)} avg patterns)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-24 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                        <div
                          className="h-full bg-purple-500"
                          style={{ width: `${priority.percentage}%` }}
                        />
                      </div>
                      <span className="w-16 text-right text-sm tabular-nums text-zinc-600 dark:text-zinc-400">
                        {priority.count} ({priority.percentage.toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-zinc-500">No data available.</p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function formatPattern(pattern: string): string {
  const labels: Record<string, string> = {
    AI_QUALITY_FAILURES: "AI Quality",
    AI_WALL_LOOPING: "AI Wall",
    IGNORING_CONTEXT: "Ignore Ctx",
    RESPONSE_DELAYS: "Delays",
    PREMATURE_CLOSURE: "Premature",
    P1_SEV1_MISHANDLING: "P1/SEV1",
  };
  return labels[pattern] || pattern;
}
