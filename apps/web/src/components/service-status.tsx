import { CheckCircle2, CircleAlert, Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type ServiceState = "loading" | "ok" | "degraded" | "error";

type ServiceStatusProps = {
  state: ServiceState;
  okLabel?: string;
  className?: string;
};

const labels: Record<ServiceState, string> = {
  loading: "Checking…",
  ok: "Ready",
  degraded: "Unavailable",
  error: "Unreachable",
};

export function ServiceStatus({ state, okLabel, className }: ServiceStatusProps) {
  const variant = state === "ok" ? "verified" : state === "loading" ? "outline" : "danger";
  const Icon = state === "ok" ? CheckCircle2 : state === "loading" ? Loader2 : CircleAlert;
  const label = state === "ok" && okLabel ? okLabel : labels[state];

  return (
    <Badge variant={variant} className={className}>
      <Icon aria-hidden="true" className={cn("size-3.5", state === "loading" && "animate-spin")} />
      {label}
    </Badge>
  );
}
