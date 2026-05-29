import { describe, expect, it } from "vitest";

import { ApiClientError } from "./client";
import {
  createErrorState,
  createIdleState,
  createLoadingState,
  createRetryingState,
  createSuccessState,
  isEmptyApiData
} from "./state";

describe("API request state", () => {
  it("统一表达加载状态并保留已有数据", () => {
    const previousState = createSuccessState(["task_001"], "trace_existing");

    const state = createLoadingState(previousState);

    expect(state.status).toBe("loading");
    expect(state.data).toEqual(["task_001"]);
    expect(state.error).toBeNull();
    expect(state.traceId).toBe("trace_existing");
  });

  it("统一表达错误状态并保留错误码与重试能力", () => {
    const previousState = createIdleState<{ task_id: string }>();
    const error = new ApiClientError({
      code: "TASK_NOT_FOUND",
      message: "任务不存在",
      traceId: "trace_error"
    });

    const state = createErrorState(error, previousState);

    expect(state.status).toBe("error");
    expect(state.canRetry).toBe(true);
    expect(state.error?.code).toBe("TASK_NOT_FOUND");
    expect(state.traceId).toBe("trace_error");
  });

  it("统一表达空数据和重试状态", () => {
    const emptyState = createSuccessState([], "trace_empty");
    const retryingState = createRetryingState(emptyState);

    expect(isEmptyApiData([])).toBe(true);
    expect(emptyState.status).toBe("empty");
    expect(retryingState.status).toBe("retrying");
    expect(retryingState.retryCount).toBe(1);
    expect(retryingState.canRetry).toBe(false);
  });
});
