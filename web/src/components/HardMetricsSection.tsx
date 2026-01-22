import type { TicketHardMetrics } from "@/lib/types";
import { formatDuration, formatBoolean } from "@/lib/formatters";

interface HardMetricsSectionProps {
  metrics: TicketHardMetrics | undefined;
}

type MetricStatus = "normal" | "warning" | "critical";

function MetricCard({
  label,
  value,
  subtitle,
  status = "normal",
}: {
  label: string;
  value: string;
  subtitle?: string;
  status?: MetricStatus;
}) {
  const statusStyles: Record<MetricStatus, string> = {
    normal: "border-zinc-200 dark:border-zinc-800",
    warning:
      "border-yellow-400/50 bg-yellow-50/50 dark:border-yellow-500/30 dark:bg-yellow-950/20",
    critical:
      "border-red-400/50 bg-red-50/50 dark:border-red-500/30 dark:bg-red-950/20",
  };

  return (
    <div className={`rounded-lg border p-3 ${statusStyles[status]}`}>
      <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
      {subtitle && (
        <div className="mt-0.5 text-xs text-zinc-500">{subtitle}</div>
      )}
    </div>
  );
}

function FlagIndicator({
  active,
  label,
  description,
}: {
  active: boolean;
  label: string;
  description: string;
}) {
  return (
    <div
      className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${
        active
          ? "border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-200"
          : "border-zinc-200 bg-zinc-50 text-zinc-600 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400"
      }`}
    >
      <span
        className={`h-2.5 w-2.5 shrink-0 rounded-full ${
          active ? "bg-red-500" : "bg-zinc-300 dark:bg-zinc-600"
        }`}
      />
      <div>
        <div className="text-sm font-medium">{label}</div>
        <div className="text-xs opacity-75">{description}</div>
      </div>
    </div>
  );
}

export function HardMetricsSection({ metrics }: HardMetricsSectionProps) {
  const csv = metrics?.csv;
  const interactions = metrics?.interactions;
  const flags = metrics?.flags;

  const hasData = csv || interactions;

  if (!hasData) {
    return (
      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="text-lg font-semibold">Hard Metrics</h2>
        <p className="mt-2 text-sm text-zinc-500">
          No algorithmic metrics available for this ticket.
        </p>
      </section>
    );
  }

  // Determine status for metrics
  const responseStatus: MetricStatus = flags?.slowInitialResponse
    ? "critical"
    : "normal";
  const resolutionStatus: MetricStatus = flags?.longResolution
    ? "critical"
    : "normal";
  const holdStatus: MetricStatus = flags?.extendedHold ? "warning" : "normal";

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mb-5">
        <h2 className="text-lg font-semibold">Hard Metrics</h2>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Algorithmically computed from ticket data
        </p>
      </div>

      {/* Timing Metrics Grid */}
      {csv && (
        <div className="mb-6">
          <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Timing
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <MetricCard
              label="Initial Response"
              value={formatDuration(csv.initialResponseTime)}
              status={responseStatus}
            />
            <MetricCard
              label="Resolution Time"
              value={formatDuration(csv.resolutionTime)}
              status={resolutionStatus}
            />
            <MetricCard
              label="Time at L1"
              value={formatDuration(csv.timeSpentOpenL1)}
            />
            <MetricCard
              label="Time at L2"
              value={formatDuration(csv.timeSpentOpenL2)}
            />
            <MetricCard
              label="Time on Hold"
              value={formatDuration(csv.timeSpentInHold)}
              status={holdStatus}
            />
            <MetricCard
              label="Time Pending"
              value={formatDuration(csv.timeSpentInPending)}
            />
          </div>
        </div>
      )}

      {/* Resolution Metrics */}
      {csv && (
        <div className="mb-6">
          <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Resolution
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricCard
              label="FCR"
              value={formatBoolean(csv.fcr)}
              subtitle="First Contact Resolution"
            />
            <MetricCard label="Level Solved" value={csv.levelSolved || "-"} />
            <MetricCard
              label="Escalated to BU"
              value={formatBoolean(csv.wasHandedToBu)}
            />
            <MetricCard label="L2 FCR" value={formatBoolean(csv.l2Fcr)} />
          </div>
        </div>
      )}

      {/* Interaction Metrics */}
      {interactions && (
        <div className="mb-6">
          <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Interactions
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <MetricCard
              label="Total"
              value={String(interactions.totalInteractions)}
            />
            <MetricCard
              label="AI Responses"
              value={String(interactions.aiCount)}
              subtitle={
                interactions.atlasCount > 0 || interactions.hermesCount > 0
                  ? `Atlas: ${interactions.atlasCount}, Hermes: ${interactions.hermesCount}`
                  : undefined
              }
            />
            <MetricCard
              label="Employee"
              value={String(interactions.employeeCount)}
            />
            <MetricCard
              label="Customer"
              value={String(interactions.customerCount)}
            />
            <MetricCard
              label="Max Gap"
              value={formatDuration(interactions.maxGapSeconds)}
              subtitle={
                interactions.gapsOver24h > 0
                  ? `${interactions.gapsOver24h} gaps > 24h`
                  : undefined
              }
            />
          </div>
        </div>
      )}

      {/* Derived Flags / Alerts */}
      {flags && (
        <div>
          <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Alerts
          </h3>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            <FlagIndicator
              active={flags.slowInitialResponse}
              label="Slow Initial Response"
              description="> 24 hours to first response"
            />
            <FlagIndicator
              active={flags.longResolution}
              label="Long Resolution"
              description="> 7 days to resolve"
            />
            <FlagIndicator
              active={flags.extendedHold}
              label="Extended Hold"
              description="> 24 hours total hold time"
            />
            <FlagIndicator
              active={flags.wasEscalated}
              label="Was Escalated"
              description="Handled by L2 or BU"
            />
            <FlagIndicator
              active={flags.hasLargeGaps}
              label="Large Response Gaps"
              description="Gaps > 48 hours detected"
            />
          </div>
        </div>
      )}
    </section>
  );
}
