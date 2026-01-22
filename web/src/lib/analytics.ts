import type { DatasetConfig } from "@/lib/datasets";
import { loadSummaryRows, rowToListItem, loadCsvMetrics, loadTicketInteractionMetrics } from "@/lib/data";
import { OUR_PATTERNS, type PatternId, type TicketListItem, type CsvMetrics, type TicketInteractionMetrics } from "@/lib/types";

export type PatternStats = {
  pattern: PatternId;
  count: number;
  percentage: number;
};

export type VerticalStats = {
  vertical: string;
  totalTickets: number;
  sev1Count: number;
  sev1Percentage: number;
  avgPatternsPerTicket: number;
  patternBreakdown: Record<PatternId, number>;
};

export type ProductStats = {
  product: string;
  vertical: string;
  totalTickets: number;
  detectedCount: number;
  detectionRate: number;
  topPatterns: PatternId[];
};

export type StatusBreakdown = {
  status: string;
  count: number;
  percentage: number;
  avgPatterns: number;
};

export type SourceBreakdown = {
  source: string;
  count: number;
  percentage: number;
  sev1Count: number;
};

export type PriorityBreakdown = {
  priority: string;
  count: number;
  percentage: number;
  avgPatterns: number;
};

export type AnalyticsSummary = {
  totalTickets: number;
  ticketsWithPatterns: number;
  detectionRate: number;
  sev1Count: number;
  sev1Percentage: number;
  avgPatternsPerTicket: number;
  totalPatternsDetected: number;
};

export type PatternCoOccurrence = {
  pattern1: PatternId;
  pattern2: PatternId;
  count: number;
};

export type HardMetricsSummary = {
  // Response time metrics (in hours)
  avgInitialResponseHours: number | null;
  medianInitialResponseHours: number | null;
  avgResolutionHours: number | null;
  medianResolutionHours: number | null;
  // Time distribution (in hours)
  avgTimeAtL1Hours: number | null;
  avgTimeAtL2Hours: number | null;
  avgTimeOnHoldHours: number | null;
  // Resolution metrics
  fcrRate: number; // percentage
  escalationRate: number; // percentage handed to L2/BU
  // Alert flag counts
  slowResponseCount: number; // > 24h initial response
  longResolutionCount: number; // > 7 days
  extendedHoldCount: number; // > 24h hold
  largeGapsCount: number; // > 48h gaps
  // Interaction metrics
  avgTotalInteractions: number | null;
  avgAiInteractions: number | null;
  avgEmployeeInteractions: number | null;
  ticketsWithFrustration: number; // count with frustration keywords
};

export type AnalyticsData = {
  summary: AnalyticsSummary;
  patternStats: PatternStats[];
  verticalStats: VerticalStats[];
  productStats: ProductStats[];
  statusBreakdown: StatusBreakdown[];
  sourceBreakdown: SourceBreakdown[];
  priorityBreakdown: PriorityBreakdown[];
  patternCoOccurrence: PatternCoOccurrence[];
  ticketsByPatternCount: { patternCount: number; ticketCount: number }[];
  hardMetricsSummary: HardMetricsSummary;
  // Filter options for the UI
  filterOptions: {
    verticals: string[];
    products: string[];
    statuses: string[];
    priorities: string[];
  };
};

export type AnalyticsFilters = {
  vertical?: string;
  product?: string;
  status?: string;
  priority?: string;
  onlySev1?: boolean;
  patterns?: PatternId[];
};

