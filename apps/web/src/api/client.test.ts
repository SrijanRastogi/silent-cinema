import { describe, expect, it, vi } from "vitest";

import { ApiError, getHealth, getReadiness } from "@/api/client";

import { jsonResponse } from "@/test/helpers";

describe("API client", () => {
  it("returns a typed health response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ status: "ok", version: "0.1.0" })),
    );

    await expect(getHealth()).resolves.toEqual({ status: "ok", version: "0.1.0" });
  });

  it("maps the documented error envelope to ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            error: {
              code: "validation_error",
              message: "Request validation failed.",
              details: [{ field: "name", reason: "required" }],
              request_id: "req-9",
            },
          },
          422,
        ),
      ),
    );

    const error = await getHealth().catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    if (error instanceof ApiError) {
      expect(error.code).toBe("validation_error");
      expect(error.status).toBe(422);
      expect(error.requestId).toBe("req-9");
      expect(error.details).toEqual([{ field: "name", reason: "required" }]);
    }
  });

  it("accepts a 503 readiness payload as a valid readiness result", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ status: "not_ready", database: "unavailable" }, 503)),
    );

    await expect(getReadiness()).resolves.toEqual({
      status: "not_ready",
      database: "unavailable",
    });
  });

  it("reports a non-JSON failure without inventing success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("upstream failed", { status: 502 })),
    );

    const error = await getHealth().catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    if (error instanceof ApiError) {
      expect(error.code).toBe("unexpected_response");
      expect(error.status).toBe(502);
    }
  });

  it("reports a transport failure as a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    const error = await getHealth().catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    if (error instanceof ApiError) {
      expect(error.code).toBe("network_error");
      expect(error.message).toContain("Could not reach the API");
    }
  });
});
