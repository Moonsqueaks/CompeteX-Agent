import {
  TERM_DICTIONARY,
  isTermKey,
  type TermExplanation,
  type TermKey
} from "./domain/termExplanations";

export { TERM_DICTIONARY, isTermKey, type TermExplanation, type TermKey };

export const TERM_EXPLANATIONS = Object.fromEntries(
  Object.entries(TERM_DICTIONARY).map(([key, value]) => [
    key,
    {
      description: value.professional,
      label: value.name
    }
  ])
) as Record<TermKey, { description: string; label: string }>;
