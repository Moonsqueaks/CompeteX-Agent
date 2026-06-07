import { useQuery } from "@tanstack/react-query";

import type { ApiClient, components } from "../api";

type BattlefieldData = components["schemas"]["BattlefieldData"];
type BattlefieldSliceSelection = components["schemas"]["BattlefieldSliceSelection"];
type OverviewData = components["schemas"]["OverviewData"];
type TaskApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download" | "getBattlefield" | "getOverview">>;

export function useOverview(
  apiClient: TaskApiClient,
  taskId: string | null,
  selectedSlice: BattlefieldSliceSelection
) {
  return useQuery({
    enabled: Boolean(taskId),
    queryFn: () => getOverviewData(apiClient, taskId ?? "", selectedSlice),
    queryKey: [
      "task-overview",
      taskId,
      selectedSlice.price_band,
      selectedSlice.persona,
      selectedSlice.scenario
    ],
    retry: false
  });
}

export function useOverviewSliceOptions(apiClient: TaskApiClient, taskId: string | null) {
  return useQuery({
    enabled: Boolean(taskId),
    queryFn: () => getBattlefieldData(apiClient, taskId ?? "", { include_all_relations: true }),
    queryKey: ["overview-slice-options", taskId],
    retry: false
  });
}

function getOverviewData(
  apiClient: TaskApiClient,
  taskId: string,
  selection: BattlefieldSliceSelection
) {
  const query = compactSliceQuery(selection);
  if (apiClient.getOverview) {
    return apiClient.getOverview(taskId, query);
  }

  return apiClient.get<OverviewData>(
    `/tasks/${encodeURIComponent(taskId)}/overview`,
    Object.keys(query).length > 0 ? { query } : undefined
  );
}

function getBattlefieldData(
  apiClient: TaskApiClient,
  taskId: string,
  query: {
    include_all_relations?: boolean;
    persona?: string;
    price_band?: string;
    scenario?: string;
  } = {}
) {
  if (apiClient.getBattlefield) {
    return apiClient.getBattlefield(taskId, query);
  }

  return apiClient.get<BattlefieldData>(`/tasks/${encodeURIComponent(taskId)}/battlefield`, {
    query
  });
}

function compactSliceQuery(selection: BattlefieldSliceSelection) {
  const query: Record<string, string> = {};
  if (selection.price_band) {
    query.price_band = selection.price_band;
  }
  if (selection.persona) {
    query.persona = selection.persona;
  }
  if (selection.scenario) {
    query.scenario = selection.scenario;
  }
  return query;
}
