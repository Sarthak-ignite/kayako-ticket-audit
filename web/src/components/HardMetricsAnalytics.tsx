import type { HardMetricsSummary } from "@/lib/analytics";

interface HardMetricsAnalyticsProps {
  metrics: HardMetricsSummary;
  totalTickets: number;
}

function formatHours(hours: number | null): string {
  if (hours == null) return "-";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${hours.toFixed(1)}h`;
  const days = hours / 24;
  return `${days.toFixed(1)}d`;
}

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

function formatNumber(value: number | null, decimals: number = 1): string {
  if (value == null) return "-";
  return value.toFixed(decimals);
}

function MetricCard({
  label,
  value,
  subtitle,
  highlight,
}: {
  label: string;
  value: string;
  subtitle?: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border p-4 ${
        highlight
          ? "border-amber-200 bg-amber-50/50 dark:border-amber-900/50 dark:bg-amber-950/20"
          : "border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900"
      }`}
    >
      <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
      {subtitle && (
        <div className="mt-0.5 text-xs text-zinc-500">{subtitle}</div>
      )}
    </div>
  );
}

function AlertCounter({
  label,
  count,
  total,
  description,
}: {
  label: string;
  count: number;
  total: number;
  description: string;
}) {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  const isHighlight = percentage > 10;

  return (
    <div
      className={`flex items-center justify-between rounded-lg border px-4 py-3 ${
        isHighlight
          ? "border-red-200 bg-red-50/50 dark:border-red-900/50 dark:bg-red-950/20"
          : "border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900"
      }`}
    >
      <div>
        <div className="text-sm font-medium">{label}</div>
        <div className="text-xs text-zinc-500">{description}</div>
      </div>
      <div className="text-right">
        <div className="text-lg font-semibold">{count}</div>
        <div className="text-xs text-zinc-500">{formatPercent(percentage)}</div>
      </div>
    </div>
  );
}

export function HardMetricsAnalytics({
  metrics,
  totalTickets,
}: HardMetricsAnalyticsProps) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mb-5">
        <h2 className="text-lg font-semibold">Hard Metrics Overview</h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Aggregate timing, resolution, and interaction metrics from ticket data
        </p>
      </div>

      {/* Response Time Metrics */}
      <div className="mb-6">
        <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Response Times
        </h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <MetricCard
            label="Avg Initial Response"
            value={formatHours(metrics.avgInitialResponseHours)}
            subtitle="Time to first reply"
          />
          <MetricCard
            label="Median Initial Response"
            value={formatHours(metrics.medianInitialResponseHours)}
            subtitle="50th percentile"
          />
          <MetricCard
            label="Avg Resolution"
            value={formatHours(metrics.avgResolutionHours)}
            subtitle="Time to close"
          />
          <MetricCard
            label="Median Resolution"
            value={formatHours(metrics.medianResolutionHours)}
            subtitle="50th percentile"
          />
        </div>
      </div>

      {/* Time Distribution */}
      <div className="mb-6">
        <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Time Distribution
        </h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <MetricCard
            label="Avg Time at L1"
            value={formatHours(metrics.avgTimeAtL1Hours)}
            subtitle="Central support"
          />
          <MetricCard
            label="Avg Time at L2"
            value={formatHours(metrics.avgTimeAtL2Hours)}
            subtitle="Business unit"
          />
          <MetricCard
            label="Avg Time on Hold"
            value={formatHours(metrics.avgTimeOnHoldHours)}
            subtitle="Customer waiting"
            highlight={(metrics.avgTimeOnHoldHours ?? 0) > 24}
          />
        </div>
      </div>

      {/* Resolution Metrics */}
      <div className="mb-6">
        <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Resolution Metrics
        </h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <MetricCard
            label="FCR Rate"
            value={formatPercent(metrics.fcrRate)}
            subtitle="First Contact Resolution"
          />
          <MetricCard
            label="Escalation Rate"
            value={formatPercent(metrics.escalationRate)}
            subtitle="Sent to L2 or BU"
          />
          <MetricCard
            label="Avg Interactions"
            value={formatNumber(metrics.avgTotalInteractions)}
            subtitle="Per ticket"
          />
          <MetricCard
            label="Avg AI Interactions"
            value={formatNumber(metrics.avgAiInteractions)}
            subtitle="Per ticket"
          />
        </div>
      </div>

      {/* Alert Flags */}
      <div>
        <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Quality Alerts
        </h3>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <AlertCounter
            label="Slow Initial Response"
            count={metrics.slowResponseCount}
            total={totalTickets}
            description="> 24 hours"
          />
          <AlertCounter
            label="Long Resolution"
            count={metrics.longResolutionCount}
            total={totalTickets}
            description="> 7 days"
          />
          <AlertCounter
            label="Extended Hold"
            count={metrics.extendedHoldCount}
            total={totalTickets}
            description="> 24 hours"
          />
          <AlertCounter
            label="Large Response Gaps"
            count={metrics.largeGapsCount}
            total={totalTickets}
            description="> 48 hours"
          />
        </div>
        {metrics.ticketsWithFrustration > 0 && (
          <div className="mt-3">
            <AlertCounter
              label="Customer Frustration Detected"
              count={metrics.ticketsWithFrustration}
              total={totalTickets}
              description="Frustration keywords found"
            />
          </div>
        )}
      </div>
    </section>
  );
}
