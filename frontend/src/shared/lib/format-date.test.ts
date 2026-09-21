import { formatDateTime } from "./format-date";

describe("formatDateTime", () => {
  it("formats an ISO datetime as YYYY-MM-DD HH:mm", () => {
    const iso = new Date(2026, 8, 1, 10, 32).toISOString();
    expect(formatDateTime(iso)).toBe("2026-09-01 10:32");
  });

  it("returns an empty string for null/undefined", () => {
    expect(formatDateTime(null)).toBe("");
    expect(formatDateTime(undefined)).toBe("");
  });
});
