import type { DevelopmentMockMeta, MockFixtureName } from "../types";

// F03 fixtures are only for frontend development and component tests, not final demo data.
export function createDevelopmentMockMeta(fixture_name: MockFixtureName): DevelopmentMockMeta {
  return {
    data_kind: "development_mock",
    final_demo_data: false,
    fixture_name,
    generated_for: "frontend_f03",
    note: "仅用于前端组件开发，非最终演示数据。",
    updated_at: "2026-05-26T09:30:00+08:00"
  };
}
