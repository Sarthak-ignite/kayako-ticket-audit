import {
  OUR_PATTERNS,
  type PatternId,
  type TicketResultJson,
} from "@/lib/types";

// Pattern display names and descriptions
const PATTERN_INFO: Record<PatternId, { label: string; description: string }> =
  {
    AI_QUALITY_FAILURES: {
      label: "AI Quality Failures",
      description: "AI provided unhelpful, incorrect, or repetitive responses",
    },
    AI_WALL_LOOPING: {
      label: "AI Wall / Looping",
      description: "Customer stuck in AI loop without reaching a human",
    },
    IGNORING_CONTEXT: {
      label: "Ignoring Context",
      description: "Support ignored information already provided by customer",
    },
    RESPONSE_DELAYS: {
      label: "Response Delays",
      description: "Significant gaps or delays in response times",
    },
    PREMATURE_CLOSURE: {
      label: "Premature Closure",
      description: "Ticket closed before issue was fully resolved",
    },
    P1_SEV1_MISHANDLING: {
      label: "P1/SEV1 Mishandling",
      description: "High priority ticket not handled with appropriate urgency",
    },
  };

interface LLMPatternsSectionProps {
  result: TicketResultJson | undefined;
}

function PatternCard({
  patternId,
  detected,
  reasoning,
  evidence,
}: {
  patternId: PatternId;
  detected: boolean;
  reasoning: string;
  evidence: string[];
}) {
  const info = PATTERN_INFO[patternId];

  return (
    <div
      className={`rounded-lg border p-4 ${
        detected
          ? "border-red-200 bg-red-50/50 dark:border-red-900/50 dark:bg-red-950/20"
          : "border-zinc-200 dark:border-zinc-800"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="font-medium">{info.label}</div>
          <div className="mt-0.5 text-xs text-zinc-500">{info.description}</div>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${
            detected
              ? "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300"
              : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
          }`}
        >
          {detected ? "DETECTED" : "NOT DETECTED"}
        </span>
      </div>

      {reasoning && (
        <p className="mt-3 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
          {reasoning}
        </p>
      )}

      {!reasoning && !detected && (
        <p className="mt-3 text-sm text-zinc-500">
          No issues detected for this pattern.
        </p>
      )}

      {evidence.length > 0 && (
        <div className="mt-4">
          <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Evidence
          </div>
          <ul className="mt-2 space-y-2">
            {evidence.map((ev, idx) => (
              <li
                key={idx}
                className="rounded-md bg-zinc-100 p-2.5 text-xs leading-relaxed text-zinc-800 dark:bg-zinc-900 dark:text-zinc-100"
              >
                {ev}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function LLMPatternsSection({ result }: LLMPatternsSectionProps) {
  // Count detected patterns
  const detectedCount = OUR_PATTERNS.filter((p) => result?.[p]?.detected).length;

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mb-5">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">LLM-Detected Patterns</h2>
          <span
            className={`rounded-full px-3 py-1 text-sm font-medium ${
              detectedCount > 0
                ? "bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300"
                : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
            }`}
          >
            {detectedCount} / {OUR_PATTERNS.length} detected
          </span>
        </div>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Each pattern includes the model's reasoning and the evidence quotes it
          cited.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {OUR_PATTERNS.map((patternId) => {
          const block = result?.[patternId];
          return (
            <PatternCard
              key={patternId}
              patternId={patternId}
              detected={Boolean(block?.detected)}
              reasoning={block?.reasoning || ""}
              evidence={Array.isArray(block?.evidence) ? block.evidence : []}
            />
          );
        })}
      </div>
    </section>
  );
}
