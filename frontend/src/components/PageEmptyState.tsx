import { Empty } from "antd";

export function PageEmptyState({
  description = "暂无可恢复的分析任务。请先从任务输入页创建任务。"
}: {
  description?: string;
}) {
  return <Empty className="page-empty-state" description={description} />;
}
