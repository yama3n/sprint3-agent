import type React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InspectorPanel, type InspectorState } from "./InspectorPanel";
import "@/shared/i18n";

function candidate(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    value: "東西石油開発株式会社",
    source_type: "excel",
    source_file: "order.xlsx",
    source_location: "A2",
    quoted_text: "発注元: 東西石油開発株式会社",
    web_url: null,
    web_source_name: null,
    web_referenced_at: null,
    is_explicit_correction: false,
    superseded_value: null,
    is_selected: false,
    ...overrides,
  };
}

function field(overrides: Record<string, unknown> = {}) {
  return {
    field_id: "requester",
    label: "依頼元企業",
    display_order: 1,
    value: "東西石油開発株式会社",
    status: "ok",
    reason_type: null,
    is_web_supplemented: false,
    confirmed_by: "ai",
    candidates: [candidate()],
    ...overrides,
  };
}

function renderPanel(state: InspectorState, overrides: Record<string, unknown> = {}) {
  const onConfirm = jest.fn().mockResolvedValue(true);
  const merged: Record<string, unknown> = {
    state,
    reviewEntries: [],
    onClose: jest.fn(),
    onBackToOverview: jest.fn(),
    onSelectEntry: jest.fn(),
    onConfirm,
    isSaving: false,
    saveError: null,
    ...overrides,
  };
  render(
    <InspectorPanel
      {...(merged as unknown as React.ComponentProps<typeof InspectorPanel>)}
    />,
  );
  return merged as { onConfirm: jest.Mock };
}

describe("InspectorPanel (SCR-04)", () => {
  it("shows read-only evidence mode for confirmed fields (TEST-11)", () => {
    renderPanel({ mode: "field", field: field() as never });

    expect(screen.getByText("根拠確認")).toBeInTheDocument();
    expect(screen.getByText("order.xlsx A2", { exact: false })).toBeInTheDocument();
    // 読み取り専用: 編集欄・確定ボタン・候補選択ボタンを出さない
    expect(screen.queryByLabelText("確定する値")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "この値を確定する" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "この候補を使う" })).not.toBeInTheDocument();
  });

  it("shows review mode with reason, candidates and confirm button (TEST-12)", () => {
    renderPanel({
      mode: "field",
      field: field({
        value: null,
        status: "review",
        reason_type: "conflict",
        candidates: [candidate(), candidate({ id: 2, value: "東西石油開発" })],
      }) as never,
    });

    expect(screen.getByText("要確認")).toBeInTheDocument();
    expect(screen.getByText("資料間で内容が矛盾しています")).toBeInTheDocument();
    expect(screen.getByLabelText("確定する値")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "この候補を使う" })).toHaveLength(2);
  });

  it("allows an ok field to be edited after the inquiry is final (TEST-20)", () => {
    renderPanel(
      { mode: "field", field: field() as never },
      { allowFinalEdit: true },
    );

    expect(screen.getByLabelText("確定する値")).toHaveValue("東西石油開発株式会社");
    expect(screen.getByRole("button", { name: "この値を確定する" })).toBeInTheDocument();
  });

  it("confirms the picked candidate value", async () => {
    const props = renderPanel({
      mode: "field",
      field: field({
        value: null,
        status: "review",
        reason_type: "multiple_candidates",
        candidates: [candidate({ id: 7, value: "VAM TOP" })],
      }) as never,
    });
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "この候補を使う" }));
    await user.click(screen.getByRole("button", { name: "この値を確定する" }));

    expect(props.onConfirm).toHaveBeenCalledWith(
      expect.objectContaining({ value: "VAM TOP", selectedCandidateId: 7 }),
    );
  });

  it("warns that an empty value stays in review (missing)", () => {
    renderPanel({
      mode: "field",
      field: field({
        value: "",
        status: "review",
        reason_type: "missing",
        candidates: [],
      }) as never,
    });

    expect(screen.getByText("候補となる記載が見つかりませんでした")).toBeInTheDocument();
    expect(
      screen.getByText(
        "値が空のため、この項目は要確認（情報が見つかりません）のまま保持されます。",
      ),
    ).toBeInTheDocument();
  });

  it("groups review items by reason in overview mode", () => {
    renderPanel(
      { mode: "overview" },
      {
        reviewEntries: [
          { field: field({ field_id: "a", label: "希望納期", status: "review", reason_type: "conflict" }) },
          { field: field({ field_id: "b", label: "グレード", status: "review", reason_type: "missing" }), itemNo: 2 },
        ],
      },
    );

    expect(screen.getByText("要確認項目")).toBeInTheDocument();
    expect(screen.getByText("資料間で内容が矛盾しています")).toBeInTheDocument();
    expect(screen.getByText("情報が見つかりません")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "品目2 / グレード" })).toBeInTheDocument();
  });

  it("shows the empty overview message when nothing needs review", () => {
    renderPanel({ mode: "overview" }, { reviewEntries: [] });
    expect(screen.getByText("確認が必要な項目はありません")).toBeInTheDocument();
  });
});
