import { useQuery } from "@tanstack/react-query";
import { CircleAlert, CircleCheck, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { healthQueryOptions } from "@/api/queries";
import { cn } from "@/lib/utils";

export function ApiStatusPill() {
  const health = useQuery(healthQueryOptions);
  const state = health.isPending ? "loading" : health.isError ? "error" : "ok";
  const label =
    state === "loading" ? "Checking API…" : state === "error" ? "API unreachable" : "API online";
  const Icon = state === "loading" ? Loader2 : state === "error" ? CircleAlert : CircleCheck;

  return (
    <Link
      to="/system"
      aria-label={`${label}. Open system status.`}
      className={cn(
        "inline-flex h-8 items-center gap-2 rounded-full border px-3 text-xs font-medium",
        state === "ok" && "border-verified/30 bg-verified/10 text-verified",
        state === "error" && "border-danger/30 bg-danger/10 text-danger",
        state === "loading" && "border-border text-muted-foreground",
      )}
    >
      <Icon aria-hidden="true" className={cn("size-3.5", state === "loading" && "animate-spin")} />
      <span className="hidden sm:inline">{label}</span>
    </Link>
  );
}
