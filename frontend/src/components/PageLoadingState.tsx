import { Spin, Typography } from "antd";

const { Text } = Typography;

export function PageLoadingState({ text = "正在加载数据" }: { text?: string }) {
  return (
    <div className="page-loading-state" role="status">
      <Spin size="large" />
      <Text type="secondary">{text}</Text>
    </div>
  );
}
