import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Composer from "./Composer";

describe("Composer", () => {
  it("submits a trimmed prompt and clears the input", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<Composer busy={false} onSubmit={onSubmit} />);

    const input = screen.getByRole("textbox", { name: "Message" });
    await user.type(input, "  Explain CIS Control 1  ");
    await user.click(screen.getByRole("button", { name: "Send message" }));

    expect(onSubmit).toHaveBeenCalledWith("Explain CIS Control 1");
    expect(input).toHaveValue("");
  });

  it("disables submission while busy", () => {
    render(<Composer busy onSubmit={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Send message" })).toBeDisabled();
  });
});
