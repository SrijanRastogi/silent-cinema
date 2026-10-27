import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { jsonResponse, renderRoute, stubApi } from "@/test/helpers";

describe("System status", () => {
  it("shows the API version and ready database from live requests", async () => {
    stubApi();

    renderRoute("/system");

    expect(await screen.findByText("0.1.0")).toBeInTheDocument();
    expect(await screen.findByText("Online")).toBeInTheDocument();
    expect(await screen.findByText("Ready")).toBeInTheDocument();
    expect(
      await screen.findByText("The API is reachable and PostgreSQL is ready."),
    ).toBeInTheDocument();
  });

  it("treats a 503 readiness payload as unavailable rather than a transport error", async () => {
    stubApi({
      readiness: () => jsonResponse({ status: "not_ready", database: "unavailable" }, 503),
    });

    renderRoute("/system");

    expect(await screen.findByText("Unavailable")).toBeInTheDocument();
    expect(
      await screen.findByText("The API is reachable. PostgreSQL is unavailable."),
    ).toBeInTheDocument();
    expect(screen.queryByText("The last check failed")).not.toBeInTheDocument();
  });

  it("surfaces a safe error envelope and request id", async () => {
    stubApi({
      health: () =>
        jsonResponse(
          {
            error: {
              code: "service_unavailable",
              message: "The API is restarting.",
              details: [],
              request_id: "req-123",
            },
          },
          503,
        ),
    });

    renderRoute("/system");

    expect(await screen.findByText("The last check failed")).toBeInTheDocument();
    expect(await screen.findByText("The API is restarting.")).toBeInTheDocument();
    expect(await screen.findByText("Request ID: req-123")).toBeInTheDocument();
  });

  it("refetches both checks when Refresh status is used", async () => {
    const fetchMock = stubApi();
    const user = userEvent.setup();

    renderRoute("/system");

    const refresh = await screen.findByRole("button", { name: "Refresh status" });
    await waitFor(() => expect(refresh).toBeEnabled());
    await user.click(refresh);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
  });
});
