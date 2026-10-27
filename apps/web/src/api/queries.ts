import { queryOptions } from "@tanstack/react-query";

import { getFilm, getHealth, getReadiness, listFilms } from "@/api/client";

export const healthQueryOptions = queryOptions({
  queryKey: ["system", "health"],
  queryFn: getHealth,
  retry: false,
  staleTime: 5_000,
});

export const readinessQueryOptions = queryOptions({
  queryKey: ["system", "readiness"],
  queryFn: getReadiness,
  retry: false,
  staleTime: 5_000,
});

export const filmListQueryOptions = queryOptions({
  queryKey: ["films"],
  queryFn: listFilms,
  retry: false,
});

export function filmQueryOptions(filmId: string) {
  return queryOptions({
    queryKey: ["films", filmId],
    queryFn: () => getFilm(filmId),
    retry: false,
  });
}