export async function computeAnalytics(
  dataset: DatasetConfig,
  filters: AnalyticsFilters = {}
): Promise<AnalyticsData> {
  const rows = await loadSummaryRows(dataset);
  const allItems = rows.map(rowToListItem).filter((x) => x.ticketId > 0);

  // Extract filter options from all items (before filtering)
  const filterOptions = {
    verticals: [...new Set(allItems.map((t) => t.vertical).filter(Boolean))].sort(),
    products: [...new Set(allItems.map((t) => t.product).filter(Boolean))].sort(),
    statuses: [...new Set(allItems.map((t) => t.status).filter(Boolean))].sort(),
    priorities: [...new Set(allItems.map((t) => t.priority).filter(Boolean))].sort(),
  };

  // Apply filters
  let items = allItems;
  if (filters.vertical) {
    items = items.filter((t) => t.vertical === filters.vertical);
  }
  if (filters.product) {
    items = items.filter((t) => t.product === filters.product);
  }
  if (filters.status) {
    items = items.filter((t) => t.status === filters.status);
  }
  if (filters.priority) {
    items = items.filter((t) => t.priority === filters.priority);
  }
  if (filters.onlySev1) {
    items = items.filter((t) => t.isSev1);
  }
  if (filters.patterns && filters.patterns.length > 0) {
    items = items.filter((t) =>
      filters.patterns!.every((p) => t.predictedLabels.includes(p))
    );
  }

  // Load hard metrics data
  const [csvMetricsMap, interactionMetricsMap] = await Promise.all([
    loadCsvMetrics(dataset),
    loadTicketInteractionMetrics(dataset),
  ]);

  const summary = computeSummary(items);
  const patternStats = computePatternStats(items);
  const verticalStats = computeVerticalStats(items);
  const productStats = computeProductStats(items);
  const statusBreakdown = computeStatusBreakdown(items);
  const sourceBreakdown = computeSourceBreakdown(items);
  const priorityBreakdown = computePriorityBreakdown(items);
  const patternCoOccurrence = computePatternCoOccurrence(items);
  const ticketsByPatternCount = computeTicketsByPatternCount(items);
  const hardMetricsSummary = computeHardMetricsSummary(items, csvMetricsMap, interactionMetricsMap);

  return {
    summary,
    patternStats,
    verticalStats,
    productStats,
    statusBreakdown,
    sourceBreakdown,
    priorityBreakdown,
    patternCoOccurrence,
    ticketsByPatternCount,
    hardMetricsSummary,
    filterOptions,
  };
}

function computeSummary(items: TicketListItem[]): AnalyticsSummary {
  const totalTickets = items.length;
  const ticketsWithPatterns = items.filter((t) => t.detectedCount > 0).length;
  const sev1Count = items.filter((t) => t.isSev1).length;
  const totalPatternsDetected = items.reduce((sum, t) => sum + t.detectedCount, 0);

  return {
    totalTickets,
    ticketsWithPatterns,
    detectionRate: totalTickets > 0 ? (ticketsWithPatterns / totalTickets) * 100 : 0,
    sev1Count,
    sev1Percentage: totalTickets > 0 ? (sev1Count / totalTickets) * 100 : 0,
    avgPatternsPerTicket: totalTickets > 0 ? totalPatternsDetected / totalTickets : 0,
    totalPatternsDetected,
  };
}

function computePatternStats(items: TicketListItem[]): PatternStats[] {
  const totalTickets = items.length;
  const counts: Record<PatternId, number> = {} as Record<PatternId, number>;

  for (const pattern of OUR_PATTERNS) {
    counts[pattern] = 0;
  }

  for (const item of items) {
    for (const pattern of item.predictedLabels) {
      counts[pattern]++;
    }
  }

  return OUR_PATTERNS.map((pattern) => ({
    pattern,
    count: counts[pattern],
    percentage: totalTickets > 0 ? (counts[pattern] / totalTickets) * 100 : 0,
  })).sort((a, b) => b.count - a.count);
}

function computeVerticalStats(items: TicketListItem[]): VerticalStats[] {
  const byVertical = new Map<string, TicketListItem[]>();

  for (const item of items) {
    const vertical = item.vertical || "Unknown";
    if (!byVertical.has(vertical)) {
      byVertical.set(vertical, []);
    }
    byVertical.get(vertical)!.push(item);
  }

  const stats: VerticalStats[] = [];

  for (const [vertical, ticketList] of byVertical) {
    const totalTickets = ticketList.length;
    const sev1Count = ticketList.filter((t) => t.isSev1).length;
    const totalPatterns = ticketList.reduce((sum, t) => sum + t.detectedCount, 0);

    const patternBreakdown: Record<PatternId, number> = {} as Record<PatternId, number>;
    for (const pattern of OUR_PATTERNS) {
      patternBreakdown[pattern] = 0;
    }
    for (const ticket of ticketList) {
      for (const pattern of ticket.predictedLabels) {
        patternBreakdown[pattern]++;
      }
    }

    stats.push({
      vertical,
      totalTickets,
      sev1Count,
      sev1Percentage: totalTickets > 0 ? (sev1Count / totalTickets) * 100 : 0,
      avgPatternsPerTicket: totalTickets > 0 ? totalPatterns / totalTickets : 0,
      patternBreakdown,
    });
  }

  return stats.sort((a, b) => b.totalTickets - a.totalTickets);
}

