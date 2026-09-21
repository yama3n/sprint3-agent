import { groupReviewEntries, inspectorModeOf, isEditable } from "./inspector-lib";

describe("inspectorModeOf", () => {
  it("uses read-only evidence mode for confirmed (ok) fields", () => {
    const field = { field_id: "requester", label: "依頼元企業", status: "ok" as const };
    expect(inspectorModeOf(field)).toBe("evidence");
    expect(isEditable(field)).toBe(false);
  });

  it("uses review mode for fields needing confirmation", () => {
    const field = {
      field_id: "desired_delivery",
      label: "希望納期",
      status: "review" as const,
      reason_type: "conflict" as const,
    };
    expect(inspectorModeOf(field)).toBe("review");
    expect(isEditable(field)).toBe(true);
  });
});

describe("groupReviewEntries", () => {
  it("groups review fields by internal reason and ignores confirmed ones", () => {
    const groups = groupReviewEntries([
      { field: { field_id: "a", label: "A", status: "review", reason_type: "missing" } },
      { field: { field_id: "b", label: "B", status: "review", reason_type: "conflict" } },
      { field: { field_id: "c", label: "C", status: "review", reason_type: "missing" } },
      { field: { field_id: "d", label: "D", status: "ok" } },
    ]);

    const byReason = Object.fromEntries(groups.map((g) => [g.reasonType, g.entries.length]));
    expect(byReason).toEqual({ missing: 2, conflict: 1 });
    expect(groups.find((g) => g.reasonType === "missing")?.reasonKey).toBe(
      "detail.reasonMissing",
    );
  });

  it("returns an empty list when nothing needs review", () => {
    expect(groupReviewEntries([{ field: { field_id: "a", label: "A", status: "ok" } }])).toEqual(
      [],
    );
  });

  it("keeps the item number alongside item-level entries", () => {
    const groups = groupReviewEntries([
      {
        field: { field_id: "grade", label: "グレード", status: "review", reason_type: "ambiguous" },
        itemNo: 3,
      },
    ]);
    expect(groups[0].entries[0].itemNo).toBe(3);
  });
});
