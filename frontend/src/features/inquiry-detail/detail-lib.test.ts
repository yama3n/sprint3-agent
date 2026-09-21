import { REASON_LABEL_KEY, toFieldDisplay } from "./detail-lib";

describe("toFieldDisplay", () => {
  it("shows the value for a confirmed (ok) field", () => {
    expect(toFieldDisplay({ value: "東西石油開発", status: "ok" })).toEqual({
      kind: "value",
      value: "東西石油開発",
      isWebSupplemented: false,
    });
  });

  it("flags web-supplemented values as a separate axis from status", () => {
    const result = toFieldDisplay({
      value: "北海圏の油田開発は増加傾向",
      status: "ok",
      is_web_supplemented: true,
    });
    expect(result).toEqual({
      kind: "value",
      value: "北海圏の油田開発は増加傾向",
      isWebSupplemented: true,
    });
  });

  it("shows review state with reason and candidate count", () => {
    const result = toFieldDisplay({
      value: null,
      status: "review",
      reason_type: "conflict",
      candidates: [{}, {}],
    });
    expect(result).toEqual({
      kind: "review",
      reasonKey: "detail.reasonConflict",
      candidateCount: 2,
    });
  });

  it("allows zero candidates for missing", () => {
    const result = toFieldDisplay({
      value: null,
      status: "review",
      reason_type: "missing",
      candidates: [],
    });
    expect(result).toEqual({
      kind: "review",
      reasonKey: "detail.reasonMissing",
      candidateCount: 0,
    });
  });

  it("returns empty when a confirmed field has no value", () => {
    expect(toFieldDisplay({ value: null, status: "ok" })).toEqual({ kind: "empty" });
  });
});

describe("REASON_LABEL_KEY", () => {
  it("covers all five internal reason types (03-spec 4章)", () => {
    expect(Object.keys(REASON_LABEL_KEY).sort()).toEqual(
      ["ambiguous", "conflict", "missing", "multiple_candidates", "parse_error"].sort(),
    );
  });
});
