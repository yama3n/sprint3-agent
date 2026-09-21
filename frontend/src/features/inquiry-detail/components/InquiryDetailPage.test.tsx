import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import { useGetInquiryDetailApiV1InquiriesInquiryIdGet } from "@/shared/api/generated/inquiries";
import { InquiryDetailPage } from "./InquiryDetailPage";
import "@/shared/i18n";

jest.mock("next/navigation", () => ({ useRouter: jest.fn() }));
jest.mock("@/shared/api/generated/inquiries", () => ({
  useGetInquiryDetailApiV1InquiriesInquiryIdGet: jest.fn(),
}));

const mockDetail = useGetInquiryDetailApiV1InquiriesInquiryIdGet as jest.Mock;

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
    candidates: [],
    ...overrides,
  };
}

function detailPayload(overrides: Record<string, unknown> = {}) {
  return {
    status: 200,
    data: {
      inquiry: {
        id: 1,
        inquiry_code: "INQ-2026-0091",
        requester: "東西石油開発",
        project_name: "北海油田 鋼管更新案件",
        status: "draft",
        requested_at: "2026-09-01T10:32:00+09:00",
        updated_at: "2026-09-10T14:02:00+09:00",
      },
      case_fields: [field()],
      items: [],
      case_notes: [],
      review_summary: { review_count: 0, web_supplemented_count: 0 },
      ...overrides,
    },
  };
}

describe("InquiryDetailPage (SCR-03)", () => {
  const push = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
    push.mockReset();
  });

  it("shows a loading skeleton while fetching", () => {
    mockDetail.mockReturnValue({ isLoading: true });
    render(<InquiryDetailPage inquiryId={1} />);
    expect(screen.queryByText("案件サマリー")).not.toBeInTheDocument();
  });

  it("shows an actionable error message on failure", () => {
    mockDetail.mockReturnValue({ isLoading: false, isError: true });
    render(<InquiryDetailPage inquiryId={1} />);
    expect(
      screen.getByText("引合詳細の取得に失敗しました。時間をおいて再度お試しください"),
    ).toBeInTheDocument();
  });

  it("renders the header, summary order and confirmed values", () => {
    mockDetail.mockReturnValue({ isLoading: false, isError: false, data: detailPayload() });
    render(<InquiryDetailPage inquiryId={1} />);

    expect(
      screen.getByText("東西石油開発 - 北海油田 鋼管更新案件"),
    ).toBeInTheDocument();
    expect(screen.getByText(/INQ-2026-0091/)).toBeInTheDocument();
    expect(screen.getByText("確認中")).toBeInTheDocument();
    expect(screen.getByText("依頼元企業")).toBeInTheDocument();
    expect(screen.getByText("東西石油開発株式会社")).toBeInTheDocument();
  });

  it("shows a single 要確認 badge with the reason hint (no colour-coding per reason)", () => {
    mockDetail.mockReturnValue({
      isLoading: false,
      isError: false,
      data: detailPayload({
        case_fields: [
          field({
            field_id: "desired_delivery",
            label: "希望納期",
            value: null,
            status: "review",
            reason_type: "conflict",
            candidates: [{ id: 1 }, { id: 2 }],
          }),
        ],
        review_summary: { review_count: 1, web_supplemented_count: 0 },
      }),
    });
    render(<InquiryDetailPage inquiryId={1} />);

    expect(screen.getByText("要確認")).toBeInTheDocument();
    expect(screen.getByText("候補2件")).toBeInTheDocument();
  });

  it("marks web-supplemented values with a separate tag, not a status badge", () => {
    mockDetail.mockReturnValue({
      isLoading: false,
      isError: false,
      data: detailPayload({
        case_fields: [
          field({
            field_id: "market_condition",
            label: "市況",
            value: "北海圏の油田開発は増加傾向",
            status: "ok",
            is_web_supplemented: true,
            confirmed_by: "web",
          }),
        ],
        review_summary: { review_count: 0, web_supplemented_count: 1 },
      }),
    });
    render(<InquiryDetailPage inquiryId={1} />);

    expect(screen.getByText("北海圏の油田開発は増加傾向")).toBeInTheDocument();
    expect(screen.getAllByText("Web補完").length).toBeGreaterThan(0);
    expect(screen.queryByText("要確認")).not.toBeInTheDocument();
  });

  it("renders item rows with B-field columns", () => {
    mockDetail.mockReturnValue({
      isLoading: false,
      isError: false,
      data: detailPayload({
        items: [
          {
            id: 10,
            item_no: 1,
            notes: [],
            fields: [
              field({ field_id: "grade", label: "グレード", value: "L-80" }),
              field({ field_id: "quantity", label: "数量", value: "480" }),
            ],
          },
        ],
      }),
    });
    render(<InquiryDetailPage inquiryId={1} />);

    expect(screen.getByText("グレード")).toBeInTheDocument();
    expect(screen.getByText("L-80")).toBeInTheDocument();
    expect(screen.getByText("480")).toBeInTheDocument();
  });

  it("opens the field inspector callback when a summary row is clicked", async () => {
    const onOpenField = jest.fn();
    mockDetail.mockReturnValue({ isLoading: false, isError: false, data: detailPayload() });
    render(<InquiryDetailPage inquiryId={1} onOpenField={onOpenField} />);
    const user = userEvent.setup();

    await user.click(screen.getByText("依頼元企業"));

    expect(onOpenField).toHaveBeenCalledWith(
      expect.objectContaining({ field_id: "requester" }),
    );
  });

  it("navigates to the add-files screen (SCR-05)", async () => {
    mockDetail.mockReturnValue({ isLoading: false, isError: false, data: detailPayload() });
    render(<InquiryDetailPage inquiryId={7} />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "資料を追加" }));

    expect(push).toHaveBeenCalledWith("/inquiries/7/add-files");
  });
});
