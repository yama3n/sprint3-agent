import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import { DetailActionBar } from "./DetailActionBar";
import "@/shared/i18n";

jest.mock("next/navigation", () => ({ useRouter: jest.fn() }));

describe("DetailActionBar (SCR-03 アクションバー)", () => {
  const push = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
    push.mockReset();
  });

  function renderBar(props: Partial<React.ComponentProps<typeof DetailActionBar>> = {}) {
    const onConfirm = jest.fn().mockResolvedValue(true);
    const onExport = jest.fn().mockResolvedValue(true);
    render(
      <DetailActionBar
        inquiryId={7}
        isFinal={false}
        onConfirm={onConfirm}
        onExport={onExport}
        isConfirming={false}
        isExporting={false}
        error={null}
        {...props}
      />,
    );
    return { onConfirm, onExport };
  }

  it("shows 確定する (not 出力する) while the inquiry is still draft (TEST-19)", () => {
    renderBar({ isFinal: false });
    expect(screen.getByRole("button", { name: "確定する" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "出力する" })).not.toBeInTheDocument();
  });

  it("swaps to 出力する once the inquiry is final (TEST-19)", () => {
    renderBar({ isFinal: true });
    expect(screen.getByRole("button", { name: "出力する" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "確定する" })).not.toBeInTheDocument();
  });

  it("confirms through the confirmation modal", async () => {
    const { onConfirm } = renderBar({ isFinal: false });
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "確定する" }));
    expect(screen.getByText("この引合を確定しますか？")).toBeInTheDocument();

    const buttons = screen.getAllByRole("button", { name: "確定する" });
    await user.click(buttons[buttons.length - 1]);

    expect(onConfirm).toHaveBeenCalled();
  });

  it("offers Excel only, with Word/PDF disabled (Scope 1 / TEST-24)", async () => {
    renderBar({ isFinal: true });
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "出力する" }));

    expect(screen.getByRole("radio", { name: "Excel（Item List）" })).toBeEnabled();
    expect(screen.getByRole("radio", { name: "Word（準備中）" })).toBeDisabled();
    expect(screen.getByRole("radio", { name: "PDF（準備中）" })).toBeDisabled();
  });

  it("starts the export and reports completion", async () => {
    const { onExport } = renderBar({ isFinal: true });
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "出力する" }));
    await user.click(screen.getByRole("button", { name: "出力開始" }));

    expect(onExport).toHaveBeenCalled();
    expect(
      await screen.findByText("出力しました。ダウンロードを開始します。"),
    ).toBeInTheDocument();
  });

  it("navigates to the add-files screen", async () => {
    renderBar();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "資料を追加" }));

    expect(push).toHaveBeenCalledWith("/inquiries/7/add-files");
  });
});
