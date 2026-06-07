import { useQuery } from "@tanstack/react-query";

import type { ApiClient, components } from "../api";

type BattlefieldData = components["schemas"]["BattlefieldData"];
type BattlefieldSliceSelection = components["schemas"]["BattlefieldSliceSelection"];
type TaskApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download" | "getBattlefield" | "getOverview">>;

type BattlefieldQuery = {
  include_all_relations?: boolean;
  persona?: string;
  price_band?: string;
  scenario?: string;
};

export function useBattlefield(
  apiClient: TaskApiClient,
  taskId: string | null,
  selectedSlice: BattlefieldSliceSelection,
  includeAllRelations: boolean
) {
  return useQuery({
    enabled: Boolean(taskId),
    placeholderData: (previousData) => previousData,
    queryFn: () =>
      getBattlefieldData(apiClient, taskId ?? "", {
        ...compactSliceQuery(selectedSlice),
        ...(includeAllRelations ? { include_all_relations: true } : {})
      }),
    queryKey: [
      "battlefield",
      taskId,
      selectedSlice.price_band,
      selectedSlice.persona,
      selectedSlice.scenario,
      includeAllRelations
    ],
    retry: false
  });
}

function getBattlefieldData(apiClient: TaskApiClient, taskId: string, query: BattlefieldQuery = {}) {
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
