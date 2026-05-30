import { useId, useState } from "react";

import { TERM_EXPLANATIONS, type TermKey } from "./termExplanations";

export function TermHint({ term }: { term: TermKey }) {
  const tooltipId = useId();
  const [isOpen, setIsOpen] = useState(false);
  const termInfo = TERM_EXPLANATIONS[term];

  return (
    <span
      className="term-hint"
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <button
        aria-describedby={isOpen ? tooltipId : undefined}
        aria-expanded={isOpen}
        aria-label={`${termInfo.label}解释`}
        className="term-hint-trigger"
        onBlur={() => setIsOpen(false)}
        onFocus={() => setIsOpen(true)}
        type="button"
      >
        ?
      </button>
      {isOpen ? (
        <span className="term-hint-tooltip" id={tooltipId} role="tooltip">
          {termInfo.description}
        </span>
      ) : null}
    </span>
  );
}
