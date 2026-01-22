import fs from "node:fs/promises";
import path from "node:path";
import { parse } from "csv-parse/sync";

import type { DatasetConfig } from "@/lib/datasets";
import {
  OUR_PATTERNS,
  type PatternId,
  type TicketDetail,
  type TicketListItem,
  type TicketResultJson,
  type TicketSummaryRow,
  type TranscriptEvent,
  type CsvMetrics,
  type TicketInteractionMetrics,
  type DerivedMetricFlags,
  type TicketHardMetrics,
} from "@/lib/types";

const summaryCache = new Map<string, TicketSummaryRow[]>();
const csvMetricsCache = new Map<string, Map<number, CsvMetrics>>();
const ticketMetricsCache = new Map<string, Map<number, TicketInteractionMetrics>>();

function toBool(v: string | undefined): boolean {
  const s = (v || "").trim().toLowerCase();
  return s === "1" || s === "true" || s === "yes";
}

function safeJsonParse<T>(s: string, fallback: T): T {
  try {
    return JSON.parse(s) as T;
  } catch {
    return fallback;
  }
}

function parseNumeric(v: string | undefined): number | null {
  if (!v || v.trim() === "") return null;
  const n = parseFloat(v);
  return isNaN(n) ? null : n;
}

function parseIntSafe(v: string | undefined): number {
  const n = parseInt(v || "0", 10);
  return isNaN(n) ? 0 : n;
}

export async function loadSummaryRows(dataset: DatasetConfig): Promise<TicketSummaryRow[]> {
  if (!dataset.summaryCsvPath) return [];
  if (summaryCache.has(dataset.summaryCsvPath)) return summaryCache.get(dataset.summaryCsvPath)!;

  const csvText = await fs.readFile(dataset.summaryCsvPath, "utf-8");
  const rows = parse(csvText, {
    columns: true,
    skip_empty_lines: true,
  }) as TicketSummaryRow[];

  summaryCache.set(dataset.summaryCsvPath, rows);
  return rows;
}

export function rowToListItem(row: TicketSummaryRow): TicketListItem {
  const ticketId = Number.parseInt(row.ticket_id || row["Ticket ID"] || "0", 10);
  const vertical = row.vertical || row.Brand || "";
  const product = row.Product || "";
  const status = row.Status || "";
  const priority = row.Priority || "";
  const isSev1 = toBool(row.isSev1);
  const source = row.source || "";

  const predictedLabels = safeJsonParse<PatternId[]>(row.predicted_labels || "[]", [])
    .filter((x) => (OUR_PATTERNS as readonly string[]).includes(x)) as PatternId[];

  const detectedCount = predictedLabels.length;

  return {
    ticketId,
    vertical,
    product,
    status,
    priority,
    isSev1,
    source,
    predictedLabels,
    detectedCount,
    row,
  };
}

export type TicketListQuery = {
  datasetId: string;
  q?: string;
  vertical?: string;
  product?: string;
  status?: string;
  source?: string;
  onlySev1?: boolean;
  patterns?: PatternId[];
  sort?: "updated_desc" | "created_desc" | "patterns_desc";
  offset?: number;
  limit?: number;
};

export async function queryTickets(dataset: DatasetConfig, query: TicketListQuery): Promise<{ total: number; items: TicketListItem[] }> {
  const rows = await loadSummaryRows(dataset);
  let items = rows.map(rowToListItem).filter((x) => x.ticketId > 0);

  const q = (query.q || "").trim();
  if (q) {
    const qLower = q.toLowerCase();
    items = items.filter((t) => {
      if (String(t.ticketId).includes(qLower)) return true;
      if ((t.product || "").toLowerCase().includes(qLower)) return true;
      return false;
    });
  }

  if (query.vertical) items = items.filter((t) => t.vertical === query.vertical);
  if (query.product) items = items.filter((t) => t.product === query.product);
  if (query.status) items = items.filter((t) => t.status === query.status);
  if (query.source) items = items.filter((t) => t.source === query.source);
  if (query.onlySev1) items = items.filter((t) => t.isSev1);

  if (query.patterns && query.patterns.length > 0) {
    const required = new Set(query.patterns);
    items = items.filter((t) => query.patterns!.every((p) => required.has(p) && t.predictedLabels.includes(p)));
  }

  // Sorting
  const sort = query.sort || "patterns_desc";
  if (sort === "patterns_desc") {
    items.sort((a, b) => b.detectedCount - a.detectedCount);
  } else if (sort === "updated_desc") {
    items.sort((a, b) => {
      const au = a.row["Ticket Updated"] || "";
      const bu = b.row["Ticket Updated"] || "";
      return bu.localeCompare(au);
    });
  } else if (sort === "created_desc") {
    items.sort((a, b) => {
      const ac = a.row["Ticket Created"] || "";
      const bc = b.row["Ticket Created"] || "";
      return bc.localeCompare(ac);
    });
  }

  const total = items.length;
  const offset = Math.max(0, query.offset || 0);
  const limit = Math.max(1, query.limit || 50);
  const page = items.slice(offset, offset + limit);
  return { total, items: page };
}

