"use client";

import { useMemo, useState, useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { OUR_PATTERNS, type PatternId } from "@/lib/types";
import { useDebounce } from "@/lib/hooks";

function setParam(params: URLSearchParams, key: string, value: string | null) {
  if (!value) params.delete(key);
  else params.set(key, value);
}

export function TicketsFilters(props: {
  datasets: { id: string; label: string }[];
  verticals: string[];
  products: string[];
  statuses: string[];
  sources: string[];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [q, setQ] = useState(searchParams.get("q") || "");
  const debouncedQ = useDebounce(q, 300);

  const selectedPatterns = useMemo(() => {
    const raw = searchParams.getAll("pattern");
    return raw.filter((p) => (OUR_PATTERNS as readonly string[]).includes(p)) as PatternId[];
  }, [searchParams]);

  function apply(next: URLSearchParams) {
    router.push(`${pathname}?${next.toString()}`);
  }

  // Auto-search when debounced query changes
  useEffect(() => {
    const currentQ = searchParams.get("q") || "";
    if (debouncedQ !== currentQ) {
      const next = new URLSearchParams(searchParams.toString());
      setParam(next, "q", debouncedQ.trim() || null);
      setParam(next, "offset", "0");
      apply(next);
    }
  }, [debouncedQ]);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-6">
        <div className="md:col-span-2">
          <label htmlFor="search-input" className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">Search</label>
          <div className="relative mt-1">
            <input
              id="search-input"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Ticket id or product…"
              className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 pr-8 text-sm dark:border-zinc-700 dark:bg-black"
            />
            {q !== debouncedQ && (
              <div className="absolute right-2 top-1/2 -translate-y-1/2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-600" />
              </div>
            )}
            {q && q === debouncedQ && (
              <button
                type="button"
                onClick={() => setQ("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                aria-label="Clear search"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">Dataset</label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("dataset") || "v6_sample"}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "dataset", e.target.value || null);
              setParam(next, "offset", "0");
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
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">Vertical</label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("vertical") || ""}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "vertical", e.target.value || null);
              setParam(next, "offset", "0");
              apply(next);
            }}
          >
            <option value="">All</option>
            {props.verticals.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">Product</label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("product") || ""}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "product", e.target.value || null);
              setParam(next, "offset", "0");
              apply(next);
            }}
          >
            <option value="">All</option>
            {props.products.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">Status</label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("status") || ""}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "status", e.target.value || null);
              setParam(next, "offset", "0");
              apply(next);
            }}
          >
            <option value="">All</option>
            {props.statuses.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div>
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">Source</label>
          <select
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
            value={searchParams.get("source") || ""}
            onChange={(e) => {
              const next = new URLSearchParams(searchParams.toString());
              setParam(next, "source", e.target.value || null);
              setParam(next, "offset", "0");
              apply(next);
            }}
          >
            <option value="">All</option>
            {props.sources.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="block text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Patterns (requires all selected)
          </label>
          <div className="mt-2 flex flex-wrap gap-2">
            {OUR_PATTERNS.map((p) => {
              const checked = selectedPatterns.includes(p);
              return (
                <label key={p} className="inline-flex items-center gap-2 text-sm">
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
                      setParam(next, "offset", "0");
                      apply(next);
                    }}
                  />
                  <span className="text-xs text-zinc-700 dark:text-zinc-300">{p}</span>
                </label>
              );
            })}
          </div>

          <div className="mt-3 flex items-center gap-4">
            <label className="inline-flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={(searchParams.get("onlySev1") || "").toLowerCase() === "true"}
                onChange={(e) => {
                  const next = new URLSearchParams(searchParams.toString());
                  setParam(next, "onlySev1", e.target.checked ? "true" : null);
                  setParam(next, "offset", "0");
                  apply(next);
                }}
              />
              <span className="text-xs text-zinc-700 dark:text-zinc-300">Only Sev1</span>
            </label>

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
          </div>
        </div>
      </div>
    </div>
  );
}


