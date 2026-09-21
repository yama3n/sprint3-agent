import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import { useListInquiriesApiV1InquiriesGet } from "@/shared/api/generated/inquiries";
import { InquiryListPage } from "./InquiryListPage";
import "@/shared/i18n";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

const mockInvalidateQueries = jest.fn();
jest.mock("@tanstack/react-query", () => ({
  ...jest.requireActual("@tanstack/react-query"),
  useQueryClient: () => ({ invalidateQueries: mockInvalidateQueries }),
}));

const mockMutate = jest.fn();

jest.mock("@/shared/api/generated/inquiries", () => ({
  useListInquiriesApiV1InquiriesGet: jest.fn(),
  useRemoveInquiryApiV1InquiriesInquiryIdDelete: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
  getListInquiriesApiV1InquiriesGetQueryKey: () => [
    "/api/v1/inquiries",
  ],
}));

function mockQuery(
  overrides: Partial<ReturnType<typeof useListInquiriesApiV1InquiriesGet>>,
) {
  (useListInquiriesApiV1InquiriesGet as jest.Mock).mockReturnValue({
    isLoading: false,
    isError: false,
    data: undefined,
    ...overrides,
  });
}

describe("InquiryListPage", () => {
  const push = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
    push.mockClear();
    mockMutate.mockReset();
    mockInvalidateQueries.mockReset();
  });

  it("shows a loading skeleton while fetching", () => {
    mockQuery({ isLoading: true });
    render(<InquiryListPage />);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("shows the top action without duplicated plus signs", () => {
    mockQuery({ data: { status: 200, data: { items: [], total_count: 0 } } });
    render(<InquiryListPage />);

    expect(
      screen.getByRole("button", { name: "新規アップロード" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /＋.*新規アップロード/ }),
    ).not.toBeInTheDocument();
  });

  it("shows an error message on failure", () => {
    mockQuery({ isError: true });
    render(<InquiryListPage />);
    expect(
      screen.getByText("引合一覧の取得に失敗しました"),
    ).toBeInTheDocument();
  });

  it("shows the total-zero empty state with a CTA when there are no inquiries at all", () => {
    mockQuery({ data: { status: 200, data: { items: [], total_count: 0 } } });
    render(<InquiryListPage />);

    expect(screen.getByText("まだ引合がありません")).toBeInTheDocument();
    expect(screen.getByText("＋ 書類をアップロード")).toBeInTheDocument();
  });

  it("shows the filtered-empty state without a CTA when a filter yields zero results", async () => {
    mockQuery({
      data: {
        status: 200,
        data: {
          items: [
            {
              id: 1,
              inquiry_code: "INQ-1",
              requester: "A社",
              project_name: "案件A",
              status: "draft",
              requested_at: null,
              review_count: 0,
              updated_at: new Date().toISOString(),
            },
          ],
          total_count: 1,
        },
      },
    });
    render(<InquiryListPage />);
    const user = userEvent.setup();

    await user.click(screen.getByText("確定済み（0）"));

    expect(screen.getByText("確定済みの引合はありません")).toBeInTheDocument();
    expect(screen.queryByText("＋ 書類をアップロード")).not.toBeInTheDocument();
  });

  it("renders the table with rows when data is present", () => {
    mockQuery({
      data: {
        status: 200,
        data: {
          items: [
            {
              id: 1,
              inquiry_code: "INQ-1",
              requester: "東西石油開発",
              project_name: "北海油田 鋼管更新案件",
              status: "draft",
              requested_at: "2026-09-01T10:32:00+09:00",
              review_count: 7,
              updated_at: "2026-09-10T14:02:00+09:00",
            },
          ],
          total_count: 1,
        },
      },
    });
    render(<InquiryListPage />);

    expect(screen.getByText("東西石油開発")).toBeInTheDocument();
    expect(screen.getByText("北海油田 鋼管更新案件")).toBeInTheDocument();
    expect(screen.getByText("7件")).toBeInTheDocument();
  });

  it("keeps unextracted header values blank", () => {
    mockQuery({
      data: {
        status: 200,
        data: {
          items: [
            {
              id: 2,
              inquiry_code: "INQ-2",
              requester: null,
              project_name: null,
              status: "draft",
              requested_at: null,
              review_count: 0,
              updated_at: "2026-09-10T14:02:00+09:00",
            },
          ],
          total_count: 1,
        },
      },
    });
    render(<InquiryListPage />);

    const cells = screen.getAllByRole("cell");
    expect(cells[0]).toBeEmptyDOMElement();
    expect(cells[1]).toBeEmptyDOMElement();
    expect(cells[2]).toBeEmptyDOMElement();
    expect(screen.queryByText("不明")).not.toBeInTheDocument();
  });

  it("navigates to the detail screen when a row is clicked", async () => {
    mockQuery({
      data: {
        status: 200,
        data: {
          items: [
            {
              id: 42,
              inquiry_code: "INQ-42",
              requester: "北洋エナジー",
              project_name: "資材所要一覧",
              status: "final",
              requested_at: null,
              review_count: 0,
              updated_at: new Date().toISOString(),
            },
          ],
          total_count: 1,
        },
      },
    });
    render(<InquiryListPage />);
    const user = userEvent.setup();

    await user.click(screen.getByText("北洋エナジー"));

    expect(push).toHaveBeenCalledWith("/inquiries/42");
  });

  it("opens the confirmation without navigating and deletes the selected inquiry", async () => {
    mockQuery({
      data: {
        status: 200,
        data: {
          items: [
            {
              id: 42,
              inquiry_code: "INQ-42",
              requester: "北洋エナジー",
              project_name: "資材所要一覧",
              status: "draft",
              requested_at: null,
              review_count: 0,
              updated_at: new Date().toISOString(),
            },
          ],
          total_count: 1,
        },
      },
    });
    mockMutate.mockImplementation((_variables, options) =>
      options.onSuccess({ status: 204, data: undefined }),
    );
    render(<InquiryListPage />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "INQ-42 を削除" }));

    expect(push).not.toHaveBeenCalled();
    expect(screen.getByText("この引合を削除しますか？")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "削除する" }));

    expect(mockMutate).toHaveBeenCalledWith(
      { inquiryId: 42 },
      expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      }),
    );
    expect(mockInvalidateQueries).toHaveBeenCalledWith({
      queryKey: ["/api/v1/inquiries"],
    });
  });
});
