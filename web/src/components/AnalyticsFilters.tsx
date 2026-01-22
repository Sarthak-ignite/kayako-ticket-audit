"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { OUR_PATTERNS, type PatternId } from "@/lib/types";
import { useMemo } from "react";

function setParam(params: URLSearchParams, key: string, value: string | null) {
  if (!value) params.delete(key);
  else params.set(key, value);
}

export function AnalyticsFilters(props: {
  datasets: { id: string; label: string }[];
  verticals: string[];
  products: string[];
  statuses: string[];
  priorities: string[];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const selectedPatterns = useMemo(() => {
    const raw = searchParams.getAll("pattern");
    return raw.filter((p) =>
      (OUR_PATTERNS as readonly string[]).includes(p)
    ) as PatternId[];
  }, [searchParams]);

  function apply(next: URLSearchParams) {
    router.push(`${pathname}?${next.toString()}`);
  }

  const hasFilters =
    searchParams.get("vertical") ||
    searchParams.get("product") ||
    searchParams.get("status") ||
    searchParams.get("priority") ||
    searchParams.get("onlySev1") === "true" ||
    selectedPatterns.length > 0;

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Filter Analytics
        </h3>
        {hasFilters && (
          <button
            type="button"
            className="text-xs text-zinc-600 underline hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200"
            onClick={() => {
              const next = new URLSearchParams();
              next.set("dataset", searchParams.get("dataset") || "v6_sample");
              apply(next);
            }}
          >
            Reset filters
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Dataset
          </label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("dataset") || "v6_sample"}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "dataset", e.target.value || null);
              apply(next);
            }}
          >
            {props.datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Vertical
          </label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("vertical") || ""}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "vertical", e.target.value || null);
              apply(next);
            }}
          >
            <option value="">All Verticals</option>
            {props.verticals.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Product
          </label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("product") || ""}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "product", e.target.value || null);
              apply(next);
            }}
          >
            <option value="">All Products</option>
            {props.products.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Status
          </label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("status") || ""}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "status", e.target.value || null);
              apply(next);
            }}
          >
            <option value="">All Statuses</option>
            {props.statuses.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Priority
          </label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("priority") || ""}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "priority", e.target.value || null);
              apply(next);
            }}
          >
            <option value="">All Priorities</option>
            {props.priorities.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-end">
          <label className="inline-flex items-center gap-2 pb-2">
            <input
              type="checkbox"
              checked={
                (searchParams.get("onlySev1") || "").toLowerCase() === "true"
              }
              onChange={(e) => {
                const next = new URLSearchParams(searchParams.toString());
                setParam(next, "onlySev1", e.target.checked ? "true" : null);
                apply(next);
              }}
              className="rounded"
            />
            <span className="text-sm text-zinc-700 dark:text-zinc-300">
              SEV1 Only
            </span>
          </label>
        </div>
      </div>

      {/* Pattern filter */}
      <div className="mt-4">
        <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
          Filter by Pattern (tickets must have selected patterns)
        </label>
        <div className="mt-2 flex flex-wrap gap-3">
          {OUR_PATTERNS.map((p) => {
            const checked = selectedPatterns.includes(p);
            const label = p
              .replace(/_/g, " ")
              .toLowerCase()
              .replace(/\b\w/g, (c) => c.toUpperCase());
            return (
              <label
                key={p}
                className={`inline-flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-xs transition-colors ${
                  checked
                    ? "border-blue-500 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-950/30 dark:text-blue-300"
                    : "border-zinc-200 bg-zinc-50 text-zinc-700 hover:border-zinc-300 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => {
                    const next = new URLSearchParams(searchParams.toString());
                    const cur = new Set(next.getAll("pattern"));
                    if (e.target.checked) cur.add(p);
                    else cur.delete(p);
                    next.delete("pattern");
                    for (const v of [...cur]) next.append("pattern", v);
                    apply(next);
                  }}
                  className="sr-only"
                />
                {label}
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
}
