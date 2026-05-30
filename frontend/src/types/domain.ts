import type { components } from "../api/schema";

export type IsoDateTime = string;

export type MockFixtureName = "overview" | "profile" | "battlefield" | "trace" | "report";

export type DevelopmentMockMeta = {
  data_kind: "development_mock";
  fixture_name: MockFixtureName;
  final_demo_data: false;
  generated_for: "frontend_f03";
  note: string;
  updated_at: IsoDateTime;
};

export type OverviewFixture = components["schemas"]["OverviewData"] & {
  mock_meta: DevelopmentMockMeta;
};

export type ProfileFixture = components["schemas"]["ProductProfileData"] & {
  mock_meta: DevelopmentMockMeta;
};

export type BattlefieldFixture = components["schemas"]["BattlefieldData"] & {
  mock_meta: DevelopmentMockMeta;
};

export type TraceFixture = components["schemas"]["TraceData"] & {
  mock_meta: DevelopmentMockMeta;
};

export type ReportFixture = components["schemas"]["ReportData"] & {
  mock_meta: DevelopmentMockMeta;
};

export type { components, operations, paths } from "../api/schema";
