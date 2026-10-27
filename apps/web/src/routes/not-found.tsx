import { Film } from "lucide-react";
import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="mx-auto max-w-xl py-16 text-center">
      <div className="mx-auto grid size-14 place-items-center rounded-full border border-dashed border-amber/50 text-amber">
        <Film aria-hidden="true" className="size-6" />
      </div>
      <p className="timecode mt-6 text-xs text-muted-foreground">404</p>
      <h1 className="mt-2 text-3xl font-medium">That page is not in this reel</h1>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">
        The address does not match a page in this build. Return to the workspace to see the current
        status.
      </p>
      <Link
        to="/"
        className="mt-6 inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        Back to workspace
      </Link>
    </div>
  );
}