function computeProductStats(items: TicketListItem[]): ProductStats[] {
  const byProduct = new Map<string, TicketListItem[]>();

  for (const item of items) {
    const product = item.product || "Unknown";
    if (!byProduct.has(product)) {
      byProduct.set(product, []);
    }
    byProduct.get(product)!.push(item);
  }

  const stats: ProductStats[] = [];

  for (const [product, ticketList] of byProduct) {
    const totalTickets = ticketList.length;
    const detectedCount = ticketList.filter((t) => t.detectedCount > 0).length;

    const patternCounts: Record<PatternId, number> = {} as Record<PatternId, number>;
    for (const pattern of OUR_PATTERNS) {
      patternCounts[pattern] = 0;
    }
    for (const ticket of ticketList) {
      for (const pattern of ticket.predictedLabels) {
        patternCounts[pattern]++;
      }
    }

    const topPatterns = (Object.entries(patternCounts) as [PatternId, number][])
      .sort((a, b) => b[1] - a[1])
      .filter(([, count]) => count > 0)
      .slice(0, 3)
      .map(([pattern]) => pattern);

    stats.push({
      product,
      vertical: ticketList[0]?.vertical || "Unknown",
      totalTickets,
      detectedCount,
      detectionRate: totalTickets > 0 ? (detectedCount / totalTickets) * 100 : 0,
      topPatterns,
    });
  }

  return stats.sort((a, b) => b.totalTickets - a.totalTickets);
}

function computeStatusBreakdown(items: TicketListItem[]): StatusBreakdown[] {
  const byStatus = new Map<string, TicketListItem[]>();

  for (const item of items) {
    const status = item.status || "Unknown";
    if (!byStatus.has(status)) {
      byStatus.set(status, []);
    }
    byStatus.get(status)!.push(item);
  }

  const totalTickets = items.length;
  const stats: StatusBreakdown[] = [];

  for (const [status, ticketList] of byStatus) {
    const count = ticketList.length;
    const totalPatterns = ticketList.reduce((sum, t) => sum + t.detectedCount, 0);

    stats.push({
      status,
      count,
      percentage: totalTickets > 0 ? (count / totalTickets) * 100 : 0,
      avgPatterns: count > 0 ? totalPatterns / count : 0,
    });
  }

  return stats.sort((a, b) => b.count - a.count);
}

function computeSourceBreakdown(items: TicketListItem[]): SourceBreakdown[] {
  const bySource = new Map<string, TicketListItem[]>();

  for (const item of items) {
    const source = item.source || "Unknown";
    if (!bySource.has(source)) {
      bySource.set(source, []);
    }
    bySource.get(source)!.push(item);
  }

  const totalTickets = items.length;
  const stats: SourceBreakdown[] = [];

  for (const [source, ticketList] of bySource) {
    const count = ticketList.length;
    const sev1Count = ticketList.filter((t) => t.isSev1).length;

    stats.push({
      source,
      count,
      percentage: totalTickets > 0 ? (count / totalTickets) * 100 : 0,
      sev1Count,
    });
  }

  return stats.sort((a, b) => b.count - a.count);
}

function computePriorityBreakdown(items: TicketListItem[]): PriorityBreakdown[] {
  const byPriority = new Map<string, TicketListItem[]>();

  for (const item of items) {
    const priority = item.priority || "Unknown";
    if (!byPriority.has(priority)) {
      byPriority.set(priority, []);
    }
    byPriority.get(priority)!.push(item);
  }

  const totalTickets = items.length;
  const stats: PriorityBreakdown[] = [];

  for (const [priority, ticketList] of byPriority) {
    const count = ticketList.length;
    const totalPatterns = ticketList.reduce((sum, t) => sum + t.detectedCount, 0);

    stats.push({
      priority,
      count,
      percentage: totalTickets > 0 ? (count / totalTickets) * 100 : 0,
      avgPatterns: count > 0 ? totalPatterns / count : 0,
    });
  }

  return stats.sort((a, b) => b.count - a.count);
}

function computePatternCoOccurrence(items: TicketListItem[]): PatternCoOccurrence[] {
  const coOccurrence: PatternCoOccurrence[] = [];

  for (let i = 0; i < OUR_PATTERNS.length; i++) {
    for (let j = i + 1; j < OUR_PATTERNS.length; j++) {
      const pattern1 = OUR_PATTERNS[i];
      const pattern2 = OUR_PATTERNS[j];

      const count = items.filter(
        (t) => t.predictedLabels.includes(pattern1) && t.predictedLabels.includes(pattern2)
      ).length;

      if (count > 0) {
        coOccurrence.push({ pattern1, pattern2, count });
      }
    }
  }

  return coOccurrence.sort((a, b) => b.count - a.count);
}

