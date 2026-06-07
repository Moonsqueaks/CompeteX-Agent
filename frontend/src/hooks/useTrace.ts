import { useQuery } from "@tanstack/react-query";

import type { ApiClient, components } from "../api";

type TaskStatus = components["schemas"]["TaskStatus"];
type TaskStatusResponse = components["schemas"]["TaskStatusResponse"];
type TraceData = components["schemas"]["TraceData"];
type TaskApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download" | "getBattlefield" | "getOverview">>;

const TASK_STATUS_REFETCH_INTERVAL_MS = 1000;
const RUNNING_TASK_STATUSES = new Set<TaskStatus>([
  "created",
  "collecting",
  "analyzing",
  "reviewing",
  "writing"
]);

export function useTaskStatus(apiClient: TaskApiClient, taskId: string | null) {
  return useQuery({
    enabled: Boolean(taskId),
    queryFn: () => apiClient.get<TaskStatusResponse>(`/tasks/${encodeURIComponent(taskId ?? "")}`),
    queryKey: ["task-status", taskId],
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && isRunningTaskStatus(status) ? TASK_STATUS_REFETCH_INTERVAL_MS : false;
    },
    retry: false
  });
}

export function useTrace(
  apiClient: TaskApiClient,
  taskId: string | null,
  options: { isPolling: boolean }
) {
  return useQuery({
    enabled: Boolean(taskId),
    queryFn: () => apiClient.get<TraceData>(`/tasks/${encodeURIComponent(taskId ?? "")}/trace`),
    queryKey: ["task-trace", taskId],
    refetchInterval: () => (options.isPolling ? TASK_STATUS_REFETCH_INTERVAL_MS : false),
    retry: false
  });
}

export function isRunningTaskStatus(status: TaskStatus) {
  return RUNNING_TASK_STATUSES.has(status);
}
