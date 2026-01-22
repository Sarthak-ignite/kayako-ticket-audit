import { repoPath } from "@/lib/paths";

export type DatasetId = "v6_sample" | "v6_gt";

export type DatasetConfig = {
  id: DatasetId;
  label: string;
  summaryCsvPath?: string;
  csvMetricsPath?: string; // path to poc_csv_metrics.csv
  ticketMetricsPath?: string; // path to poc_ticket_metrics.csv
  resultsDir: string;
  rawDir: string;
};

export const DATASETS: Record<DatasetId, DatasetConfig> = {
  v6_sample: {
    id: "v6_sample",
    label: "GPT-5.2 v6 (sample)",
    summaryCsvPath: repoPath("data/poc/poc_llm_v6_sample_summary.csv"),
    csvMetricsPath: repoPath("data/poc/poc_csv_metrics.csv"),
    ticketMetricsPath: repoPath("data/poc/poc_ticket_metrics.csv"),
    resultsDir: repoPath("data/poc/llm_results/gpt-5.2-v6-sample"),
    rawDir: repoPath("data/poc/raw"),
  },
  v6_gt: {
    id: "v6_gt",
    label: "GPT-5.2 v6 (ground-truth rerun)",
    csvMetricsPath: repoPath("data/poc/poc_csv_metrics.csv"),
    ticketMetricsPath: repoPath("data/poc/poc_ticket_metrics.csv"),
    resultsDir: repoPath("data/poc/llm_results/gpt-5.2-v6-gt-rerun"),
    rawDir: repoPath("data/poc/raw"),
  },
};

export function getDataset(id: string | null | undefined): DatasetConfig {
  const key = (id || "v6_sample") as DatasetId;
  return DATASETS[key] || DATASETS.v6_sample;
}


