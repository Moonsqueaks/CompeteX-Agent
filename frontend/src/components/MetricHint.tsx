import { Popover, Typography } from "antd";
import { Info } from "lucide-react";

import { METRIC_DICTIONARY, type MetricKey } from "../domain/metricExplanations";

const { Text } = Typography;

export function MetricHint({ metric }: { metric: MetricKey }) {
  const data = METRIC_DICTIONARY[metric];

  return (
    <Popover
      content={
        <div className="metric-hint-popover-content">
          <Text>{data.source}</Text>
          <div className="metric-hint-scale">
            <Text strong>区间口径</Text>
            <Text>{data.scale}</Text>
          </div>
          <div className="metric-hint-business">
            <Text>{data.businessUse}</Text>
          </div>
        </div>
      }
      placement="top"
      title={<span className="metric-hint-popover-title">{data.name}</span>}
      trigger="hover"
    >
      <span aria-label={`${data.name}说明`} className="metric-hint-trigger" role="img">
        <Info aria-hidden="true" size={14} />
      </span>
    </Popover>
  );
}
