import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/shared/lib/auth-store";
import { AppShell } from "./AppShell";
import "@/shared/i18n";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}));

describe("AppShell", () => {
  const push = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
    (usePathname as jest.Mock).mockReturnValue("/inquiries");
    useAuthStore.setState({
      token: "poc-mock-token",
      user: { email: "sales@toseki-steel.co.jp", displayName: "田中 太郎" },
    });
    push.mockClear();
  });

  it("renders the nav items and the current user", () => {
    render(
      <AppShell>
        <div>content</div>
      </AppShell>,
    );

    expect(screen.getAllByText("進捗確認").length).toBeGreaterThan(0);
    expect(screen.getByText("新規アップロード")).toBeInTheDocument();
    expect(screen.getByText("田中 太郎")).toBeInTheDocument();
    expect(screen.getByText("content")).toBeInTheDocument();
    expect(screen.getByText("引合書整理エージェント")).toHaveStyle({
      whiteSpace: "nowrap",
    });
    expect(screen.getByRole("button", { name: "進捗確認" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(
      screen.getByRole("button", { name: "新規アップロード" }),
    ).not.toHaveAttribute("aria-current");
  });

  it("marks only the upload navigation active on /inquiries/upload", () => {
    (usePathname as jest.Mock).mockReturnValue("/inquiries/upload");

    render(
      <AppShell>
        <div>content</div>
      </AppShell>,
    );

    expect(
      screen.getByRole("button", { name: "進捗確認" }),
    ).not.toHaveAttribute("aria-current");
    expect(
      screen.getByRole("button", { name: "新規アップロード" }),
    ).toHaveAttribute("aria-current", "page");
  });

  it("shows a toast instead of navigating for placeholder nav items", async () => {
    render(
      <AppShell>
        <div>content</div>
      </AppShell>,
    );
    const user = userEvent.setup();

    await user.click(screen.getByText("設定"));

    expect(await screen.findByText("準備中の機能です")).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("navigates when a real nav item is clicked", async () => {
    render(
      <AppShell>
        <div>content</div>
      </AppShell>,
    );
    const user = userEvent.setup();

    await user.click(screen.getByText("新規アップロード"));

    expect(push).toHaveBeenCalledWith("/inquiries/upload");
  });

  it("clears the session and redirects to /login after confirming logout", async () => {
    render(
      <AppShell>
        <div>content</div>
      </AppShell>,
    );
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "ログアウト" }));
    expect(screen.getByText("ログアウトしますか？")).toBeInTheDocument();
    expect(
      screen.getByText("未確定の変更は保存されています"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("ログアウトすると再度ログインが必要です"),
    ).toBeInTheDocument();

    const dialogLogoutButtons = screen.getAllByRole("button", {
      name: "ログアウト",
    });
    await user.click(dialogLogoutButtons[dialogLogoutButtons.length - 1]);

    expect(useAuthStore.getState().token).toBeNull();
    expect(push).toHaveBeenCalledWith("/login");
  });
});
