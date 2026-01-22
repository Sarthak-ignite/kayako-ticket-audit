"use client";

import { PatternBarChart } from "@/components/charts/PatternBarChart";
import { VerticalPieChart } from "@/components/charts/VerticalPieChart";
import { PatternHeatmap } from "@/components/charts/PatternHeatmap";
import { TicketDistributionChart } from "@/components/charts/TicketDistributionChart";
import { SourceChart } from "@/components/charts/SourceChart";
import type { PatternStats, VerticalStats, SourceBreakdown } from "@/lib/analytics";

interface AnalyticsChartsProps {
  patternStats: PatternStats[];
  verticalStats: VerticalStats[];
  sourceBreakdown: SourceBreakdown[];
  ticketsByPatternCount: { patternCount: number; ticketCount: number }[];
}

export function AnalyticsCharts({
  patternStats,
  verticalStats,
  sourceBreakdown,
  ticketsByPatternCount,
}: AnalyticsChartsProps) {
  return (
    <>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-4 text-lg font-semibold">Pattern Detection Frequency</h2>
          <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
            Number of tickets where each quality pattern was detected
          </p>
          <PatternBarChart data={patternStats} />
        </section>

        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-4 text-lg font-semibold">Tickets by Vertical</h2>
          <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
            Distribution of tickets across business verticals
          </p>
          <VerticalPieChart data={verticalStats} />
        </section>
      </div>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="mb-4 text-lg font-semibold">Pattern Heatmap by Vertical</h2>
        <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
          Pattern detection rate (%) for each vertical - darker colors indicate higher frequency
        </p>
        <PatternHeatmap data={verticalStats} />
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-4 text-lg font-semibold">Tickets by Issue Count</h2>
          <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
            Distribution of tickets by number of patterns detected
          </p>
          <TicketDistributionChart data={ticketsByPatternCount} />
        </section>

        <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
          <h2 className="mb-4 text-lg font-semibold">Tickets by Source Channel</h2>
          <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
            Ticket volume and SEV1 incidents by source channel
          </p>
          <SourceChart data={sourceBreakdown} />
        </section>
      </div>
    </>
  );
}
