import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import {
  useAddFilesApiV1InquiriesInquiryIdFilesPost,
  useGetAgentStatusApiV1InquiriesInquiryIdAgentStatusGet,
  useGetInquiryDetailApiV1InquiriesInquiryIdGet,
} from "@/shared/api/generated/inquiries";
import { AddFilesPage } from "./AddFilesPage";
import "@/shared/i18n";

jest.mock("next/navigation", () => ({ useRouter: jest.fn() }));
jest.mock("@/shared/api/generated/inquiries", () => ({
  useCreateInquiryApiV1InquiriesPost: jest.fn(),
  useAddFilesApiV1InquiriesInquiryIdFilesPost: jest.fn(),
  useGetAgentStatusApiV1InquiriesInquiryIdAgentStatusGet: jest.fn(),
  useGetInquiryDetailApiV1InquiriesInquiryIdGet: jest.fn(),
}));

const mockAdd = useAddFilesApiV1InquiriesInquiryIdFilesPost as jest.Mock;
const mockStatus = useGetAgentStatusApiV1InquiriesInquiryIdAgentStatusGet as jest.Mock;
const mockDetail = useGetInquiryDetailApiV1InquiriesInquiryIdGet as jest.Mock;

function file(name: string): File {
  return new File(["x"], name, { type: "application/octet-stream" });
}

describe("AddFilesPage (SCR-05)", () => {
  const push = jest.fn();
  const mutateAsync = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
    mutateAsync.mockReset();
    push.mockReset();
    mockAdd.mockReturnValue({ mutateAsync, isPending: false });
    mockStatus.mockReturnValue({ data: undefined });
    mockDetail.mockReturnValue({
      data: {
        status: 200,
        data: {
          inquiry: {
            id: 7,
            inquiry_code: "INQ-2026-0091",
            requester: "東西石油開発",
            project_name: "北海油田 鋼管更新案件",
            status: "draft",
            requested_at: null,
            updated_at: "2026-09-10T14:02:00+09:00",
          },
          case_fields: [],
          items: [],
          case_notes: [],
          review_summary: { review_count: 0, web_supplemented_count: 0 },
        },
      },
    });
  });

  it("shows the target inquiry in the header", () => {
    render(<AddFilesPage inquiryId={7} />);
    expect(
      screen.getByText(/東西石油開発 - 北海油田 鋼管更新案件（INQ-2026-0091）/),
    ).toBeInTheDocument();
  });

  it("posts the added files to the existing inquiry", async () => {
    mutateAsync.mockResolvedValue({
      status: 202,
      data: { inquiry_id: 7, status: "draft", agent_run_id: 12 },
    });
    render(<AddFilesPage inquiryId={7} />);
    const user = userEvent.setup();

    await user.upload(screen.getByLabelText("ファイルを選択"), [file("extra.pdf")]);
    await user.click(screen.getByRole("button", { name: "追加する" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    expect(mutateAsync.mock.calls[0][0].inquiryId).toBe(7);
    expect(mutateAsync.mock.calls[0][0].data.files).toHaveLength(1);
  });

  it("rejects unsupported file types before upload", async () => {
    render(<AddFilesPage inquiryId={7} />);
    const user = userEvent.setup();

    await user.upload(screen.getByLabelText("ファイルを選択"), [file("memo.docx")]);

    expect(
      await screen.findByText("「memo.docx」は対応していません（Excel／PDF／メールのみ）"),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "追加する" })).toBeDisabled();
  });
});
