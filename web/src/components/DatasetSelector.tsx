"use client";

import { useRouter, useSearchParams } from "next/navigation";

interface DatasetSelectorProps {
  datasets: { id: string; label: string }[];
  currentDataset: string;
}

export function DatasetSelector({ datasets, currentDataset }: DatasetSelectorProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  return (
    <select
      id="dataset-select"
      value={currentDataset}
      onChange={(e) => {
        const next = new URLSearchParams(searchParams.toString());
        next.set("dataset", e.target.value);
        router.push(`?${next.toString()}`);
      }}
      className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-black"
    >
      {datasets.map((d) => (
        <option key={d.id} value={d.id}>
          {d.label}
        </option>
      ))}
    </select>
  );
}
