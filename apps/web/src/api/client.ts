import type { components } from "./schema";

export type HealthResponse = components["schemas"]["HealthResponse"];
export type ReadinessResponse = components["schemas"]["ReadinessResponse"];
export type FilmSummary = components["schemas"]["FilmSummary"];
export type FilmDetail = components["schemas"]["FilmDetail"];
export type SubtitleEntry = components["schemas"]["SubtitleEntryRead"];
export type EntryUpdate = components["schemas"]["EntryUpdate"];
export type EntryCreate = components["schemas"]["EntryCreate"];
type ErrorEnvelope = components["schemas"]["ErrorEnvelope"];
type ErrorDetail = NonNullable<ErrorEnvelope["error"]["details"]>[number];

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const REQUEST_TIMEOUT_MS = 8_000;
const UPLOAD_TIMEOUT_MS = 60 * 60 * 1_000;

export class ApiError extends Error {
  readonly code: string;
  readonly status: number | null;
  readonly requestId: string | null;
  readonly details: ErrorDetail[];

  constructor(options: {
    code: string;
    message: string;
    status?: number | null;
    requestId?: string | null;
    details?: ErrorDetail[];
  }) {
    super(options.message);
    this.name = "ApiError";
    this.code = options.code;
    this.status = options.status ?? null;
    this.requestId = options.requestId ?? null;
    this.details = options.details ?? [];
  }
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false;
  }
  const error = (value as { error: unknown }).error;
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string"
  );
}

type RequestOptions = {
  acceptStatuses?: readonly number[];
  body?: BodyInit;
  method?: string;
  timeoutMs?: number;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    const init: RequestInit = {
      method: options.method ?? "GET",
      headers,
      signal: AbortSignal.timeout(options.timeoutMs ?? REQUEST_TIMEOUT_MS),
    };
    if (options.body !== undefined) {
      init.body = options.body;
    }
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    throw new ApiError({
      code: timedOut ? "request_timeout" : "network_error",
      message: timedOut
        ? "The API did not answer in time. The request is still running on the server if it was an upload; reload before retrying."
        : "Could not reach the API. Check that the backend is running.",
    });
  }

  if (!response.ok && !options.acceptStatuses?.includes(response.status)) {
    const payload: unknown = await response.json().catch(() => null);
    if (isErrorEnvelope(payload)) {
      throw new ApiError({
        code: payload.error.code,
        message: payload.error.message,
        status: response.status,
        requestId: payload.error.request_id,
        details: payload.error.details ?? [],
      });
    }
    throw new ApiError({
      code: "unexpected_response",
      message: `The API returned HTTP ${response.status} without a readable error.`,
      status: response.status,
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/v1/health");
}

export function getReadiness(): Promise<ReadinessResponse> {
  return request<ReadinessResponse>("/api/v1/health/ready", { acceptStatuses: [503] });
}

export function listFilms(): Promise<FilmSummary[]> {
  return request<FilmSummary[]>("/api/v1/films");
}

export function getFilm(filmId: string): Promise<FilmDetail> {
  return request<FilmDetail>(`/api/v1/films/${filmId}`);
}

export function uploadFilm(file: File, ocrLanguage: string): Promise<FilmDetail> {
  const form = new FormData();
  form.append("file", file);
  form.append("ocr_language", ocrLanguage);
  return request<FilmDetail>("/api/v1/films", {
    method: "POST",
    body: form,
    timeoutMs: UPLOAD_TIMEOUT_MS,
  });
}

export function updateEntry(
  filmId: string,
  entryId: string,
  payload: EntryUpdate,
): Promise<SubtitleEntry> {
  return request<SubtitleEntry>(`/api/v1/films/${filmId}/entries/${entryId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createEntry(filmId: string, payload: EntryCreate): Promise<SubtitleEntry> {
  return request<SubtitleEntry>(`/api/v1/films/${filmId}/entries`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteEntry(filmId: string, entryId: string): Promise<void> {
  return request<void>(`/api/v1/films/${filmId}/entries/${entryId}`, { method: "DELETE" });
}

export function filmVideoUrl(filmId: string): string {
  return `${API_BASE_URL}/api/v1/films/${filmId}/video`;
}

export function subtitleDownloadUrl(filmId: string, format: "srt" | "vtt"): string {
  return `${API_BASE_URL}/api/v1/films/${filmId}/subtitles/${format}`;
}

export function muxedVideoDownloadUrl(filmId: string): string {
  return `${API_BASE_URL}/api/v1/films/${filmId}/video-with-subtitles`;
}

export function burnedVideoDownloadUrl(filmId: string): string {
  return `${API_BASE_URL}/api/v1/films/${filmId}/video-burned-subtitles`;
}

export function scanFilm(filmId: string, ocrLanguage: string = "eng"): Promise<FilmDetail> {
  return request<FilmDetail>(`/api/v1/films/${filmId}/scan`, {
    method: "POST",
    body: JSON.stringify({ ocr_language: ocrLanguage }),
    timeoutMs: UPLOAD_TIMEOUT_MS,
  });
}

