export const EMPTY_VALUE_TEXT = "暂无可靠数据";

export function formatNullable(value: string | null | undefined, emptyText = EMPTY_VALUE_TEXT) {
  return value && value.trim().length > 0 ? value : emptyText;
}

export function formatPrice(
  value: number | null | undefined,
  currency: string,
  emptyText = EMPTY_VALUE_TEXT
) {
  if (value === null || value === undefined) {
    return emptyText;
  }

  return `${currency} ${value.toFixed(0)}`;
}

export function formatScore(value: number) {
  if (value >= 0 && value <= 1) {
    return `${Math.round(value * 100)}%`;
  }

  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

export function formatDuration(durationMs: number | null | undefined, emptyText = EMPTY_VALUE_TEXT) {
  if (durationMs === null || durationMs === undefined) {
    return emptyText;
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  return `${(durationMs / 1000).toFixed(1)} s`;
}

export function formatDateTime(
  value: string | null | undefined,
  options: {
    emptyText?: string;
    fallback?: (value: string) => string;
    style?: "compact" | "localized";
  } = {}
) {
  const { emptyText = EMPTY_VALUE_TEXT, fallback, style = "compact" } = options;

  if (!value) {
    return emptyText;
  }

  if (style === "localized") {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return fallback ? fallback(value) : value;
    }

    return new Intl.DateTimeFormat("zh-CN", {
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      month: "2-digit",
      year: "numeric"
    }).format(date);
  }

  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/);
  if (match) {
    return `${match[1]}/${match[2]}/${match[3]} ${match[4]}:${match[5]}`;
  }

  return fallback ? fallback(value) : value;
}

export function isInternalIdentifier(value: string) {
  return /^(task|run|edge|claim|ev|prod|ri|review|msg|tool|trace)_[A-Za-z0-9_]+$/.test(value);
}

export function isRecordValue(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function stringValue(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}
