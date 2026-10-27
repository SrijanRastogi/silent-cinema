import { useQuery } from "@tanstack/react-query";
import { CircleAlert, Database, RefreshCw, Server } from "lucide-react";

import { ApiError } from "@/api/client";
import { healthQueryOptions, readinessQueryOptions } from "@/api/queries";
import { PageHeader } from "@/components/page-header";
import { ServiceStatus, type ServiceState } from "@/components/service-status";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCheckedAt } from "@/lib/format";
import { cn } from "@/lib/utils";

function Summary({ state }: { state: string }) {
  return (
    <p className="sr-only" aria-live="polite">
      {state}
    </p>
  );
}

export function SystemPage() {
  const health = useQuery(healthQueryOptions);
  const readiness = useQuery(readinessQueryOptions);
  const isRefreshing = health.isFetching || readiness.isFetching;

  const apiState: ServiceState =
    health.status === "pending" ? "loading" : health.status === "error" ? "error" : "ok";
  const databaseState: ServiceState =
    readiness.status === "pending"
      ? "loading"
      : readiness.status === "error"
        ? "error"
        : readiness.data.database === "ok"
          ? "ok"
          : "degraded";

  const summary =
    apiState === "loading" || databaseState === "loading"
      ? "Checking the API and database."
      : apiState === "error"
        ? "The API is not reachable."
        : databaseState === "ok"
          ? "The API is reachable and PostgreSQL is ready."
          : "The API is reachable. PostgreSQL is unavailable.";

  const failure = health.error ?? readiness.error;

  function refresh() {
    void Promise.all([health.refetch(), readiness.refetch()]);
  }

  return (
    <div className="space-y-8">
      <Summary state={summary} />
      <PageHeader
        title="System status"
        description="Liveness tells you the API process is answering. Readiness performs a live SELECT 1 against PostgreSQL. Both results below come from this browser, not from stored or sample values."
      >
        <Button
          type="button"
          variant="outline"
          onClick={refresh}
          disabled={isRefreshing}
          className="mt-5"
        >
          <RefreshCw aria-hidden="true" className={cn("size-4", isRefreshing && "animate-spin")} />
          {isRefreshing ? "Refreshing…" : "Refresh status"}
        </Button>
      </PageHeader>

      {failure ? (
        <div
          role="status"
          className="flex gap-3 rounded-lg border border-danger/30 bg-danger/5 p-4"
        >
          <CircleAlert aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-danger" />
          <div className="min-w-0 space-y-1 text-sm">
            <p className="font-medium text-danger">The last check failed</p>
            <p className="leading-6 text-muted-foreground">
              {failure instanceof ApiError
                ? failure.message
                : "The browser could not read the status response."}
            </p>
            {failure instanceof ApiError && failure.requestId ? (
              <p className="timecode text-xs text-muted-foreground">
                Request ID: {failure.requestId}
              </p>
            ) : null}
            <p className="leading-6 text-muted-foreground">
              For the API, run <code className="timecode text-xs">make dev</code>. For PostgreSQL,
              run <code className="timecode text-xs">docker compose up -d db</code>.
            </p>
          </div>
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Server aria-hidden="true" className="size-5 text-muted-foreground" />
                  API
                </CardTitle>
                <CardDescription>Process liveness, independent of the database.</CardDescription>
              </div>
              <ServiceStatus state={apiState} okLabel="Online" />
            </div>
          </CardHeader>
          <CardContent>
            <dl className="space-y-3 text-sm">
              <div className="flex items-baseline justify-between gap-4">
                <dt className="text-muted-foreground">Endpoint</dt>
                <dd className="timecode text-xs">/api/v1/health</dd>
              </div>
              <div className="flex items-baseline justify-between gap-4">
                <dt className="text-muted-foreground">Version</dt>
                <dd>
                  {health.status === "success" ? (
                    <span className="timecode text-xs">{health.data.version}</span>
                  ) : (
                    <span className="text-muted-foreground">No response</span>
                  )}
                </dd>
              </div>
              <div className="flex items-baseline justify-between gap-4">
                <dt className="text-muted-foreground">Last checked</dt>
                <dd className="timecode text-xs">{formatCheckedAt(health.dataUpdatedAt)}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Database aria-hidden="true" className="size-5 text-muted-foreground" />
                  PostgreSQL
                </CardTitle>
                <CardDescription>
                  Readiness runs a live query against the application database.
                </CardDescription>
              </div>
              <ServiceStatus state={databaseState} okLabel="Ready" />
            </div>
          </CardHeader>
          <CardContent>
            <dl className="space-y-3 text-sm">
              <div className="flex items-baseline justify-between gap-4">
                <dt className="text-muted-foreground">Endpoint</dt>
                <dd className="timecode text-xs">/api/v1/health/ready</dd>
              </div>
              <div className="flex items-baseline justify-between gap-4">
                <dt className="text-muted-foreground">Result</dt>
                <dd>
                  {readiness.status === "success" ? (
                    <span className="text-xs">
                      {readiness.data.status === "ready" ? "ready" : "not_ready"}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">No response</span>
                  )}
                </dd>
              </div>
              <div className="flex items-baseline justify-between gap-4">
                <dt className="text-muted-foreground">Last checked</dt>
                <dd className="timecode text-xs">{formatCheckedAt(readiness.dataUpdatedAt)}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      <section aria-labelledby="check-notes" className="max-w-3xl">
        <h2 id="check-notes" className="text-xl font-medium">
          Reading these results
        </h2>
        <div className="mt-3 space-y-3 text-sm leading-6 text-muted-foreground">
          <p>
            An online API with an unavailable database means the backend is running but PostgreSQL
            is stopped or unreachable. Uploads and processing would fail in that state.
          </p>
          <p>
            An unreachable API means the browser could not complete the request. The frontend does
            not retry silently or invent a status.
          </p>
        </div>
      </section>
    </div>
  );
}
