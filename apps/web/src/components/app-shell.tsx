import { useState } from "react";
import { Activity, LayoutDashboard, Moon, PanelLeftClose, PanelLeftOpen, Sun } from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { ApiStatusPill } from "@/components/api-status-pill";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

const RAIL_STORAGE_KEY = "silent-cinema-rail";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/system", label: "System status", icon: Activity, end: false },
] as const;

function initialRailExpanded() {
  try {
    const stored = localStorage.getItem(RAIL_STORAGE_KEY);
    if (stored === "expanded") return true;
    if (stored === "collapsed") return false;
    return window.matchMedia("(min-width: 1280px)").matches;
  } catch {
    return false;
  }
}

function currentPage(pathname: string) {
  if (pathname === "/") return "Dashboard";
  if (pathname === "/system") return "System status";
  return "Not found";
}

export function AppShell() {
  const [railExpanded, setRailExpanded] = useState(initialRailExpanded);
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  function toggleRail() {
    setRailExpanded((previous) => {
      const next = !previous;
      try {
        localStorage.setItem(RAIL_STORAGE_KEY, next ? "expanded" : "collapsed");
      } catch {
        /* The rail still changes for this session. */
      }
      return next;
    });
  }

  return (
    <div className={cn("min-h-dvh pl-16 md:pl-[72px]", railExpanded && "lg:pl-[232px]")}>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-panel focus:px-4 focus:py-2 focus:text-sm focus:text-foreground focus:shadow-lg"
      >
        Skip to content
      </a>

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 flex w-16 flex-col border-r border-border bg-panel md:w-[72px]",
          railExpanded && "lg:w-[232px]",
        )}
      >
        <div className="flex h-16 items-center justify-center border-b border-border lg:justify-start lg:px-4">
          <NavLink
            to="/"
            aria-label="Silent Cinema home"
            className="flex min-w-0 items-center gap-3"
          >
            <span
              aria-hidden="true"
              className="grid size-9 shrink-0 place-items-center rounded border border-amber/40 bg-amber/10 font-serif text-base text-amber"
            >
              SC
            </span>
            <span
              className={cn(
                "hidden font-serif text-lg leading-tight text-foreground",
                railExpanded && "lg:inline",
              )}
            >
              Silent Cinema
            </span>
          </NavLink>
        </div>

        <nav
          id="primary-navigation"
          aria-label="Primary"
          className="flex flex-1 flex-col gap-1 p-2 md:p-3"
        >
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                aria-label={item.label}
                title={railExpanded ? undefined : item.label}
                className={({ isActive }) =>
                  cn(
                    "flex h-11 items-center gap-3 rounded-md px-3 text-sm font-medium",
                    isActive
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      aria-hidden="true"
                      className={cn("size-5 shrink-0", isActive && "text-amber")}
                    />
                    <span className={railExpanded ? "hidden lg:inline" : "sr-only"}>
                      {item.label}
                    </span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        <div className="border-t border-border p-2 md:p-3">
          <p
            className={cn(
              "px-2 pb-2 text-xs leading-5 text-muted-foreground",
              railExpanded ? "hidden lg:block" : "sr-only",
            )}
          >
            Milestone 1 preview
          </p>
          <button
            type="button"
            onClick={toggleRail}
            aria-expanded={railExpanded}
            aria-controls="primary-navigation"
            title={railExpanded ? "Collapse rail" : "Expand rail"}
            className="hidden h-10 w-full items-center gap-3 rounded-md px-3 text-sm text-muted-foreground hover:bg-secondary/60 hover:text-foreground lg:flex"
          >
            {railExpanded ? (
              <PanelLeftClose aria-hidden="true" className="size-5 shrink-0" />
            ) : (
              <PanelLeftOpen aria-hidden="true" className="size-5 shrink-0" />
            )}
            <span className={cn(!railExpanded && "sr-only")}>
              {railExpanded ? "Collapse rail" : "Expand rail"}
            </span>
          </button>
        </div>
      </aside>

      <div className="flex min-h-dvh flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between gap-4 border-b border-border bg-background px-4 md:px-6">
          <div className="flex min-w-0 items-center gap-2 text-sm">
            <span className="text-muted-foreground">Workspace</span>
            <span aria-hidden="true" className="text-muted-foreground">
              /
            </span>
            <span className="truncate font-medium">{currentPage(location.pathname)}</span>
          </div>
          <div className="flex items-center gap-1">
            <ApiStatusPill />
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
              title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
              className="inline-flex size-10 items-center justify-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground"
            >
              {theme === "dark" ? (
                <Sun aria-hidden="true" className="size-5" />
              ) : (
                <Moon aria-hidden="true" className="size-5" />
              )}
            </button>
            <span className="sr-only" aria-live="polite">
              {theme === "dark" ? "Dark theme" : "Light theme"}
            </span>
          </div>
        </header>

        <main
          id="main"
          tabIndex={-1}
          className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-8 md:px-8 md:py-10"
        >
          <Outlet />
        </main>

        <footer className="mx-auto w-full max-w-[1440px] px-4 pb-8 text-xs text-muted-foreground md:px-8">
          <p>
            Local-first workspace. Subtitles are exported as files and are never burned into the
            film.
          </p>
        </footer>
      </div>
    </div>
  );
}
