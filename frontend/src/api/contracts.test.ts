import { describe, expectTypeOf, it } from "vitest";

import type { components, operations, paths } from "./schema";

type JsonContent<TResponse> = TResponse extends {
  content: { "application/json": infer TContent };
}
  ? TContent
  : never;

type SuccessResponse<TOperation, TStatus extends number = 200> = TOperation extends {
  responses: Record<TStatus, infer TResponse>;
}
  ? JsonContent<TResponse>
  : never;

type RequestBody<TOperation> = TOperation extends {
  requestBody: { content: { "application/json": infer TBody } };
}
  ? TBody
  : never;

describe("OpenAPI type contracts", () => {
  it("同步任务创建接口的请求和响应字段", () => {
    type CreateTaskOperation = operations["create_task_tasks_post"];
    type CreateTaskRequest = RequestBody<CreateTaskOperation>;
    type CreateTaskResponse = SuccessResponse<CreateTaskOperation, 201>;

    expectTypeOf<CreateTaskRequest>().toEqualTypeOf<components["schemas"]["TaskCreateRequest"]>();
    expectTypeOf<CreateTaskRequest["target_product_name"]>().toEqualTypeOf<
      string | null | undefined
    >();
    expectTypeOf<CreateTaskRequest["data_source_mode"]>().toEqualTypeOf<
      "demo_snapshot" | "snapshot_plus_live"
    >();
    expectTypeOf<CreateTaskResponse["trace_id"]>().toEqualTypeOf<string>();
    expectTypeOf<CreateTaskResponse["error"]>().toEqualTypeOf<
      components["schemas"]["ApiError"] | null | undefined
    >();
    expectTypeOf<CreateTaskResponse["data"]>().toEqualTypeOf<
      components["schemas"]["TaskCreateResponse"] | null | undefined
    >();
  });

  it("同步任务状态和业务页面接口字段", () => {
    type TaskStatus = SuccessResponse<operations["get_task_tasks__task_id__get"]>;
    type ProductProfile = SuccessResponse<
      operations["get_task_profile_tasks__task_id__profile_get"]
    >;
    type Battlefield = SuccessResponse<
      operations["get_task_battlefield_tasks__task_id__battlefield_get"]
    >;
    type Trace = SuccessResponse<operations["get_task_trace_tasks__task_id__trace_get"]>;
    type Report = SuccessResponse<operations["get_task_report_tasks__task_id__report_get"]>;

    expectTypeOf<TaskStatus["trace_id"]>().toEqualTypeOf<string>();
    expectTypeOf<TaskStatus["error"]>().toEqualTypeOf<
      components["schemas"]["ApiError"] | null | undefined
    >();
    expectTypeOf<TaskStatus["data"]>().toEqualTypeOf<
      components["schemas"]["TaskStatusResponse"] | null | undefined
    >();
    expectTypeOf<ProductProfile["data"]>().toEqualTypeOf<
      components["schemas"]["ProductProfileData"] | null | undefined
    >();
    expectTypeOf<Battlefield["data"]>().toEqualTypeOf<
      components["schemas"]["BattlefieldData"] | null | undefined
    >();
    expectTypeOf<Trace["data"]>().toEqualTypeOf<
      components["schemas"]["TraceData"] | null | undefined
    >();
    expectTypeOf<Report["data"]>().toEqualTypeOf<
      components["schemas"]["ReportData"] | null | undefined
    >();
  });

  it("同步路由路径和人工反馈接口字段", () => {
    type FeedbackOperation = operations["submit_task_feedback_tasks__task_id__feedback_post"];
    type FeedbackRequest = RequestBody<FeedbackOperation>;
    type FeedbackResponse = SuccessResponse<FeedbackOperation, 201>;

    expectTypeOf<paths>().toHaveProperty("/tasks");
    expectTypeOf<paths>().toHaveProperty("/health");
    expectTypeOf<FeedbackRequest>().toEqualTypeOf<
      components["schemas"]["HumanFeedbackCreateRequest"]
    >();
    expectTypeOf<FeedbackResponse["trace_id"]>().toEqualTypeOf<string>();
    expectTypeOf<FeedbackResponse["error"]>().toEqualTypeOf<
      components["schemas"]["ApiError"] | null | undefined
    >();
    expectTypeOf<FeedbackResponse["data"]>().toEqualTypeOf<
      components["schemas"]["HumanFeedbackCreateResponse"] | null | undefined
    >();
  });
});
