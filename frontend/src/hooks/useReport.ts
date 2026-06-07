import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import type { ApiClient, components } from "../api";

type ReportData = components["schemas"]["ReportData"];
type TaskApiClient = Pick<ApiClient, "get" | "post"> & Partial<Pick<ApiClient, "download">>;

const REPORT_CACHE_TIME_MS = 10 * 60 * 1000;

export type CompletedReportCache = Map<string, ReportData>;

export function useReport(
  apiClient: TaskApiClient,
  taskId: string | null,
  completedReportCache: CompletedReportCache
) {
  const cachedReport = taskId ? completedReportCache.get(taskId) : undefined;
  const reportQueryKey = useMemo(() => ["report", taskId] as const, [taskId]);
  const reportQuery = useQuery({
    enabled: Boolean(taskId) && !cachedReport,
    gcTime: REPORT_CACHE_TIME_MS,
    initialData: cachedReport,
    queryFn: () => apiClient.get<ReportData>(`/tasks/${encodeURIComponent(taskId ?? "")}/report`),
    queryKey: reportQueryKey,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
    retry: false,
    staleTime: Number.POSITIVE_INFINITY
  });

  return { cachedReport, reportQuery, reportQueryKey };
}
