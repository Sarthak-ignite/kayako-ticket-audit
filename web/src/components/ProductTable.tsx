import type { ProductStats } from "@/lib/analytics";

const PATTERN_LABELS: Record<string, string> = {
  AI_QUALITY_FAILURES: "AI Quality",
  AI_WALL_LOOPING: "AI Wall",
  IGNORING_CONTEXT: "Ignore Ctx",
  RESPONSE_DELAYS: "Delays",
  PREMATURE_CLOSURE: "Premature",
  P1_SEV1_MISHANDLING: "P1/SEV1",
};

interface ProductTableProps {
  data: ProductStats[];
  limit?: number;
}

export function ProductTable({ data, limit = 10 }: ProductTableProps) {
  const displayData = data.slice(0, limit);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-200 text-left text-xs uppercase tracking-wide text-zinc-500 dark:border-zinc-800">
            <th scope="col" className="px-4 py-3">Product</th>
            <th scope="col" className="px-4 py-3">Vertical</th>
            <th scope="col" className="px-4 py-3 text-right">Tickets</th>
            <th scope="col" className="px-4 py-3 text-right">With Issues</th>
            <th scope="col" className="px-4 py-3 text-right">Rate</th>
            <th scope="col" className="px-4 py-3">Top Patterns</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 dark:divide-zinc-900">
          {displayData.map((product) => (
            <tr
              key={product.product}
              className="hover:bg-zinc-50 dark:hover:bg-zinc-900/40"
            >
              <td className="px-4 py-3 font-medium text-zinc-900 dark:text-zinc-100">
                {product.product || "Unknown"}
              </td>
              <td className="px-4 py-3 text-zinc-600 dark:text-zinc-400">
                {product.vertical}
              </td>
              <td className="px-4 py-3 text-right tabular-nums">
                {product.totalTickets}
              </td>
              <td className="px-4 py-3 text-right tabular-nums">
                {product.detectedCount}
              </td>
              <td className="px-4 py-3 text-right">
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                    product.detectionRate >= 50
                      ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                      : product.detectionRate >= 25
                      ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                      : "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  }`}
                >
                  {product.detectionRate.toFixed(0)}%
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {product.topPatterns.map((pattern) => (
                    <span
                      key={pattern}
                      className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                    >
                      {PATTERN_LABELS[pattern] || pattern}
                    </span>
                  ))}
                  {product.topPatterns.length === 0 && (
                    <span className="text-xs text-zinc-400">-</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
