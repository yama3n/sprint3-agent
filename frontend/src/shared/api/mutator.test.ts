import { useAuthStore } from "@/shared/lib/auth-store";
import { customInstance } from "./mutator";

describe("customInstance", () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null });
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...window.location, href: "", pathname: "/inquiries" },
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("attaches Authorization header when a token is present", async () => {
    useAuthStore.setState({
      token: "poc-mock-token",
      user: { email: "a@b.com", displayName: "A" },
    });
    const fetchMock = jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );

    await customInstance("/api/v1/inquiries");

    const [, init] = fetchMock.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(headers.get("Authorization")).toBe("Bearer poc-mock-token");
  });

  it("does not attach Authorization header when no token is present", async () => {
    const fetchMock = jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );

    await customInstance("/api/v1/auth/login", { method: "POST", body: "{}" });

    const [, init] = fetchMock.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(headers.has("Authorization")).toBe(false);
  });

  it("clears the session and redirects to /login on 401", async () => {
    useAuthStore.setState({
      token: "expired",
      user: { email: "a@b.com", displayName: "A" },
    });
    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "UNAUTHORIZED" }), { status: 401 }),
    );

    await expect(customInstance("/api/v1/inquiries")).rejects.toThrow(
      "Authentication failed",
    );

    expect(useAuthStore.getState().token).toBeNull();
    expect(window.location.href).toBe("/login");
  });

  it("does not redirect on 401 when no session token was held (e.g. login failure)", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "INVALID_CREDENTIALS" }), { status: 401 }),
    );

    const result = await customInstance<{ data: { detail: string }; status: number }>(
      "/api/v1/auth/login",
      { method: "POST", body: "{}" },
    );

    expect(result.status).toBe(401);
    expect(result.data.detail).toBe("INVALID_CREDENTIALS");
    expect(window.location.href).toBe("");
  });
});
