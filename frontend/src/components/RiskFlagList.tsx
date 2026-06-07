import { AlertTriangle } from "lucide-react";
import { Space, Tag } from "antd";
import type { ReactNode } from "react";

import { RISK_FLAG_LABELS } from "../domain/labels";

type RiskFlagListProps = {
  ariaLabel?: string;
  className?: string;
  color?: string;
  icon?: ReactNode;
  labels?: Record<string, string>;
  riskFlags: string[];
  useSpace?: boolean;
};

export function RiskFlagList({
  ariaLabel = "风险标记",
  className = "risk-flag-list",
  color = "warning",
  icon,
  labels = RISK_FLAG_LABELS,
  riskFlags,
  useSpace = false
}: RiskFlagListProps) {
  if (riskFlags.length === 0) {
    return null;
  }

  const tags = riskFlags.map((riskFlag) => (
    <Tag color={color} key={riskFlag}>
      {icon}
      {labels[riskFlag] ?? riskFlag}
    </Tag>
  ));

  if (useSpace) {
    return (
      <Space aria-label={ariaLabel} className={className} size={[6, 6]} wrap>
        {tags}
      </Space>
    );
  }

  return (
    <div aria-label={ariaLabel} className={className}>
      {tags}
    </div>
  );
}

export function WarningRiskFlagList(props: Omit<RiskFlagListProps, "icon">) {
  return <RiskFlagList {...props} icon={<AlertTriangle size={12} />} />;
}
