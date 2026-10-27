import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { App } from "@/app";

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type ApiHandlers = {
  health?: () => Response | Promise<Response>;
  readiness?: () => Response | Promise<Response>;
};

const defaultHealth = () => jsonResponse({ status: "ok", version: "0.1.0" });
const defaultReadiness = () => jsonResponse({ status: "ready", database: "ok" });

export function stubApi(handlers: ApiHandlers = {}) {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url =
      typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;

    if (url.endsWith("/api/v1/health")) {
      return Promise.resolve((handlers.health ?? defaultHealth)());
    }
    if (url.endsWith("/api/v1/health/ready")) {
      return Promise.resolve((handlers.readiness ?? defaultReadiness)());
    }
    return Promise.resolve(
      jsonResponse(
        {
          error: {
            code: "not_found",
            message: "Resource not found.",
            details: [],
            request_id: "test-request",
          },
        },
        404,
      ),
    );
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export function renderRoute(path = "/") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}
