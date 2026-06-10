import { describe, expect, it, vi } from "vitest";

import {
  ApiClient,
  ApiClientError,
  FetchApiTransport,
  MockApiTransport,
  createApiClient,
  getDefaultApiBaseUrl,
  parseApiEnvelope
} from "./client";
import type { ApiTransport } from "./client";

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

  it("清理内部标准文案但保留正常版本号", () => {
    const internalStandardCopy = "按 " + "2." + "0 标准";
    const envelope = parseApiEnvelope<{ model: string; reason: string }>({
      data: {
        model: "Doubao-Seed-2.0-lite",
        reason: `DeepSeek 在当前切片关系分为 0.79，${internalStandardCopy}标记为中威胁。`
      },
      error: null,
      trace_id: "trace_sanitized_copy"
    });

    expect(envelope.data?.reason).toBe("DeepSeek 在当前切片关系分为 0.79，当前标记为中威胁。");
    expect(envelope.data?.model).toBe("Doubao-Seed-2.0-lite");
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

  it("2.0 总览请求封装能处理成功响应和切片参数", async () => {
    const client = new ApiClient(
      new MockApiTransport({
        "GET /tasks/task_overview/overview": ({ query }) => {
          expect(query).toEqual({
            persona: "多猫家庭",
            price_band: "1500-2000",
            scenario: null
          });
          return {
            data: {
              action_recommendations: [],
              analysis_scope: {
                category: "smart_pet_hardware",
                data_source_statement: "基于用户提供的脱敏 SKU 快照。",
                sku_count: 3,
                snapshot_time_range: "2026-05-27",
                source_modes: ["demo_snapshot"],
                subcategory: "automatic_litter_box"
              },
              current_slice: {
                persona: "多猫家庭",
                price_band: "1500-2000",
                scenario: null
              },
              decision_usability: {
                reason: "证据基本可复核。",
                status: "ready_for_initial_decision"
              },
              generated_at: "2026-05-30T08:00:00Z",
              judgment_strength: {
                reason: "关键结论有证据链。",
                status: "directional_judgment"
              },
              key_competitors: [],
              one_sentence_judgment: {
                content: "目标产品在当前切片下需要重点关注直接竞品。",
                drilldown_refs: [],
                evidence_ids: ["ev_overview"],
                risk_flags: [],
                trace_refs: ["claim:claim_overview"]
              },
              opportunities: [],
              overview_id: "overview_task_overview",
              risk_points: [],
              status_reasons: ["证据来自本地快照。"],
              task_id: "task_overview"
            },
            error: null,
            trace_id: "trace_overview"
          };
        }
      })
    );

    await expect(
      client.getOverview("task_overview", {
        persona: "多猫家庭",
        price_band: "1500-2000",
        scenario: null
      })
    ).resolves.toMatchObject({
      overview_id: "overview_task_overview",
      task_id: "task_overview"
    });
  });

  it("2.0 总览请求封装能处理标准错误响应", async () => {
    const client = new ApiClient(
      new MockApiTransport({
        "GET /tasks/task_overview/overview": () => ({
          data: null,
          error: {
            code: "OVERVIEW_NOT_READY",
            details: { task_id: "task_overview" },
            message: "总览尚未生成"
          },
          trace_id: "trace_overview_error"
        })
      })
    );

    await expect(client.getOverview("task_overview")).rejects.toMatchObject({
      code: "OVERVIEW_NOT_READY",
      details: { task_id: "task_overview" },
      traceId: "trace_overview_error"
    });
  });

  it("2.0 任务数据封装使用受控路径并支持 Word 下载", async () => {
    const wordBlob = new Blob(["docx"]);
    const transport = {
      download: vi.fn().mockResolvedValue(wordBlob),
      request: vi.fn().mockResolvedValue({})
    } as unknown as ApiTransport;
    const client = new ApiClient(transport);

    await client.getBattlefield("task 2.0", { include_all_relations: true });
    await client.getProductProfile("task 2.0");
    await client.getReport("task 2.0");
    await client.getTrace("task 2.0");
    await expect(client.downloadWordReport("task 2.0")).resolves.toBe(wordBlob);

    expect(transport.request).toHaveBeenNthCalledWith(1, "/tasks/task%202.0/battlefield", {
      method: "GET",
      query: { include_all_relations: true }
    });
    expect(transport.request).toHaveBeenNthCalledWith(2, "/tasks/task%202.0/profile", {
      method: "GET"
    });
    expect(transport.request).toHaveBeenNthCalledWith(3, "/tasks/task%202.0/report", {
      method: "GET"
    });
    expect(transport.request).toHaveBeenNthCalledWith(4, "/tasks/task%202.0/trace", {
      method: "GET"
    });
    expect(transport.download).toHaveBeenCalledWith("/tasks/task%202.0/report/docx", undefined);
  });
});
