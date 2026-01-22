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

function ChartCard({
  title,
  description,
  icon,
  children,
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="group overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-950">
      <div className="border-b border-zinc-100 bg-gradient-to-r from-zinc-50 to-white px-6 py-4 dark:border-zinc-800/50 dark:from-zinc-900/50 dark:to-zinc-950">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-zinc-100 p-2 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
            {icon}
          </div>
          <div>
            <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">{title}</h2>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">{description}</p>
          </div>
        </div>
      </div>
      <div className="p-6">{children}</div>
    </section>
  );
}

function ChartIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}

function PieIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 1 0 7.5 7.5h-7.5V6Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0 0 13.5 3v7.5Z" />
    </svg>
  );
}

function GridIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
    </svg>
  );
}

function HistogramIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0 0 20.25 18V6A2.25 2.25 0 0 0 18 3.75H6A2.25 2.25 0 0 0 3.75 6v12A2.25 2.25 0 0 0 6 20.25Z" />
    </svg>
  );
}

function SourceIcon() {
  return (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.172 48.172 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
    </svg>
  );
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
        <ChartCard
          title="Pattern Detection Frequency"
          description="Number of tickets where each quality pattern was detected"
          icon={<ChartIcon />}
        >
          <PatternBarChart data={patternStats} />
        </ChartCard>

        <ChartCard
          title="Tickets by Vertical"
          description="Distribution of tickets across business verticals"
          icon={<PieIcon />}
        >
          <VerticalPieChart data={verticalStats} />
        </ChartCard>
      </div>

      <ChartCard
        title="Pattern Heatmap by Vertical"
        description="Pattern detection rate (%) for each vertical - darker colors indicate higher frequency"
        icon={<GridIcon />}
      >
        <PatternHeatmap data={verticalStats} />
      </ChartCard>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Tickets by Issue Count"
          description="Distribution of tickets by number of patterns detected"
          icon={<HistogramIcon />}
        >
          <TicketDistributionChart data={ticketsByPatternCount} />
        </ChartCard>

        <ChartCard
          title="Tickets by Source Channel"
          description="Ticket volume and SEV1 incidents by source channel"
          icon={<SourceIcon />}
        >
          <SourceChart data={sourceBreakdown} />
        </ChartCard>
      </div>
    </>
  );
}
