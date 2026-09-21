import {
  isSupportedFile,
  isTerminalStage,
  partitionFiles,
  STAGE_PROGRESS,
} from "./upload-lib";

function file(name: string): File {
  return new File(["x"], name, { type: "application/octet-stream" });
}

describe("isSupportedFile", () => {
  it.each(["order.xlsx", "quote.PDF", "mail.eml"])("accepts %s", (name) => {
    expect(isSupportedFile(name)).toBe(true);
  });

  it.each(["contract.docx", "image.png", "noext"])("rejects %s", (name) => {
    expect(isSupportedFile(name)).toBe(false);
  });
});

describe("partitionFiles", () => {
  it("splits supported and unsupported files", () => {
    const result = partitionFiles([file("a.xlsx"), file("b.docx"), file("c.pdf")]);

    expect(result.accepted.map((f) => f.name)).toEqual(["a.xlsx", "c.pdf"]);
    expect(result.rejectedNames).toEqual(["b.docx"]);
  });
});

describe("isTerminalStage", () => {
  it("treats completed/failed/stopped as terminal", () => {
    expect(isTerminalStage("completed")).toBe(true);
    expect(isTerminalStage("failed")).toBe(true);
    expect(isTerminalStage("stopped")).toBe(true);
  });

  it("treats in-flight stages as non-terminal", () => {
    expect(isTerminalStage("uploading")).toBe(false);
    expect(isTerminalStage("extracting")).toBe(false);
    expect(isTerminalStage(undefined)).toBe(false);
  });
});

describe("STAGE_PROGRESS", () => {
  it("increases monotonically through the happy path", () => {
    const order: Array<keyof typeof STAGE_PROGRESS> = [
      "uploading",
      "extracting",
      "structuring",
      "reviewing",
      "completed",
    ];
    const values = order.map((s) => STAGE_PROGRESS[s]);
    expect(values).toEqual([...values].sort((a, b) => a - b));
    expect(STAGE_PROGRESS.completed).toBe(100);
  });
});
