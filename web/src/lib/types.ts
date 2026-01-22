export const OUR_PATTERNS = [
  "AI_QUALITY_FAILURES",
  "AI_WALL_LOOPING",
  "IGNORING_CONTEXT",
  "RESPONSE_DELAYS",
  "PREMATURE_CLOSURE",
  "P1_SEV1_MISHANDLING",
] as const;

export type PatternId = (typeof OUR_PATTERNS)[number];

export type TicketSummaryRow = Record<string, string>;

export type TicketListItem = {
  ticketId: number;
  vertical: string;
  product: string;
  status: string;
  priority: string;
  isSev1: boolean;
  source: string;
  predictedLabels: PatternId[];
  detectedCount: number;
  row: TicketSummaryRow;
};

export type TicketPatternBlock = {
  detected: boolean;
  reasoning: string;
  evidence: string[];
};

export type TicketResultJson = Record<string, unknown> & {
  _model?: string;
  _ticket_id?: number;
} & Partial<Record<PatternId, TicketPatternBlock>>;

export type TranscriptEvent = {
  ts: string;
  text: string;
};

// Hard metrics from poc_csv_metrics.csv (timing/resolution data)
export type CsvMetrics = {
  ticketId: number;
  initialResponseTime: number | null; // seconds
  resolutionTime: number | null; // seconds
  timeSpentInNew: number | null;
  timeSpentInOpen: number | null;
  timeSpentInHold: number | null;
  timeSpentInPending: number | null;
  timeSpentOpenL1: number | null; // seconds at L1
  timeSpentOpenL2: number | null; // seconds at L2
  timeSpentOpenUnassigned: number | null;
  levelSolved: string | null; // "L1 Agent" | "L2 Agent" etc.
  wasHandedToBu: boolean;
  fcr: boolean;
  fcrPlus: boolean;
  l2Fcr: boolean;
  ticketCreated: string | null;
  ticketSolved: string | null;
  ticketClosed: string | null;
  npsScore: number | null;
  csatScore: number | null;
};

// Interaction metrics from poc_ticket_metrics.csv
export type TicketInteractionMetrics = {
  ticketId: number;
  aiCount: number;
  employeeCount: number;
  customerCount: number;
  totalInteractions: number;
  atlasCount: number;
  hermesCount: number;
  timeToFirstHumanSeconds: number | null;
  timeToFirstAiSeconds: number | null;
  maxGapSeconds: number | null;
  gapsOver24h: number;
  gapsOver48h: number;
  maxConsecutiveAi: number;
  aiOnlyBeforeHuman: boolean;
  hasCustomerFrustrationKeywords: boolean;
  hasPreviousTicketReference: boolean;
  hasRepeatedInfoRequest: boolean;
};

// Computed flags for visual indicators
export type DerivedMetricFlags = {
  slowInitialResponse: boolean; // > 24 hours
  longResolution: boolean; // > 7 days
  extendedHold: boolean; // > 24 hours total hold time
  wasEscalated: boolean; // L2 or handed to BU
  hasLargeGaps: boolean; // any gaps > 48h
};

// Combined metrics for a single ticket
export type TicketHardMetrics = {
  csv: CsvMetrics | null;
  interactions: TicketInteractionMetrics | null;
  flags: DerivedMetricFlags;
};

export type TicketDetail = {
  ticketId: number;
  dataset: string;
  summary?: TicketSummaryRow;
  result?: TicketResultJson;
  transcript?: TranscriptEvent[];
  hardMetrics?: TicketHardMetrics;
};
