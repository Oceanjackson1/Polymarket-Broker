"use client";

import { useQuery } from "@tanstack/react-query";
import { marketsApi, type ListMarketsParams } from "@/lib/api";

const STALE = 60_000;

export function useMarkets(params?: ListMarketsParams) {
  return useQuery({
    queryKey: ["markets", params ?? {}],
    queryFn: () => marketsApi.list(params),
    staleTime: STALE,
  });
}

export function useMarket(id: string) {
  return useQuery({
    queryKey: ["markets", id],
    queryFn: () => marketsApi.get(id),
    staleTime: STALE,
    enabled: !!id,
  });
}