export async function loadTicketResult(dataset: DatasetConfig, ticketId: number): Promise<TicketResultJson | undefined> {
  const p = path.join(dataset.resultsDir, `ticket_${ticketId}.json`);
  try {
    const text = await fs.readFile(p, "utf-8");
    return safeJsonParse<TicketResultJson>(text, {} as TicketResultJson);
  } catch {
    return undefined;
  }
}

export async function loadTicketTranscript(dataset: DatasetConfig, ticketId: number): Promise<TranscriptEvent[] | undefined> {
  const p = path.join(dataset.rawDir, `ticket_${ticketId}.json`);
  try {
    const text = await fs.readFile(p, "utf-8");
    const raw = safeJsonParse<unknown>(text, null);
    const interactions =
      typeof raw === "object" && raw !== null
        ? (raw as { payload?: { ticket?: { interactions?: unknown } } }).payload?.ticket?.interactions
        : undefined;
    if (!Array.isArray(interactions)) return [];

    // Stored reverse-chronological in our pipeline; sort by timestamp ascending just in case.
    const events: TranscriptEvent[] = interactions
      .filter((x: unknown): x is unknown[] => Array.isArray(x) && x.length >= 2)
      .map((arr) => ({ ts: String(arr[0] || ""), text: String(arr[1] || "") }))
      .filter((e) => e.ts && e.text);

    events.sort((a, b) => a.ts.localeCompare(b.ts));
    return events;
  } catch {
    return undefined;
  }
}

// Load CSV metrics (timing, resolution data) from poc_csv_metrics.csv
export async function loadCsvMetrics(
  dataset: DatasetConfig
): Promise<Map<number, CsvMetrics>> {
  if (!dataset.csvMetricsPath) return new Map();
  if (csvMetricsCache.has(dataset.csvMetricsPath)) {
    return csvMetricsCache.get(dataset.csvMetricsPath)!;
  }

  try {
    const csvText = await fs.readFile(dataset.csvMetricsPath, "utf-8");
    const rows = parse(csvText, {
      columns: true,
      skip_empty_lines: true,
    }) as Record<string, string>[];

    const map = new Map<number, CsvMetrics>();
    for (const row of rows) {
      const ticketId = parseInt(row["Ticket ID"] || "0", 10);
      if (ticketId > 0) {
        map.set(ticketId, {
          ticketId,
          initialResponseTime: parseNumeric(row.initialResponseTime),
          resolutionTime: parseNumeric(row.resolutionTime),
          timeSpentInNew: parseNumeric(row.timeSpentInNew),
          timeSpentInOpen: parseNumeric(row.timeSpentInOpen),
          timeSpentInHold: parseNumeric(row.timeSpentInHold),
          timeSpentInPending: parseNumeric(row.timeSpentInPending),
          timeSpentOpenL1: parseNumeric(row.timeSpentOpenL1),
          timeSpentOpenL2: parseNumeric(row.timeSpentOpenL2),
          timeSpentOpenUnassigned: parseNumeric(row.timeSpentOpenUnassigned),
          levelSolved: row["Level Solved"] || null,
          wasHandedToBu: toBool(row.was_handed_to_bu),
          fcr: toBool(row.FCR),
          fcrPlus: toBool(row.fcrPlus),
          l2Fcr: toBool(row.l2Fcr),
          ticketCreated: row["Ticket Created"] || null,
          ticketSolved: row["Ticket Solved"] || null,
          ticketClosed: row["Ticket Closed"] || null,
          npsScore: parseNumeric(row["NPS Score"]),
          csatScore: parseNumeric(row["CSAT Score"]),
        });
      }
    }

    csvMetricsCache.set(dataset.csvMetricsPath, map);
    return map;
  } catch {
    return new Map();
  }
}

