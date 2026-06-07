import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MetricHint } from "./components/MetricHint";
import { METRIC_DICTIONARY } from "./domain/metricExplanations";

describe("MetricHint", () => {
  it("defines novice-friendly explanations for key numeric metrics", () => {
    expect(METRIC_DICTIONARY.claim_confidence.scale).toContain("0.80-1.00");
    expect(METRIC_DICTIONARY.edge_score.source).toContain("需求替代性 30%");
    expect(METRIC_DICTIONARY.threat_rating.scale).toContain(">=0.80");
  });

  it("shows source, range and business-use copy on hover", async () => {
    render(<MetricHint metric="claim_confidence" />);

    fireEvent.mouseEnter(screen.getByLabelText("结论置信度说明"));

    expect(await screen.findByText("结论置信度")).toBeInTheDocument();
    expect(screen.getByText(/0\.82 代表这条结论已有较强证据支撑/)).toBeInTheDocument();
    expect(screen.getByText("区间口径")).toBeInTheDocument();
  });
});
