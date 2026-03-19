"use client";

import { useQuery } from "@tanstack/react-query";
import { sportsApi } from "@/lib/api";

const STALE = 30_000;

export function useSportsCategories() {
  return useQuery({
    queryKey: ["sports", "categories"],
    queryFn: () => sportsApi.categories(),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}

export function useSportsEvents(sport: string) {
  return useQuery({
    queryKey: ["sports", "events", sport],
    queryFn: () => sportsApi.events(sport),
    staleTime: STALE,
    refetchInterval: STALE,
    enabled: !!sport,
  });
}
