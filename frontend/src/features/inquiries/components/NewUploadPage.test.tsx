import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import {
  useCreateInquiryApiV1InquiriesPost,
  useGetAgentStatusApiV1InquiriesInquiryIdAgentStatusGet,
} from "@/shared/api/generated/inquiries";
import { NewUploadPage } from "./NewUploadPage";
import "@/shared/i18n";

jest.mock("next/navigation", () => ({ useRouter: jest.fn() }));
jest.mock("@/shared/api/generated/inquiries", () => ({
  useCreateInquiryApiV1InquiriesPost: jest.fn(),
  useAddFilesApiV1InquiriesInquiryIdFilesPost: jest.fn(),
  useGetAgentStatusApiV1InquiriesInquiryIdAgentStatusGet: jest.fn(),
}));

const mockCreate = useCreateInquiryApiV1InquiriesPost as jest.Mock;
const mockStatus =
  useGetAgentStatusApiV1InquiriesInquiryIdAgentStatusGet as jest.Mock;

function file(name: string): File {
  return new File(["x"], name, { type: "application/octet-stream" });
}

describe("NewUploadPage (SCR-02)", () => {
  const push = jest.fn();
  const mutateAsync = jest.fn();

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push });
    mutateAsync.mockReset();
    push.mockReset();
    mockCreate.mockReturnValue({ mutateAsync, isPending: false });
    mockStatus.mockReturnValue({ data: undefined });
  });

  it("disables the upload button until a file is selected", () => {
    render(<NewUploadPage />);
    expect(screen.getByTestId("upload-form")).toHaveStyle({ width: "100%" });
    expect(
      screen.getByRole("button", { name: "アップロード開始" }),
    ).toBeDisabled();
  });

  it("rejects unsupported file types inline and keeps supported ones", async () => {
    render(<NewUploadPage />);
    const user = userEvent.setup();

    await user.upload(screen.getByLabelText("ファイルを選択"), [
      file("order.xlsx"),
      file("contract.docx"),
    ]);

    expect(
      await screen.findByText(
        "「contract.docx」は対応していません（Excel／PDF／メールのみ）",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("order.xlsx")).toBeInTheDocument();
    expect(screen.queryByText("contract.docx")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "アップロード開始" }),
    ).toBeEnabled();
  });

  it("uploads selected files and starts polling", async () => {
    mutateAsync.mockResolvedValue({
      status: 202,
      data: { inquiry_id: 42, status: "draft", agent_run_id: 7 },
    });
    render(<NewUploadPage />);
    const user = userEvent.setup();

    await user.upload(screen.getByLabelText("ファイルを選択"), [
      file("order.xlsx"),
    ]);
    await user.click(screen.getByRole("button", { name: "アップロード開始" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    const call = mutateAsync.mock.calls[0][0];
    expect(call.data.files).toHaveLength(1);
    await waitFor(() =>
      expect(mockStatus).toHaveBeenCalledWith(42, expect.anything()),
    );
  });

  it("shows the agent progress label reported by agent-status", async () => {
    mockStatus.mockReturnValue({
      data: {
        status: 200,
        data: {
          stage: "extracting",
          progress_percent: 40,
          status: "running",
          error_message: null,
        },
      },
    });
    mutateAsync.mockResolvedValue({
      status: 202,
      data: { inquiry_id: 42, status: "draft", agent_run_id: 7 },
    });
    render(<NewUploadPage />);
    const user = userEvent.setup();

    await user.upload(screen.getByLabelText("ファイルを選択"), [
      file("order.xlsx"),
    ]);
    await user.click(screen.getByRole("button", { name: "アップロード開始" }));

    expect(await screen.findByText("AI解析中…")).toBeInTheDocument();
    expect(screen.getByText("40%")).toBeInTheDocument();
  });

  it("surfaces the error message when the agent run fails", async () => {
    mockStatus.mockReturnValue({
      data: {
        status: 200,
        data: {
          stage: "failed",
          progress_percent: 40,
          status: "failed",
          error_message: "全ファイルのパースに失敗しました",
        },
      },
    });
    mutateAsync.mockResolvedValue({
      status: 202,
      data: { inquiry_id: 42, status: "draft", agent_run_id: 7 },
    });
    render(<NewUploadPage />);
    const user = userEvent.setup();

    await user.upload(screen.getByLabelText("ファイルを選択"), [
      file("bad.pdf"),
    ]);
    await user.click(screen.getByRole("button", { name: "アップロード開始" }));

    expect(
      await screen.findByText("全ファイルのパースに失敗しました"),
    ).toBeInTheDocument();
  });
});
