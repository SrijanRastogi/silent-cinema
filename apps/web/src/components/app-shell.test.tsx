import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { renderRoute, stubApi } from "@/test/helpers";

describe("Theme toggle", () => {
  it("switches theme, updates the accessible name, and remembers the choice", async () => {
    stubApi();
    const user = userEvent.setup();

    renderRoute("/");
    await screen.findByText("API online");

    expect(document.documentElement).not.toHaveClass("dark");

    await user.click(screen.getByRole("button", { name: "Switch to dark theme" }));

    expect(document.documentElement).toHaveClass("dark");
    expect(localStorage.getItem("silent-cinema-theme")).toBe("dark");
    expect(screen.getByRole("button", { name: "Switch to light theme" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Switch to light theme" }));

    expect(document.documentElement).not.toHaveClass("dark");
    expect(localStorage.getItem("silent-cinema-theme")).toBe("light");
  });
});
