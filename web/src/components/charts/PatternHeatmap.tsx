"use client";

import type { VerticalStats } from "@/lib/analytics";
import type { PatternId } from "@/lib/types";

const PATTERN_LABELS: Record<string, string> = {
  AI_QUALITY_FAILURES: "AI Quality",
  AI_WALL_LOOPING: "AI Wall",
  IGNORING_CONTEXT: "Ignore Ctx",
  RESPONSE_DELAYS: "Delays",
  PREMATURE_CLOSURE: "Premature",
  P1_SEV1_MISHANDLING: "P1/SEV1",
};

const PATTERNS: PatternId[] = [
  "AI_QUALITY_FAILURES",
  "AI_WALL_LOOPING",
  "IGNORING_CONTEXT",
  "RESPONSE_DELAYS",
  "PREMATURE_CLOSURE",
  "P1_SEV1_MISHANDLING",
];

interface PatternHeatmapProps {
  data: VerticalStats[];
}

function getHeatColor(percentage: number): string {
  if (percentage === 0) return "bg-zinc-800";
  if (percentage < 10) return "bg-blue-900/50";
  if (percentage < 20) return "bg-blue-700/60";
  if (percentage < 30) return "bg-yellow-600/60";
  if (percentage < 40) return "bg-orange-600/70";
  if (percentage < 50) return "bg-orange-500/80";
  return "bg-red-500/90";
}

export function PatternHeatmap({ data }: PatternHeatmapProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-zinc-400">
              Vertical
            </th>
            {PATTERNS.map((pattern) => (
              <th
                key={pattern}
                className="px-2 py-2 text-center text-xs font-medium text-zinc-400"
              >
                {PATTERN_LABELS[pattern]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.vertical} className="border-t border-zinc-800">
              <td className="px-3 py-2 font-medium text-zinc-200">
                {row.vertical}
                <span className="ml-2 text-xs text-zinc-500">({row.totalTickets})</span>
              </td>
              {PATTERNS.map((pattern) => {
                const count = row.patternBreakdown[pattern] || 0;
                const percentage =
                  row.totalTickets > 0 ? (count / row.totalTickets) * 100 : 0;
                return (
                  <td key={pattern} className="px-2 py-2">
                    <div
                      className={`mx-auto flex h-10 w-14 items-center justify-center rounded ${getHeatColor(
                        percentage
                      )}`}
                      title={`${count} tickets (${percentage.toFixed(1)}%)`}
                    >
                      <span className="text-xs font-medium text-zinc-200">
                        {percentage > 0 ? `${percentage.toFixed(0)}%` : "-"}
                      </span>
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="mt-4 flex items-center justify-center gap-2 text-xs text-zinc-500">
        <span>Low</span>
        <div className="flex gap-1">
          <div className="h-4 w-6 rounded bg-zinc-800" />
          <div className="h-4 w-6 rounded bg-blue-900/50" />
          <div className="h-4 w-6 rounded bg-blue-700/60" />
          <div className="h-4 w-6 rounded bg-yellow-600/60" />
          <div className="h-4 w-6 rounded bg-orange-600/70" />
          <div className="h-4 w-6 rounded bg-red-500/90" />
        </div>
        <span>High</span>
      </div>
    </div>
  );
}
