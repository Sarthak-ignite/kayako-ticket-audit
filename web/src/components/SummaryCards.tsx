import type { AnalyticsSummary } from "@/lib/analytics";

interface SummaryCardsProps {
  summary: AnalyticsSummary;
}

function StatCard({
  title,
  value,
  subtitle,
  trend,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
}) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{title}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
        {value}
      </p>
      {subtitle && (
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{subtitle}</p>
      )}
    </div>
  );
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
      <StatCard
        title="Total Tickets"
        value={summary.totalTickets.toLocaleString()}
        subtitle="In dataset"
      />
      <StatCard
        title="With Issues"
        value={summary.ticketsWithPatterns.toLocaleString()}
        subtitle={`${summary.detectionRate.toFixed(1)}% detection rate`}
      />
      <StatCard
        title="Total Patterns"
        value={summary.totalPatternsDetected.toLocaleString()}
        subtitle="Issues flagged"
      />
      <StatCard
        title="Avg per Ticket"
        value={summary.avgPatternsPerTicket.toFixed(2)}
        subtitle="Patterns detected"
      />
      <StatCard
        title="SEV1 Tickets"
        value={summary.sev1Count.toLocaleString()}
        subtitle={`${summary.sev1Percentage.toFixed(1)}% of total`}
      />
      <StatCard
        title="Detection Rate"
        value={`${summary.detectionRate.toFixed(0)}%`}
        subtitle="Tickets with issues"
      />
    </div>
  );
}