function computeTicketsByPatternCount(items: TicketListItem[]): { patternCount: number; ticketCount: number }[] {
  const byCount = new Map<number, number>();

  for (const item of items) {
    const count = item.detectedCount;
    byCount.set(count, (byCount.get(count) || 0) + 1);
  }

  const result: { patternCount: number; ticketCount: number }[] = [];
  for (const [patternCount, ticketCount] of byCount) {
    result.push({ patternCount, ticketCount });
  }

  return result.sort((a, b) => a.patternCount - b.patternCount);
}

// Helper to compute median from array of numbers
function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0
    ? sorted[mid]
    : (sorted[mid - 1] + sorted[mid]) / 2;
}

// Helper to compute average from array of numbers
function average(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

// Convert seconds to hours
function toHours(seconds: number | null): number | null {
  return seconds != null ? seconds / 3600 : null;
}

function computeHardMetricsSummary(
  items: TicketListItem[],
  csvMetrics: Map<number, CsvMetrics>,
  interactionMetrics: Map<number, TicketInteractionMetrics>
): HardMetricsSummary {
  const SECONDS_24H = 24 * 60 * 60;
  const SECONDS_7D = 7 * 24 * 60 * 60;

  // Collect metrics for items that have data
  const initialResponseTimes: number[] = [];
  const resolutionTimes: number[] = [];
  const timeAtL1: number[] = [];
  const timeAtL2: number[] = [];
  const timeOnHold: number[] = [];
  let fcrCount = 0;
  let escalatedCount = 0;
  let slowResponseCount = 0;
  let longResolutionCount = 0;
  let extendedHoldCount = 0;
  let largeGapsCount = 0;

  const totalInteractions: number[] = [];
  const aiInteractions: number[] = [];
  const employeeInteractions: number[] = [];
  let frustrationCount = 0;

  for (const item of items) {
    const csv = csvMetrics.get(item.ticketId);
    const interactions = interactionMetrics.get(item.ticketId);

    if (csv) {
      if (csv.initialResponseTime != null) {
        initialResponseTimes.push(csv.initialResponseTime);
        if (csv.initialResponseTime > SECONDS_24H) slowResponseCount++;
      }
      if (csv.resolutionTime != null) {
        resolutionTimes.push(csv.resolutionTime);
        if (csv.resolutionTime > SECONDS_7D) longResolutionCount++;
      }
      if (csv.timeSpentOpenL1 != null) timeAtL1.push(csv.timeSpentOpenL1);
      if (csv.timeSpentOpenL2 != null) timeAtL2.push(csv.timeSpentOpenL2);
      if (csv.timeSpentInHold != null) {
        timeOnHold.push(csv.timeSpentInHold);
        if (csv.timeSpentInHold > SECONDS_24H) extendedHoldCount++;
      }
      if (csv.fcr) fcrCount++;
      if (csv.levelSolved?.includes("L2") || csv.wasHandedToBu) escalatedCount++;
    }

    if (interactions) {
      totalInteractions.push(interactions.totalInteractions);
      aiInteractions.push(interactions.aiCount);
      employeeInteractions.push(interactions.employeeCount);
      if (interactions.gapsOver48h > 0) largeGapsCount++;
      if (interactions.hasCustomerFrustrationKeywords) frustrationCount++;
    }
  }

  const totalWithCsv = items.filter((i) => csvMetrics.has(i.ticketId)).length;

  return {
    avgInitialResponseHours: toHours(average(initialResponseTimes)),
    medianInitialResponseHours: toHours(median(initialResponseTimes)),
    avgResolutionHours: toHours(average(resolutionTimes)),
    medianResolutionHours: toHours(median(resolutionTimes)),
    avgTimeAtL1Hours: toHours(average(timeAtL1)),
    avgTimeAtL2Hours: toHours(average(timeAtL2)),
    avgTimeOnHoldHours: toHours(average(timeOnHold)),
    fcrRate: totalWithCsv > 0 ? (fcrCount / totalWithCsv) * 100 : 0,
    escalationRate: totalWithCsv > 0 ? (escalatedCount / totalWithCsv) * 100 : 0,
    slowResponseCount,
    longResolutionCount,
    extendedHoldCount,
    largeGapsCount,
    avgTotalInteractions: average(totalInteractions),
    avgAiInteractions: average(aiInteractions),
    avgEmployeeInteractions: average(employeeInteractions),
    ticketsWithFrustration: frustrationCount,
  };
}
