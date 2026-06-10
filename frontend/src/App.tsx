import "@xyflow/react/dist/style.css";
import "./App.css";

import { useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import type { ApiClient } from "./api";
import { createApiClient } from "./api";
import { AppProviders } from "./app/AppProviders";
import { AppShell } from "./app/AppShell";
import { getRoute, navigationEmitter } from "./app/routes";
import { BattlefieldPage } from "./pages/BattlefieldPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ReportPage, type CompletedReportCache } from "./pages/ReportPage";
import { TaskInputPage } from "./pages/TaskInputPage";
import { TracePage } from "./pages/TracePage";

type TaskApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download" | "getBattlefield" | "getOverview">>;

type AppProps = {
  apiClient?: TaskApiClient;
};

export default function App({ apiClient }: AppProps = {}) {
  const taskApiClient = useMemo(() => apiClient ?? createApiClient(), [apiClient]);
  const [completedReportCache] = useState<CompletedReportCache>(() => new Map());
  const [analysisArtifactRevisions, setAnalysisArtifactRevisions] = useState<
    Record<string, number>
  >({});

  return (
    <AppProviders>
      <BrowserRouter>
        <AppRoutes
          analysisArtifactRevisions={analysisArtifactRevisions}
          apiClient={taskApiClient}
          completedReportCache={completedReportCache}
          onAnalysisArtifactsChanged={(changedTaskId) => {
            completedReportCache.delete(changedTaskId);
            setAnalysisArtifactRevisions((current) => ({
              ...current,
              [changedTaskId]: (current[changedTaskId] ?? 0) + 1
            }));
          }}
        />
      </BrowserRouter>
    </AppProviders>
  );
}

function AppRoutes({
  analysisArtifactRevisions,
  apiClient,
  completedReportCache,
  onAnalysisArtifactsChanged
}: {
  analysisArtifactRevisions: Record<string, number>;
  apiClient: TaskApiClient;
  completedReportCache: CompletedReportCache;
  onAnalysisArtifactsChanged: (taskId: string) => void;
}) {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const handleNavigation = (event: Event) => {
      const { detail } = event as CustomEvent<string>;
      navigate(detail);
    };

    navigationEmitter.addEventListener("navigate", handleNavigation);
    return () => navigationEmitter.removeEventListener("navigate", handleNavigation);
  }, [navigate]);

  const currentRoute = getRoute(location.pathname);
  const currentTaskId = getTaskIdFromSearch(location.search);

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          path="/"
          element={
            <TaskInputPage apiClient={apiClient} route={currentRoute} taskId={currentTaskId} />
          }
        />
        <Route
          path="/overview"
          element={
            <OverviewPage apiClient={apiClient} route={currentRoute} taskId={currentTaskId} />
          }
        />
        <Route
          path="/profile"
          element={
            <ProfilePage
              apiClient={apiClient}
              onAnalysisArtifactsChanged={onAnalysisArtifactsChanged}
              route={currentRoute}
              taskId={currentTaskId}
            />
          }
        />
        <Route
          path="/battlefield"
          element={
            <BattlefieldPage apiClient={apiClient} route={currentRoute} taskId={currentTaskId} />
          }
        />
        <Route
          path="/report"
          element={
            <ReportPage
              apiClient={apiClient}
              analysisArtifactsRevision={
                currentTaskId ? (analysisArtifactRevisions[currentTaskId] ?? 0) : 0
              }
              completedReportCache={completedReportCache}
              route={currentRoute}
              taskId={currentTaskId}
            />
          }
        />
        <Route
          path="/trace"
          element={<TracePage apiClient={apiClient} route={currentRoute} taskId={currentTaskId} />}
        />
        <Route path="*" element={<Navigate replace to="/" />} />
      </Route>
    </Routes>
  );
}

function getTaskIdFromSearch(search: string) {
  const taskId = new URLSearchParams(search).get("task_id")?.trim();
  return taskId && taskId.length > 0 ? taskId : null;
}
