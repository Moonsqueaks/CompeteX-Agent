export const EMPTY_VALUE_TEXT = "暂无可靠数据";

const BEIJING_TIME_ZONE = "Asia/Shanghai";

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

export function formatDuration(
  durationMs: number | null | undefined,
  emptyText = EMPTY_VALUE_TEXT
) {
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

  const date = parseBackendDateTime(value);
  if (!Number.isNaN(date.getTime())) {
    return formatBeijingDateTime(date, style);
  }

  return fallback ? fallback(value) : value;
}

function parseBackendDateTime(value: string) {
  const trimmed = value.trim();
  const normalizedIso = trimmed.replace(/^(\d{4}-\d{2}-\d{2})\s/, "$1T");
  const hasExplicitTimezone = /(?:z|[+-]\d{2}:?\d{2})$/i.test(normalizedIso);
  const looksLikeIsoDateTime = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?$/.test(
    normalizedIso
  );

  if (looksLikeIsoDateTime && !hasExplicitTimezone) {
    return new Date(`${normalizedIso}Z`);
  }

  return new Date(trimmed);
}

function formatBeijingDateTime(date: Date, style: "compact" | "localized") {
  const formatter = new Intl.DateTimeFormat("zh-CN", {
    day: "2-digit",
    hour: "2-digit",
    hour12: false,
    minute: "2-digit",
    month: "2-digit",
    timeZone: BEIJING_TIME_ZONE,
    year: "numeric"
  });
  const parts = Object.fromEntries(
    formatter.formatToParts(date).map((part) => [part.type, part.value])
  );
  const text = `${parts.year}/${parts.month}/${parts.day} ${parts.hour}:${parts.minute}`;
  return style === "localized" ? text : text;
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
