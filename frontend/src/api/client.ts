import type { components } from "./schema";

export type ApiErrorPayload = {
  code: string;
  message: string;
  details: Record<string, unknown>;
};

export type ApiResponseEnvelope<TData> = {
  data: TData | null;
  error: ApiErrorPayload | null;
  trace_id: string;
};

export type ApiSourceMode = "real" | "mock";

export type ApiQueryValue = string | number | boolean | null | undefined;

export type ApiRequestOptions = {
  body?: unknown;
  headers?: HeadersInit;
  method?: string;
  query?: Record<string, ApiQueryValue>;
  signal?: AbortSignal;
};

export type TaskSliceQuery = {
  persona?: string | null;
  price_band?: string | null;
  scenario?: string | null;
};

export type BattlefieldQuery = TaskSliceQuery & {
  include_all_relations?: boolean;
};

export type OverviewData = components["schemas"]["OverviewData"];
export type ProductProfileData = components["schemas"]["ProductProfileData"];
export type BattlefieldData = components["schemas"]["BattlefieldData"];
export type ReportData = components["schemas"]["ReportData"];
export type TraceData = components["schemas"]["TraceData"];

export interface ApiTransport {
  download?(path: string, options?: Omit<ApiRequestOptions, "body" | "method">): Promise<Blob>;
  request<TData>(path: string, options?: ApiRequestOptions): Promise<TData>;
}

type ApiClientErrorOptions = {
  code: string;
  details?: Record<string, unknown>;
  message: string;
  status?: number;
  traceId?: string;
};

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const INVALID_RESPONSE_CODE = "INVALID_API_RESPONSE";
const NETWORK_ERROR_CODE = "NETWORK_ERROR";

export class ApiClientError extends Error {
  readonly code: string;
  readonly details: Record<string, unknown>;
  readonly status?: number;
  readonly traceId?: string;

  constructor(options: ApiClientErrorOptions) {
    super(options.message);
    this.name = "ApiClientError";
    this.code = options.code;
    this.details = options.details ?? {};
    this.status = options.status;
    this.traceId = options.traceId;
  }
}

export function getDefaultApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL?.trim() || getLocalApiBaseUrl() || DEFAULT_API_BASE_URL;
}

export function getDefaultApiSourceMode(): ApiSourceMode {
  return import.meta.env.VITE_API_SOURCE === "mock" ? "mock" : "real";
}

export function parseApiEnvelope<TData>(
  payload: unknown,
  options: { status?: number } = {}
): ApiResponseEnvelope<TData> {
  if (!isRecord(payload)) {
    throw new ApiClientError({
      code: INVALID_RESPONSE_CODE,
      message: "后端响应不是有效对象。",
      status: options.status
    });
  }

  const traceId = payload.trace_id;
  if (typeof traceId !== "string" || traceId.length === 0) {
    throw new ApiClientError({
      code: INVALID_RESPONSE_CODE,
      message: "后端响应缺少 trace_id。",
      status: options.status
    });
  }

  const error = parseApiErrorPayload(payload.error);
  if (error) {
    throw new ApiClientError({
      code: error.code,
      details: error.details,
      message: error.message,
      status: options.status,
      traceId
    });
  }

  return {
    data: (payload.data ?? null) as TData | null,
    error: null,
    trace_id: traceId
  };
}

export class FetchApiTransport implements ApiTransport {
  private readonly baseUrl: string;
  private readonly fetcher: typeof fetch;

