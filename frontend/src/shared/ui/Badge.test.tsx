import { render, screen } from "@testing-library/react";
import { Badge } from "./Badge";

describe("Badge", () => {
  it("renders its label text", () => {
    render(<Badge variant="review">要確認</Badge>);
    expect(screen.getByText("要確認")).toBeInTheDocument();
  });
});
