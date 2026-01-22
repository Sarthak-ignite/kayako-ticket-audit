import type { AnalyticsSummary } from "@/lib/analytics";

interface SummaryCardsProps {
  summary: AnalyticsSummary;
}

type CardVariant = "default" | "warning" | "success" | "info" | "danger";

const variantStyles: Record<CardVariant, { bg: string; icon: string; border: string }> = {
  default: {
    bg: "bg-gradient-to-br from-zinc-50 to-zinc-100 dark:from-zinc-900 dark:to-zinc-950",
    icon: "text-zinc-400",
    border: "border-zinc-200 dark:border-zinc-800",
  },
  warning: {
    bg: "bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/20",
    icon: "text-amber-500",
    border: "border-amber-200/60 dark:border-amber-800/40",
  },
  success: {
    bg: "bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-950/30 dark:to-green-950/20",
    icon: "text-emerald-500",
    border: "border-emerald-200/60 dark:border-emerald-800/40",
  },
  info: {
    bg: "bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/20",
    icon: "text-blue-500",
    border: "border-blue-200/60 dark:border-blue-800/40",
  },
  danger: {
    bg: "bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-950/30 dark:to-rose-950/20",
    icon: "text-red-500",
    border: "border-red-200/60 dark:border-red-800/40",
  },
};

function StatCard({
  title,
  value,
  subtitle,
  icon,
  variant = "default",
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  variant?: CardVariant;
}) {
  const styles = variantStyles[variant];
  return (
    <div className={`relative overflow-hidden rounded-2xl border ${styles.border} ${styles.bg} p-5 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            {title}
          </p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            {value}
          </p>
          {subtitle && (
            <p className="mt-1.5 text-sm text-zinc-500 dark:text-zinc-400">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className={`rounded-xl bg-white/60 p-2.5 dark:bg-black/20 ${styles.icon}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

function TicketIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-5.25h5.25M7.5 15h3M3.375 5.25c-.621 0-1.125.504-1.125 1.125v3.026a2.999 2.999 0 0 1 0 5.198v3.026c0 .621.504 1.125 1.125 1.125h17.25c.621 0 1.125-.504 1.125-1.125v-3.026a2.999 2.999 0 0 1 0-5.198V6.375c0-.621-.504-1.125-1.125-1.125H3.375Z" />
    </svg>
  );
}

function AlertIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}

function FireIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0 1 12 21 8.25 8.25 0 0 1 6.038 7.047 8.287 8.287 0 0 0 9 9.601a8.983 8.983 0 0 1 3.361-6.867 8.21 8.21 0 0 0 3 2.48Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18a3.75 3.75 0 0 0 .495-7.468 5.99 5.99 0 0 0-1.925 3.547 5.975 5.975 0 0 1-2.133-1.001A3.75 3.75 0 0 0 12 18Z" />
    </svg>
  );
}

function PercentIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m9 14.25 6-6m4.5-3.493V21.75l-3.75-1.5-3.75 1.5-3.75-1.5-3.75 1.5V4.757c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0 1 11.186 0c1.1.128 1.907 1.077 1.907 2.185ZM9.75 9h.008v.008H9.75V9Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm4.125 4.5h.008v.008h-.008V13.5Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
    </svg>
  );
}

function HashIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 8.25h15m-16.5 7.5h15m-1.8-13.5-3.9 19.5m-2.1-19.5-3.9 19.5" />
    </svg>
  );
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
      <StatCard
        title="Total Tickets"
        value={summary.totalTickets.toLocaleString()}
        subtitle="In dataset"
        icon={<TicketIcon />}
        variant="info"
      />
      <StatCard
        title="With Issues"
        value={summary.ticketsWithPatterns.toLocaleString()}
        subtitle={`${summary.detectionRate.toFixed(1)}% of total`}
        icon={<AlertIcon />}
        variant="warning"
      />
      <StatCard
        title="Total Patterns"
        value={summary.totalPatternsDetected.toLocaleString()}
        subtitle="Issues flagged"
        icon={<ChartIcon />}
        variant="default"
      />
      <StatCard
        title="Avg per Ticket"
        value={summary.avgPatternsPerTicket.toFixed(2)}
        subtitle="Patterns detected"
        icon={<HashIcon />}
        variant="default"
      />
      <StatCard
        title="SEV1 Tickets"
        value={summary.sev1Count.toLocaleString()}
        subtitle={`${summary.sev1Percentage.toFixed(1)}% of total`}
        icon={<FireIcon />}
        variant="danger"
      />
      <StatCard
        title="Detection Rate"
        value={`${summary.detectionRate.toFixed(0)}%`}
        subtitle="Tickets with issues"
        icon={<PercentIcon />}
        variant="success"
      />
    </div>
  );
}
