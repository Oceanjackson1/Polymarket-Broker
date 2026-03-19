"use client";

import { useQuery } from "@tanstack/react-query";
import { btcApi } from "@/lib/api";

const STALE = 5_000;

export function useBtcPredictions() {
  return useQuery({
    queryKey: ["btc", "predictions"],
    queryFn: () => btcApi.predictions(),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}

export function useBtcTimeframe(tf: string) {
  return useQuery({
    queryKey: ["btc", "timeframe", tf],
    queryFn: () => btcApi.timeframe(tf),
    staleTime: STALE,
    refetchInterval: STALE,
    enabled: !!tf,
  });
}

export function useBtcHistory(tf: string) {
  return useQuery({
    queryKey: ["btc", "history", tf],
    queryFn: () => btcApi.history(tf),
    staleTime: STALE,
    refetchInterval: STALE,
    enabled: !!tf,
  });
}
