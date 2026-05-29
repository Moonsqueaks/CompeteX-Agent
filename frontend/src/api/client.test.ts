import { describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  FetchApiTransport,
  MockApiTransport,
  createApiClient,
  getDefaultApiBaseUrl,
  parseApiEnvelope
} from "./client";

describe("API Client", () => {
  it("解析后端成功响应并返回 data 与 trace_id", () => {
    const envelope = parseApiEnvelope<{ status: string }>({
      data: { status: "ok" },
      error: null,
      trace_id: "trace_001"
    });

    expect(envelope.data).toEqual({ status: "ok" });
    expect(envelope.error).toBeNull();
    expect(envelope.trace_id).toBe("trace_001");
  });

  it("解析后端错误响应并保留错误码", () => {
    expect(() =>
      parseApiEnvelope({
        data: null,
        error: {
          code: "TASK_NOT_FOUND",
          details: { task_id: "task_missing" },
          message: "任务不存在"
        },
        trace_id: "trace_404"
      })
    ).toThrow(ApiClientError);

    try {
      parseApiEnvelope({
        data: null,
        error: {
          code: "TASK_NOT_FOUND",
          details: { task_id: "task_missing" },
          message: "任务不存在"
        },
        trace_id: "trace_404"
      });
    } catch (error) {
      expect(error).toBeInstanceOf(ApiClientError);
      expect((error as ApiClientError).code).toBe("TASK_NOT_FOUND");
      expect((error as ApiClientError).traceId).toBe("trace_404");
      expect((error as ApiClientError).details).toEqual({ task_id: "task_missing" });
    }
  });

  it("真实请求入口通过统一响应结构读取数据", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: { task_id: "task_001" },
          error: null,
          trace_id: "trace_fetch"
        }),
        { status: 200 }
      )
    );
    const transport = new FetchApiTransport({ baseUrl: "http://127.0.0.1:8000", fetcher });

    const data = await transport.request<{ task_id: string }>("/tasks/task_001", {
      query: { include_trace: false }
    });

    expect(data).toEqual({ task_id: "task_001" });
    expect(fetcher).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/tasks/task_001?include_trace=false",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("默认 fetch 入口保留浏览器绑定上下文", async () => {
    const originalFetch = globalThis.fetch;
    const fetcher = vi.fn(function (this: typeof globalThis) {
      if (this !== globalThis) {
        throw new TypeError(
          "'fetch' called on an object that does not implement interface Window."
        );
      }

      return Promise.resolve(
        new Response(
          JSON.stringify({
            data: { ok: true },
            error: null,
            trace_id: "trace_bound_fetch"
          }),
          { status: 200 }
        )
      );
    }) as typeof fetch;

    globalThis.fetch = fetcher;

    try {
      const transport = new FetchApiTransport({ baseUrl: "http://127.0.0.1:8000" });

      await expect(transport.request<{ ok: boolean }>("/health")).resolves.toEqual({ ok: true });
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("本地开发默认 API 地址跟随页面主机名", () => {
    expect(getDefaultApiBaseUrl()).toBe(`http://${window.location.hostname}:8000`);
  });

  it("真实请求入口在网络失败时给出可诊断错误", async () => {
    const fetcher = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch"));
    const transport = new FetchApiTransport({ baseUrl: "http://127.0.0.1:8000", fetcher });

    await expect(transport.request("/tasks")).rejects.toMatchObject({
      code: "NETWORK_ERROR",
      details: {
        cause: "Failed to fetch",
        url: "http://127.0.0.1:8000/tasks"
      },
      message: "无法连接后端服务，请确认后端已在 http://127.0.0.1:8000 启动。"
    });
  });

  it("开发数据入口与真实请求入口可以显式切换且互不混用", async () => {
    const realTransport = {
      request: vi.fn().mockResolvedValue({ source: "real" })
    };
    const mockTransport = new MockApiTransport({
      "GET /health": () => ({
        data: { source: "mock" },
        error: null,
        trace_id: "trace_mock"
      })
    });
    const client = createApiClient({
      mockTransport,
      realTransport,
      sourceMode: "mock"
    });

    const data = await client.get<{ source: string }>("/health");

    expect(data).toEqual({ source: "mock" });
    expect(realTransport.request).not.toHaveBeenCalled();
  });
});