// Load ticket interaction metrics from poc_ticket_metrics.csv
export async function loadTicketInteractionMetrics(
  dataset: DatasetConfig
): Promise<Map<number, TicketInteractionMetrics>> {
  if (!dataset.ticketMetricsPath) return new Map();
  if (ticketMetricsCache.has(dataset.ticketMetricsPath)) {
    return ticketMetricsCache.get(dataset.ticketMetricsPath)!;
  }

  try {
    const csvText = await fs.readFile(dataset.ticketMetricsPath, "utf-8");
    const rows = parse(csvText, {
      columns: true,
      skip_empty_lines: true,
    }) as Record<string, string>[];

    const map = new Map<number, TicketInteractionMetrics>();
    for (const row of rows) {
      const ticketId = parseInt(row.ticket_id || "0", 10);
      if (ticketId > 0) {
        map.set(ticketId, {
          ticketId,
          aiCount: parseIntSafe(row.ai_count),
          employeeCount: parseIntSafe(row.employee_count),
          customerCount: parseIntSafe(row.customer_count),
          totalInteractions: parseIntSafe(row.total_interactions),
          atlasCount: parseIntSafe(row.atlas_count),
          hermesCount: parseIntSafe(row.hermes_count),
          timeToFirstHumanSeconds: parseNumeric(row.time_to_first_human_seconds),
          timeToFirstAiSeconds: parseNumeric(row.time_to_first_ai_seconds),
          maxGapSeconds: parseNumeric(row.max_gap_seconds),
          gapsOver24h: parseIntSafe(row.gaps_over_24h),
          gapsOver48h: parseIntSafe(row.gaps_over_48h),
          maxConsecutiveAi: parseIntSafe(row.max_consecutive_ai),
          aiOnlyBeforeHuman: toBool(row.ai_only_before_human),
          hasCustomerFrustrationKeywords: toBool(row.has_customer_frustration_keywords),
          hasPreviousTicketReference: toBool(row.has_previous_ticket_reference),
          hasRepeatedInfoRequest: toBool(row.has_repeated_info_request),
        });
      }
    }

    ticketMetricsCache.set(dataset.ticketMetricsPath, map);
    return map;
  } catch {
    return new Map();
  }
}

// Compute derived flags based on thresholds
function computeDerivedFlags(
  csv: CsvMetrics | null,
  interactions: TicketInteractionMetrics | null
): DerivedMetricFlags {
  const SECONDS_24H = 24 * 60 * 60;
  const SECONDS_7D = 7 * 24 * 60 * 60;

  return {
    slowInitialResponse:
      csv?.initialResponseTime != null && csv.initialResponseTime > SECONDS_24H,
    longResolution:
      csv?.resolutionTime != null && csv.resolutionTime > SECONDS_7D,
    extendedHold:
      csv?.timeSpentInHold != null && csv.timeSpentInHold > SECONDS_24H,
    wasEscalated:
      (csv?.levelSolved?.includes("L2") ?? false) || (csv?.wasHandedToBu ?? false),
    hasLargeGaps: (interactions?.gapsOver48h ?? 0) > 0,
  };
}

// Load all hard metrics for a ticket
export async function loadTicketHardMetrics(
  dataset: DatasetConfig,
  ticketId: number
): Promise<TicketHardMetrics> {
  const [csvMap, interactionsMap] = await Promise.all([
    loadCsvMetrics(dataset),
    loadTicketInteractionMetrics(dataset),
  ]);

  const csv = csvMap.get(ticketId) || null;
  const interactions = interactionsMap.get(ticketId) || null;
  const flags = computeDerivedFlags(csv, interactions);

  return { csv, interactions, flags };
}

export async function loadTicketDetail(dataset: DatasetConfig, ticketId: number): Promise<TicketDetail> {
  const summaryRows = await loadSummaryRows(dataset);
  const summary = summaryRows.find((r) => Number.parseInt(r.ticket_id || "0", 10) === ticketId);

  const [result, transcript, hardMetrics] = await Promise.all([
    loadTicketResult(dataset, ticketId),
    loadTicketTranscript(dataset, ticketId),
    loadTicketHardMetrics(dataset, ticketId),
  ]);

  return {
    ticketId,
    dataset: dataset.id,
    summary,
    result,
    transcript,
    hardMetrics,
  };
}


