import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { jsonResponse, renderRoute, stubApi } from "@/test/helpers";

describe("Dashboard", () => {
  it("renders an honest empty workspace with no invented films or upload control", async () => {
    const fetchMock = stubApi();

    renderRoute("/");

    expect(screen.getByRole("heading", { level: 1, name: "Workspace" })).toBeInTheDocument();
    expect(screen.getByText("No films in this workspace")).toBeInTheDocument();
    expect(screen.queryByText(/^\d+ films$/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /upload/i })).not.toBeInTheDocument();

    expect(await screen.findByText("API online")).toBeInTheDocument();
    expect(await screen.findByText("Ready")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("shows an actionable message when the API is unreachable", async () => {
    stubApi({
      health: () => Promise.reject(new TypeError("fetch failed")),
      readiness: () => Promise.reject(new TypeError("fetch failed")),
    });

    renderRoute("/");

    expect(await screen.findAllByText("API unreachable")).not.toHaveLength(0);
    expect(await screen.findByText(/Start it with make dev/)).toBeInTheDocument();
  });

  it("reports an unavailable database from a real 503 readiness payload", async () => {
    stubApi({
      readiness: () => jsonResponse({ status: "not_ready", database: "unavailable" }, 503),
    });

    renderRoute("/");

    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
    expect(
      await screen.findByText(/PostgreSQL is not reachable.*docker compose up -d db/),
    ).toBeInTheDocument();
  });

  it("shows a not-found page for an unknown route", async () => {
    stubApi();

    renderRoute("/missing-page");

    expect(
      screen.getByRole("heading", { level: 1, name: "That page is not in this reel" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to workspace" })).toHaveAttribute("href", "/");
  });
});
