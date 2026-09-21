import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/shared/lib/auth-store";
import { LoginForm } from "./LoginForm";
import "@/shared/i18n";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

function renderWithProviders() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <LoginForm />
    </QueryClientProvider>,
  );
}

describe("LoginForm", () => {
  const push = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
    useAuthStore.setState({ token: null, user: null });
    push.mockClear();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("shows a validation error when submitted empty", async () => {
    renderWithProviders();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "ログインする" }));

    expect(
      await screen.findByText("メールアドレスとパスワードを入力してください"),
    ).toBeInTheDocument();
  });

  it("logs in successfully and stores the session", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          session_token: "poc-mock-token",
          user: { email: "sales@toseki-steel.co.jp", display_name: "田中 太郎" },
        }),
        { status: 200 },
      ),
    );
    renderWithProviders();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("メールアドレス"), "sales@toseki-steel.co.jp");
    await user.type(screen.getByLabelText("パスワード"), "password");
    await user.click(screen.getByRole("button", { name: "ログインする" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/inquiries"));
    expect(useAuthStore.getState().token).toBe("poc-mock-token");
    expect(useAuthStore.getState().user?.displayName).toBe("田中 太郎");
  });

  it("shows an error and does not navigate on wrong credentials", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "INVALID_CREDENTIALS" }), { status: 401 }),
    );
    renderWithProviders();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText("メールアドレス"), "sales@toseki-steel.co.jp");
    await user.type(screen.getByLabelText("パスワード"), "wrong");
    await user.click(screen.getByRole("button", { name: "ログインする" }));

    expect(
      await screen.findByText("メールアドレスまたはパスワードが正しくありません"),
    ).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
    expect(screen.getByLabelText("メールアドレス")).toHaveValue("sales@toseki-steel.co.jp");
  });
});
