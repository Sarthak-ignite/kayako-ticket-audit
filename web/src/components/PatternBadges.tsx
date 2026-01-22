import type { PatternId } from "@/lib/types";

const LABELS: Record<PatternId, string> = {
  AI_QUALITY_FAILURES: "AI quality failures",
  AI_WALL_LOOPING: "AI wall / looping",
  IGNORING_CONTEXT: "Ignoring context",
  RESPONSE_DELAYS: "Response delays",
  PREMATURE_CLOSURE: "Premature closure",
  P1_SEV1_MISHANDLING: "P1/SEV1 mishandling",
};

type PatternStyle = {
  bg: string;
  border: string;
  text: string;
  dot: string;
};

const PATTERN_STYLES: Record<PatternId, PatternStyle> = {
  AI_QUALITY_FAILURES: {
    bg: "bg-purple-50 dark:bg-purple-950/40",
    border: "border-purple-200 dark:border-purple-800/60",
    text: "text-purple-700 dark:text-purple-300",
    dot: "bg-purple-500",
  },
  AI_WALL_LOOPING: {
    bg: "bg-orange-50 dark:bg-orange-950/40",
    border: "border-orange-200 dark:border-orange-800/60",
    text: "text-orange-700 dark:text-orange-300",
    dot: "bg-orange-500",
  },
  IGNORING_CONTEXT: {
    bg: "bg-blue-50 dark:bg-blue-950/40",
    border: "border-blue-200 dark:border-blue-800/60",
    text: "text-blue-700 dark:text-blue-300",
    dot: "bg-blue-500",
  },
  RESPONSE_DELAYS: {
    bg: "bg-amber-50 dark:bg-amber-950/40",
    border: "border-amber-200 dark:border-amber-800/60",
    text: "text-amber-700 dark:text-amber-300",
    dot: "bg-amber-500",
  },
  PREMATURE_CLOSURE: {
    bg: "bg-rose-50 dark:bg-rose-950/40",
    border: "border-rose-200 dark:border-rose-800/60",
    text: "text-rose-700 dark:text-rose-300",
    dot: "bg-rose-500",
  },
  P1_SEV1_MISHANDLING: {
    bg: "bg-red-50 dark:bg-red-950/40",
    border: "border-red-200 dark:border-red-800/60",
    text: "text-red-700 dark:text-red-300",
    dot: "bg-red-500",
  },
};

export function PatternBadge({ pattern, compact = false }: { pattern: PatternId; compact?: boolean }) {
  const style = PATTERN_STYLES[pattern];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${style.border} ${style.bg} px-2.5 py-1 text-xs font-medium ${style.text} transition-colors`}>
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {compact ? LABELS[pattern].split(" ")[0] : LABELS[pattern]}
    </span>
  );
}

export function PatternBadges({ patterns, compact = false }: { patterns: PatternId[]; compact?: boolean }) {
  if (!patterns.length) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs text-zinc-400 dark:border-zinc-800 dark:bg-zinc-900/50 dark:text-zinc-500">
        <span className="h-1.5 w-1.5 rounded-full bg-zinc-300 dark:bg-zinc-600" />
        No issues
      </span>
    );
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {patterns.map((p) => (
        <PatternBadge key={p} pattern={p} compact={compact} />
      ))}
    </div>
  );
}


