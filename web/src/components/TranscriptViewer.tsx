"use client";

import { useMemo, useState } from "react";
import type { TranscriptEvent } from "@/lib/types";

export function TranscriptViewer({ transcript }: { transcript: TranscriptEvent[] }) {
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const qq = q.trim().toLowerCase();
    if (!qq) return transcript;
    return transcript.filter((e) => e.text.toLowerCase().includes(qq) || e.ts.toLowerCase().includes(qq));
  }, [q, transcript]);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-center justify-between gap-3 border-b border-zinc-200 p-4 dark:border-zinc-800">
        <div>
          <h3 className="text-sm font-semibold">Transcript</h3>
          <p className="text-xs text-zinc-500">{filtered.length} events</p>
        </div>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search transcript…"
          className="w-full max-w-sm rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-black"
        />
      </div>
      <div className="max-h-[60vh] overflow-auto p-4">
        <div className="space-y-3">
          {filtered.map((e, idx) => (
            <div key={`${e.ts}-${idx}`} className="rounded-md border border-zinc-200 p-3 text-sm dark:border-zinc-800">
              <div className="text-xs font-medium text-zinc-500">{e.ts}</div>
              <pre className="mt-2 whitespace-pre-wrap break-words font-sans text-sm text-zinc-900 dark:text-zinc-50">
                {e.text}
              </pre>
            </div>
          ))}
          {!filtered.length ? (
            <div className="py-8 text-center text-sm text-zinc-500">No transcript events match.</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}


