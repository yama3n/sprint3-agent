import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import { useListInquiriesApiV1InquiriesGet } from "@/shared/api/generated/inquiries";
import { InquiryListPage } from "./InquiryListPage";
import "@/shared/i18n";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

jest.mock("@/shared/api/generated/inquiries", () => ({
  useListInquiriesApiV1InquiriesGet: jest.fn(),
}));

function mockQuery(overrides: Partial<ReturnType<typeof useListInquiriesApiV1InquiriesGet>>) {
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
  });

  it("shows a loading skeleton while fetching", () => {
    mockQuery({ isLoading: true });
    render(<InquiryListPage />);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("shows an error message on failure", () => {
    mockQuery({ isError: true });
    render(<InquiryListPage />);
    expect(screen.getByText("引合一覧の取得に失敗しました")).toBeInTheDocument();
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
});
