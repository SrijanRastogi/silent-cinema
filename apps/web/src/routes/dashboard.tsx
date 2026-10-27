import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FileText, Film, PencilLine, ScanLine } from "lucide-react";
import { Link } from "react-router-dom";

import { ApiError } from "@/api/client";
import { filmListQueryOptions, healthQueryOptions, readinessQueryOptions } from "@/api/queries";
import { PageHeader } from "@/components/page-header";
import { ServiceStatus, type ServiceState } from "@/components/service-status";
import { UploadForm } from "@/components/upload-form";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { formatBytes, formatDuration, formatRecordedAt } from "@/lib/format";

const workflow = [
  {
    title: "Import",
    description: "The file is stored, hashed, and probed with FFmpeg for real stream metadata.",
    icon: Film,
  },
  {
    title: "Detect",
    description: "Sampled frames are scored for intertitle cards; timestamps come from frame PTS.",
    icon: ScanLine,
  },
  {
    title: "Review",
    description: "OCR text and timing are editable against a live subtitle overlay in the player.",
    icon: PencilLine,
  },
  {
    title: "Export",
    description: "Download UTF-8 SRT, WebVTT, or an MKV with a soft subtitle track. Never burned in.",
    icon: FileText,
  },
] as const;

function healthState(isPending: boolean, isError: boolean): ServiceState {
  if (isPending) return "loading";
  if (isError) return "error";
  return "ok";
}

export function DashboardPage() {
  const health = useQuery(healthQueryOptions);
  const readiness = useQuery(readinessQueryOptions);
  const films = useQuery(filmListQueryOptions);

  const databaseState: ServiceState =
    readiness.status === "pending"
      ? "loading"
      : readiness.status === "error"
        ? "error"
        : readiness.data.database === "ok"
          ? "ok"
          : "degraded";

  const problems: string[] = [];
  if (health.isError) {
    problems.push("The API is not answering. Start it with make dev, then reload this page.");
  }
  if (readiness.isError) {
    problems.push("The readiness check failed. Open system status for the detail.");
  } else if (readiness.data?.database === "unavailable") {
    problems.push(
      "PostgreSQL is not reachable. Start it with docker compose up -d db, then refresh.",
    );
  }
  if (health.error instanceof ApiError && health.error.requestId) {
    problems.push(`Request ${health.error.requestId}`);
  }

  return (
    <div className="space-y-10">
      <PageHeader
        title="Workspace"
        description="Import a silent film, read its intertitles, and correct the subtitles against the picture. Files stay on this machine; the exported subtitles are ordinary text files."
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section aria-labelledby="recent-films" className="space-y-4">
          <div className="flex items-baseline justify-between gap-4">
            <h2 id="recent-films" className="text-2xl font-medium">
              Recent films
            </h2>
            {films.data ? (
              <span className="text-xs text-muted-foreground">
                {films.data.length} {films.data.length === 1 ? "film" : "films"} in this workspace
              </span>
            ) : null}
          </div>

          {films.isPending ? (
            <div className="film-gate px-6 py-10 text-sm text-muted-foreground">
              Reading the film list from PostgreSQL…
            </div>
          ) : films.isError ? (
            <div role="alert" className="film-gate px-6 py-10">
              <p className="text-sm font-medium text-danger">The film list could not be loaded.</p>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                {films.error instanceof ApiError
                  ? films.error.message
                  : "Check that the API and PostgreSQL are running."}
              </p>
            </div>
          ) : films.data.length === 0 ? (
            <div className="film-gate px-8 py-12 md:px-14 md:py-16">
              <div className="mx-auto max-w-lg text-center">
                <div className="mx-auto grid size-14 place-items-center rounded-full border border-dashed border-amber/50 text-amber">
                  <Film aria-hidden="true" className="size-6" />
                </div>
                <h3 className="mt-5 text-2xl font-medium">No films in this workspace</h3>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  Import a short reel with the form beside this list. The film appears here as soon
                  as detection and OCR finish; there are no sample rows and no placeholder counts.
                </p>
              </div>
            </div>
          ) : (
            <ul className="divide-y divide-border overflow-hidden rounded-lg border border-border">
              {films.data.map((film) => (
                <li key={film.id}>
                  <Link
                    to={`/films/${film.id}`}
                    className="group flex flex-wrap items-center gap-4 bg-card px-5 py-4 transition-colors hover:bg-secondary/50"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium group-hover:text-primary">{film.original_filename}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        <span className="timecode">{formatDuration(film.duration_us)}</span>
                        {film.width && film.height ? ` · ${film.width}×${film.height}` : null}
                        {` · ${formatBytes(film.byte_size)} · imported ${formatRecordedAt(film.created_at)}`}
                      </p>
                    </div>
                    <Badge variant={film.entry_count > 0 ? "verified" : "warning"}>
                      {film.entry_count} {film.entry_count === 1 ? "subtitle" : "subtitles"}
                    </Badge>
                    <ArrowRight
                      aria-hidden="true"
                      className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5"
                    />
                  </Link>
                </li>
              ))}
            </ul>
          )}

          <UploadForm />
        </section>

        <aside aria-labelledby="workspace-status">
          <h2 id="workspace-status" className="text-2xl font-medium">
            Workspace status
          </h2>
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-lg">Service checks</CardTitle>
              <p className="text-sm leading-6 text-muted-foreground">
                Queried from this browser just now. No cached sample values.
              </p>
            </CardHeader>
            <CardContent>
              <dl className="divide-y divide-border" aria-live="polite">
                <div className="flex items-center justify-between gap-3 py-3">
                  <dt className="text-sm">API</dt>
                  <dd>
                    <ServiceStatus
                      state={healthState(health.isPending, health.isError)}
                      okLabel="Online"
                    />
                  </dd>
                </div>
                <div className="flex items-center justify-between gap-3 py-3">
                  <dt className="text-sm">Database</dt>
                  <dd>
                    <ServiceStatus state={databaseState} okLabel="Ready" />
                  </dd>
                </div>
              </dl>
              {problems.length > 0 ? (
                <div className="mt-3 space-y-2 border-t border-border pt-3 text-xs leading-5 text-muted-foreground">
                  {problems.map((problem) => (
                    <p key={problem}>{problem}</p>
                  ))}
                </div>
              ) : null}
            </CardContent>
            <CardFooter>
              <Link
                to="/system"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-primary underline-offset-4 hover:underline"
              >
                Open system status
                <ArrowRight aria-hidden="true" className="size-4" />
              </Link>
            </CardFooter>
          </Card>
        </aside>
      </div>

      <section aria-labelledby="review-path">
        <h2 id="review-path" className="text-2xl font-medium">
          The review path
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Four stages, all reachable in this build. Detection and OCR run on the uploaded file; the
          editor and every export use the same editable subtitle rows.
        </p>
        <ol className="mt-5 grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2 xl:grid-cols-4">
          {workflow.map((step, index) => {
            const Icon = step.icon;
            return (
              <li key={step.title} className="bg-panel p-5">
                <div className="flex items-center justify-between gap-3">
                  <span className="timecode text-xs text-primary">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <Icon aria-hidden="true" className="size-4 text-muted-foreground" />
                </div>
                <h3 className="mt-4 text-lg font-medium">{step.title}</h3>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">{step.description}</p>
              </li>
            );
          })}
        </ol>
      </section>
    </div>
  );
}
