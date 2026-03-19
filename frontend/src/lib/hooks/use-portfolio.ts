"use client";

import { useQuery } from "@tanstack/react-query";
import { portfolioApi } from "@/lib/api";

const STALE = 10_000;

export function useBalance() {
  return useQuery({
    queryKey: ["portfolio", "balance"],
    queryFn: () => portfolioApi.balance(),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}

export function usePositions() {
  return useQuery({
    queryKey: ["portfolio", "positions"],
    queryFn: () => portfolioApi.positions(),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}

export function usePnl() {
  return useQuery({
    queryKey: ["portfolio", "pnl"],
    queryFn: () => portfolioApi.pnl(),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}
