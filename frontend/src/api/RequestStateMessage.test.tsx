import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiClientError } from "./client";
import { RequestStateMessage } from "./RequestStateMessage";
import { createErrorState } from "./state";

describe("RequestStateMessage", () => {
  it("展示 API 错误状态而不是静默失败", () => {
    const retry = vi.fn();
    const state = createErrorState(
      new ApiClientError({
        code: "TASK_NOT_FOUND",
        message: "任务不存在",
        traceId: "trace_error"
      })
    );

    render(<RequestStateMessage onRetry={retry} state={state} />);

    expect(screen.getByRole("alert")).toHaveTextContent("请求失败");
    expect(screen.getByRole("alert")).toHaveTextContent("任务不存在");
    expect(screen.getByRole("alert")).toHaveTextContent("错误码：TASK_NOT_FOUND");
    expect(screen.getByRole("alert")).toHaveTextContent("追踪编号：trace_error");

    fireEvent.click(screen.getByRole("button", { name: "重试" }));
    expect(retry).toHaveBeenCalledTimes(1);
  });
});
