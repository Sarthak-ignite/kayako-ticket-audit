/**
 * Utility functions for formatting metric values for display
 */

/**
 * Convert seconds to human-readable duration
 * Examples: "2d 4h", "45m", "< 1m"
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null || isNaN(seconds)) return "-";
  if (seconds < 0) return "-";

  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    const remainingHours = hours % 24;
    return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
  }
  if (hours > 0) {
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  }
  if (minutes > 0) {
    return `${minutes}m`;
  }
  return "< 1m";
}

/**
 * Format a boolean as Yes/No
 */
export function formatBoolean(value: boolean | null | undefined): string {
  if (value == null) return "-";
  return value ? "Yes" : "No";
}

/**
 * Format a number with optional decimal places
 */
export function formatNumber(
  value: number | null | undefined,
  decimals: number = 0
): string {
  if (value == null || isNaN(value)) return "-";
  return value.toFixed(decimals);
}

/**
 * Format a date string to a readable format
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

/**
 * Get severity class based on threshold comparison
 */
export type SeverityLevel = "normal" | "warning" | "critical";

export function getSeverityClass(
  value: number | null,
  warningThreshold: number,
  criticalThreshold: number
): SeverityLevel {
  if (value == null) return "normal";
  if (value >= criticalThreshold) return "critical";
  if (value >= warningThreshold) return "warning";
  return "normal";
}

/**
 * Thresholds for metric severity (in seconds)
 */
export const THRESHOLDS = {
  INITIAL_RESPONSE_WARNING: 12 * 60 * 60, // 12 hours
  INITIAL_RESPONSE_CRITICAL: 24 * 60 * 60, // 24 hours
  RESOLUTION_WARNING: 3 * 24 * 60 * 60, // 3 days
  RESOLUTION_CRITICAL: 7 * 24 * 60 * 60, // 7 days
  HOLD_WARNING: 12 * 60 * 60, // 12 hours
  HOLD_CRITICAL: 24 * 60 * 60, // 24 hours
  GAP_WARNING: 24 * 60 * 60, // 24 hours
  GAP_CRITICAL: 48 * 60 * 60, // 48 hours
};
