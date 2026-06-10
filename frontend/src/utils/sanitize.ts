export function sanitizeTraceText(value: string) {
  return value
    .replace(/sk-[A-Za-z0-9_-]{8,}/g, "[已脱敏]")
    .replace(/AKIA[0-9A-Z]{16}/g, "[已脱敏]")
    .replace(/\b[A-Z][A-Z0-9_]*(API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\b/g, "[已脱敏]")
    .replace(/bearer\s+[A-Za-z0-9._-]+/gi, "Bearer [已脱敏]")
    .replace(
      /(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*([^\s,;]+)/gi,
      "凭据=[已脱敏]"
    )
    .replace(/(^|[^\d])1[3-9]\d{9}(?!\d)/g, "$1[已脱敏]")
    .replace(/\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b/g, "[已脱敏]")
    .replace(
      /\b(account[_-]?id|acct[_-]?id|open[_-]?id|openid|union[_-]?id|unionid|user[_-]?id|userid|uid)\b\s*[:=]\s*[A-Za-z0-9._:-]{4,}/gi,
      "账号=[已脱敏]"
    )
    .replace(/(账号|账户|用户ID|用户编号)\s*[:：=]\s*[\w.\-:]{4,}/g, "账号=[已脱敏]")
    .replace(/\b(address|addr)\b\s*[:=]\s*[^,;\n]+/gi, "地址=[已脱敏]")
    .replace(/(地址|住址|收货地址)\s*[:：=]\s*[^,，;；\n]+/g, "地址=[已脱敏]");
}

const INTERNAL_STANDARD_MARK_RE = /(?:按|按照|根据|基于)?\s*[12]\.0\s*标准[，,、]?\s*标记为/g;
const INTERNAL_STANDARD_REFERENCE_RE = /(?:按|按照|根据|基于)\s*[12]\.0\s*标准[，,、]?\s*/g;

export function sanitizeInternalStandardText(value: string) {
  return value
    .replace(INTERNAL_STANDARD_MARK_RE, "当前标记为")
    .replace(INTERNAL_STANDARD_REFERENCE_RE, "");
}

export function sanitizeInternalStandardCopy<T>(value: T): T {
  if (typeof value === "string") {
    return sanitizeInternalStandardText(value) as T;
  }

  if (Array.isArray(value)) {
    return value.map((item) => sanitizeInternalStandardCopy(item)) as T;
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, sanitizeInternalStandardCopy(item)])
    ) as T;
  }

  return value;
}

export function isSensitiveTraceKey(key: string | undefined) {
  return Boolean(
    key &&
    /^(api[_-]?key|apikey|token|secret|password|authorization|access[_-]?token|refresh[_-]?token|account[_-]?ids?|acct[_-]?ids?|open[_-]?ids?|openid|union[_-]?ids?|unionid|user[_-]?ids?|userid|uids?|phone|phone_number|phone_numbers|mobile|mobile_phone|address|addresses|addr)$/i.test(
      key
    )
  );
}
