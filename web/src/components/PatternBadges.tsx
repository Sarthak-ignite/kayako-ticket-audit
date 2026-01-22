import type { PatternId } from "@/lib/types";

const LABELS: Record<PatternId, string> = {
  AI_QUALITY_FAILURES: "AI quality failures",
  AI_WALL_LOOPING: "AI wall / looping",
  IGNORING_CONTEXT: "Ignoring context",
  RESPONSE_DELAYS: "Response delays",
  PREMATURE_CLOSURE: "Premature closure",
  P1_SEV1_MISHANDLING: "P1/SEV1 mishandling",
};

export function PatternBadge({ pattern }: { pattern: PatternId }) {
  return (
    <span className="inline-flex items-center rounded-full border border-zinc-200 bg-white px-2 py-0.5 text-xs font-medium text-zinc-700 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-200">
      {LABELS[pattern]}
    </span>
  );
}

export function PatternBadges({ patterns }: { patterns: PatternId[] }) {
  if (!patterns.length) return <span className="text-xs text-zinc-500">None</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {patterns.map((p) => (
        <PatternBadge key={p} pattern={p} />
      ))}
    </div>
  );
}


