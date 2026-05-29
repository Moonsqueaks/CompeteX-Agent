import type { ApiRequestState } from "./state";

type RequestStateMessageProps<TData> = {
  className?: string;
  emptyText?: string;
  loadingText?: string;
  onRetry?: () => void;
  state: ApiRequestState<TData>;
};

export function RequestStateMessage<TData>({
  className,
  emptyText = "暂无可展示数据",
  loadingText = "正在加载数据",
  onRetry,
  state
}: RequestStateMessageProps<TData>) {
  if (state.status === "loading" || state.status === "retrying") {
    return (
      <div className={className} role="status">
        {state.status === "retrying" ? "正在重新请求数据" : loadingText}
      </div>
    );
  }

  if (state.status === "empty") {
    return (
      <div className={className} role="status">
        {emptyText}
      </div>
    );
  }

  if (state.status === "error" && state.error) {
    const diagnosticDetails = getDiagnosticDetails(state.error.details);

    return (
      <div className={className} role="alert">
        <strong>请求失败</strong>
        <p>{state.error.message}</p>
        <p>错误码：{state.error.code}</p>
        {state.traceId ? <p>追踪编号：{state.traceId}</p> : null}
        {diagnosticDetails.length > 0 ? (
          <dl>
            {diagnosticDetails.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        {state.canRetry && onRetry ? (
          <button onClick={onRetry} type="button">
            重试
          </button>
        ) : null}
      </div>
    );
  }

  return null;
}

function getDiagnosticDetails(details: Record<string, unknown>) {
  const diagnostics: Array<[string, string]> = [];

  if (typeof window !== "undefined") {
    diagnostics.push(["当前页面", window.location.href]);
  }

  if (typeof details.url === "string") {
    diagnostics.push(["请求地址", details.url]);
  }

  if (typeof details.cause === "string") {
    diagnostics.push(["底层原因", details.cause]);
  }

  return diagnostics;
}
