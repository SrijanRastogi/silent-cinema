import { useEffect, useState } from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "silent-cinema-theme";

function currentTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

function persist(theme: Theme) {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    /* Storage can be unavailable; the session still changes theme. */
  }
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(currentTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  function toggleTheme() {
    setTheme((previous) => {
      const next = previous === "dark" ? "light" : "dark";
      persist(next);
      return next;
    });
  }

  return { theme, toggleTheme };
}
