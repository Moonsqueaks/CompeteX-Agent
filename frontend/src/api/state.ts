import { ApiClientError } from "./client";

export type ApiRequestStatus = "idle" | "loading" | "success" | "empty" | "error" | "retrying";

export type ApiRequestState<TData> = {
  canRetry: boolean;
  data: TData | null;
  error: ApiClientError | null;
  retryCount: number;
  status: ApiRequestStatus;
  traceId?: string;
};

export function createIdleState<TData>(): ApiRequestState<TData> {
  return {
    canRetry: false,
    data: null,
    error: null,
    retryCount: 0,
    status: "idle"
  };
}

export function createLoadingState<TData>(
  previousState: ApiRequestState<TData> = createIdleState<TData>()
): ApiRequestState<TData> {
  return {
    canRetry: false,
    data: previousState.data,
    error: null,
    retryCount: previousState.retryCount,
    status: "loading",
    traceId: previousState.traceId
  };
}

export function createSuccessState<TData>(data: TData, traceId?: string): ApiRequestState<TData> {
  if (isEmptyApiData(data)) {
    return {
      canRetry: false,
      data: null,
      error: null,
      retryCount: 0,
      status: "empty",
      traceId
    };
  }

  return {
    canRetry: false,
    data,
    error: null,
    retryCount: 0,
    status: "success",
    traceId
  };
}

export function createErrorState<TData>(
  error: unknown,
  previousState: ApiRequestState<TData> = createIdleState<TData>()
): ApiRequestState<TData> {
  const apiError = toApiClientError(error);

  return {
    canRetry: true,
    data: previousState.data,
    error: apiError,
    retryCount: previousState.retryCount,
    status: "error",
    traceId: apiError.traceId ?? previousState.traceId
  };
}

export function createRetryingState<TData>(
  previousState: ApiRequestState<TData>
): ApiRequestState<TData> {
  return {
    canRetry: false,
    data: previousState.data,
    error: null,
    retryCount: previousState.retryCount + 1,
    status: "retrying",
    traceId: previousState.traceId
  };
}

export function isEmptyApiData(data: unknown) {
  if (data === null || data === undefined) {
    return true;
  }

  if (Array.isArray(data)) {
    return data.length === 0;
  }

  if (typeof data === "object") {
    return Object.keys(data).length === 0;
  }

  return false;
}

function toApiClientError(error: unknown) {
  if (error instanceof ApiClientError) {
    return error;
  }

  return new ApiClientError({
    code: "CLIENT_ERROR",
    details: { cause: error instanceof Error ? error.message : String(error) },
    message: "请求处理失败。"
  });
}
