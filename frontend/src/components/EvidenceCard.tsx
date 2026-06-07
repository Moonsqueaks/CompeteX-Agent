import { Card, Descriptions, Space, Tag, Typography } from "antd";
import type { ReactNode } from "react";

import { CONFIDENCE_DETAIL_LABELS, CONFIDENCE_LABELS, SOURCE_TYPE_LABELS } from "../domain/labels";
import { EMPTY_VALUE_TEXT, formatDateTime } from "../utils/format";
import { MetricHint } from "./MetricHint";
import { RiskFlagList } from "./RiskFlagList";

const { Paragraph, Text } = Typography;

type EvidenceCardProps = {
  accessTime?: null | string;
  accessTimeLabel?: string;
  accessTimeStatus?: null | string;
  accessTimeText?: null | string;
  body?: ReactNode;
  className?: string;
  confidenceLevel?: null | string;
  contentSummary?: null | string;
  emptyText?: string;
  formatText?: (value: string) => string;
  limitations?: null | string;
  metaExtra?: ReactNode;
  riskFlags?: string[];
  sourceType?: null | string;
  style?: React.CSSProperties;
  title: ReactNode;
};

export function EvidenceCard({
  accessTime,
  accessTimeLabel = "访问时间",
  accessTimeStatus,
  accessTimeText,
  body,
  className,
  confidenceLevel,
  contentSummary,
  emptyText = EMPTY_VALUE_TEXT,
  formatText = (value) => value,
  limitations,
  metaExtra,
  riskFlags = [],
  sourceType,
  style,
  title
}: EvidenceCardProps) {
  const resolvedAccessTimeText =
    accessTimeText ??
    (accessTimeStatus === "available" || accessTime
      ? formatDateTime(accessTime, {
          emptyText,
          fallback: formatText
        })
      : emptyText);

  return (
    <Card className={className} size="small" style={style}>
      <Space style={{ marginBottom: 8 }} wrap>
        <Text strong>{title}</Text>
        {sourceType ? <Tag color="cyan">{SOURCE_TYPE_LABELS[sourceType] ?? formatText(sourceType)}</Tag> : null}
        {confidenceLevel ? (
          <Tag>
            {CONFIDENCE_DETAIL_LABELS[confidenceLevel] ??
              CONFIDENCE_LABELS[confidenceLevel] ??
              formatText(confidenceLevel)}
            <MetricHint metric="evidence_confidence_level" />
          </Tag>
        ) : null}
        {metaExtra}
      </Space>
      {body ?? (
        <>
          {contentSummary ? (
            <Paragraph style={{ marginBottom: 6 }}>{formatText(contentSummary)}</Paragraph>
          ) : null}
          <Descriptions column={1} size="small">
            <Descriptions.Item label={accessTimeLabel}>{resolvedAccessTimeText}</Descriptions.Item>
          </Descriptions>
          {limitations ? <Paragraph type="secondary">{formatText(limitations)}</Paragraph> : null}
        </>
      )}
      {body ? null : <RiskFlagList riskFlags={riskFlags} />}
    </Card>
  );
}