  constructor(options: { baseUrl?: string; fetcher?: typeof fetch } = {}) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl ?? getDefaultApiBaseUrl());
    this.fetcher = options.fetcher ?? globalThis.fetch.bind(globalThis);
  }

  async request<TData>(path: string, options: ApiRequestOptions = {}) {
    const url = buildApiUrl(this.baseUrl, path, options.query);
    let response: Response;

    try {
      response = await this.fetcher(url, {
        body: serializeBody(options.body),
        headers: buildHeaders(options.headers, options.body),
        method: options.method ?? "GET",
        signal: options.signal
      });
    } catch (error) {
      throw new ApiClientError({
        code: NETWORK_ERROR_CODE,
        details: {
          cause: error instanceof Error ? error.message : String(error),
          url
        },
        message: "无法连接后端服务，请确认后端已在 http://127.0.0.1:8000 启动。"
      });
    }

    const payload = await readJsonPayload(response);
    const envelope = parseApiEnvelope<TData>(payload, { status: response.status });
    return envelope.data as TData;
  }

  async download(path: string, options: Omit<ApiRequestOptions, "body" | "method"> = {}) {
    const url = buildApiUrl(this.baseUrl, path, options.query);
    let response: Response;

    try {
      response = await this.fetcher(url, {
        headers: buildHeaders(options.headers, undefined),
        method: "GET",
        signal: options.signal
      });
    } catch (error) {
      throw new ApiClientError({
        code: NETWORK_ERROR_CODE,
        details: {
          cause: error instanceof Error ? error.message : String(error),
          url
        },
        message: "无法连接后端服务，请确认后端已在 http://127.0.0.1:8000 启动。"
      });
    }

    if (!response.ok) {
      const payload = await readJsonPayload(response);
      parseApiEnvelope<never>(payload, { status: response.status });
    }

    return response.blob();
  }
}

export type MockApiHandler = (request: {
  body?: unknown;
  headers?: HeadersInit;
  method: string;
  path: string;
  query?: Record<string, ApiQueryValue>;
}) => Promise<unknown> | unknown;

export class MockApiTransport implements ApiTransport {
  private readonly handlers: Map<string, MockApiHandler>;

  constructor(handlers: Record<string, MockApiHandler>) {
    this.handlers = new Map(Object.entries(handlers));
  }

  async request<TData>(path: string, options: ApiRequestOptions = {}) {
    const method = (options.method ?? "GET").toUpperCase();
    const handler = this.handlers.get(createMockRouteKey(method, path));

    if (!handler) {
      throw new ApiClientError({
        code: "MOCK_HANDLER_NOT_FOUND",
        message: `未配置 ${method} ${path} 的开发数据入口。`,
        details: { method, path }
      });
    }

    const payload = await handler({
      body: options.body,
      headers: options.headers,
      method,
      path,
      query: options.query
    });
    const envelope = parseApiEnvelope<TData>(payload);
    return envelope.data as TData;
  }

  async download(path: string, options: Omit<ApiRequestOptions, "body" | "method"> = {}) {
    const method = "GET";
    const handler = this.handlers.get(createMockRouteKey(method, path));

    if (!handler) {
      throw new ApiClientError({
        code: "MOCK_HANDLER_NOT_FOUND",
        details: { method, path },
        message: `未配置 ${method} ${path} 的开发数据入口。`
      });
    }

    const payload = await handler({
      headers: options.headers,
      method,
      path,
      query: options.query
    });
    if (payload instanceof Blob) {
      return payload;
    }
    if (payload instanceof ArrayBuffer) {
      return new Blob([payload]);
    }
    if (typeof payload === "string") {
      return new Blob([payload]);
    }
    throw new ApiClientError({
      code: INVALID_RESPONSE_CODE,
      message: "后端下载响应不是有效文件。"
    });
  }
}

export class ApiClient {
  private readonly transport: ApiTransport;

  constructor(transport: ApiTransport = new FetchApiTransport()) {
    this.transport = transport;
  }

  request<TData>(path: string, options?: ApiRequestOptions) {
    return this.transport.request<TData>(path, options);
  }

  get<TData>(path: string, options?: Omit<ApiRequestOptions, "body" | "method">) {
    return this.request<TData>(path, { ...options, method: "GET" });
  }

  getOverview(taskId: string, query?: TaskSliceQuery) {
    return this.get<OverviewData>(taskApiPath(taskId, "/overview"), { query });
  }

  getBattlefield(taskId: string, query?: BattlefieldQuery) {
    return this.get<BattlefieldData>(taskApiPath(taskId, "/battlefield"), { query });
  }

