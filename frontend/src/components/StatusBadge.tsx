import { Tag } from "antd";
import type { ReactNode } from "react";

type StatusBadgeProps = {
  className?: string;
  color?: string;
  icon?: ReactNode;
  label: ReactNode;
};

export function StatusBadge({ className, color = "default", icon, label }: StatusBadgeProps) {
  return (
    <Tag className={className} color={color} icon={icon}>
      {label}
    </Tag>
  );
}
