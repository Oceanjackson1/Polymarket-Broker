"use client";

import { useQuery } from "@tanstack/react-query";
import { nbaApi } from "@/lib/api";

const STALE = 5_000;

export function useNbaGames() {
  return useQuery({
    queryKey: ["nba", "games"],
    queryFn: () => nbaApi.games(),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}

export function useNbaGame(id: string) {
  return useQuery({
    queryKey: ["nba", "game", id],
    queryFn: () => nbaApi.game(id),
    staleTime: STALE,
    refetchInterval: STALE,
    enabled: !!id,
  });
}

export function useNbaFusion(id: string) {
  return useQuery({
    queryKey: ["nba", "fusion", id],
    queryFn: () => nbaApi.fusion(id),
    staleTime: STALE,
    refetchInterval: STALE,
    enabled: !!id,
  });
}
