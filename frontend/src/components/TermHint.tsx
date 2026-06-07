import { Popover, Typography } from "antd";
import { Info } from "lucide-react";

import { TERM_DICTIONARY, type TermKey } from "../domain/termExplanations";

const { Text } = Typography;

export function TermHint({
  showLabel = true,
  term
}: {
  showLabel?: boolean;
  term: TermKey;
}) {
  const data = TERM_DICTIONARY[term];

  const content = (
    <div className="term-hint-popover-content">
      <Text className="term-hint-professional">{data.professional}</Text>
      <div className="term-hint-scenario">
        <Text>{data.scenario}</Text>
      </div>
    </div>
  );

  return (
    <Popover
      content={content}
      placement="top"
      title={<span className="term-hint-popover-title">{data.name}</span>}
      trigger="hover"
    >
      <button
        aria-label={`${data.name}解释`}
        className={showLabel ? "term-hint-trigger" : "term-hint-trigger term-hint-trigger-icon"}
        type="button"
      >
        {showLabel ? <span>{data.name}</span> : null}
        <Info aria-hidden="true" size={14} />
      </button>
    </Popover>
  );
}