  getProductProfile(taskId: string) {
    return this.get<ProductProfileData>(taskApiPath(taskId, "/profile"));
  }

  getReport(taskId: string) {
    return this.get<ReportData>(taskApiPath(taskId, "/report"));
  }

  getTrace(taskId: string) {
    return this.get<TraceData>(taskApiPath(taskId, "/trace"));
  }

  download(path: string, options?: Omit<ApiRequestOptions, "body" | "method">) {
    if (!this.transport.download) {
      throw new ApiClientError({
        code: "DOWNLOAD_UNAVAILABLE",
        message: "当前 API 传输层不支持文件下载。"
      });
    }
    return this.transport.download(path, options);
  }

  downloadWordReport(taskId: string) {
    return this.download(taskApiPath(taskId, "/report/docx"));
  }

  post<TData>(path: string, body?: unknown, options?: Omit<ApiRequestOptions, "body" | "method">) {
    return this.request<TData>(path, { ...options, body, method: "POST" });
  }
}

export function createApiClient(
  options: {
    mockTransport?: ApiTransport;
    realTransport?: ApiTransport;
    sourceMode?: ApiSourceMode;
  } = {}
) {
  const sourceMode = options.sourceMode ?? getDefaultApiSourceMode();

  if (sourceMode === "mock") {
    if (!options.mockTransport) {
      throw new ApiClientError({
        code: "MOCK_TRANSPORT_REQUIRED",
        message: "开发数据模式需要显式传入 mockTransport。"
      });
    }

    return new ApiClient(options.mockTransport);
  }

  return new ApiClient(options.realTransport ?? new FetchApiTransport());
}

function buildApiUrl(baseUrl: string, path: string, query?: Record<string, ApiQueryValue>) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${baseUrl}${normalizedPath}`);

  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== null && value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

function taskApiPath(taskId: string, suffix: string) {
  return `/tasks/${encodeURIComponent(taskId)}${suffix}`;
}

function buildHeaders(headers: HeadersInit | undefined, body: unknown) {
  const nextHeaders = new Headers(headers);

  if (body !== undefined && !(body instanceof FormData) && !nextHeaders.has("Content-Type")) {
    nextHeaders.set("Content-Type", "application/json");
  }

  return nextHeaders;
}

function createMockRouteKey(method: string, path: string) {
  return `${method.toUpperCase()} ${path}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeBaseUrl(baseUrl: string) {
  return baseUrl.replace(/\/+$/, "");
}

function getLocalApiBaseUrl() {
  if (typeof window === "undefined") {
    return null;
  }

  const { hostname, protocol } = window.location;
  if (protocol === "http:" && (hostname === "127.0.0.1" || hostname === "localhost")) {
    return `http://${hostname}:8000`;
  }

  return null;
}

function parseApiErrorPayload(value: unknown): ApiErrorPayload | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value) || typeof value.code !== "string" || typeof value.message !== "string") {
    throw new ApiClientError({
      code: INVALID_RESPONSE_CODE,
      message: "后端错误响应格式无效。"
    });
  }

  return {
    code: value.code,
    details: isRecord(value.details) ? value.details : {},
    message: value.message
  };
}

async function readJsonPayload(response: Response) {
  const text = await response.text();

  if (text.trim().length === 0) {
    throw new ApiClientError({
      code: "EMPTY_API_RESPONSE",
      message: "后端返回了空响应。",
      status: response.status
    });
  }

  try {
    return JSON.parse(text) as unknown;
  } catch (error) {
    throw new ApiClientError({
      code: INVALID_RESPONSE_CODE,
      details: { cause: error instanceof Error ? error.message : String(error) },
      message: "后端响应不是有效 JSON。",
      status: response.status
    });
  }
}

function serializeBody(body: unknown) {
  if (body === undefined) {
    return undefined;
  }

  if (body instanceof FormData || typeof body === "string") {
    return body;
  }

  return JSON.stringify(body);
}
