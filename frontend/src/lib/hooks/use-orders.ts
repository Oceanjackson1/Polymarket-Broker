"use client";

import { useQuery } from "@tanstack/react-query";
import { ordersApi } from "@/lib/api";

const STALE = 10_000;

export function useOrders() {
  return useQuery({
    queryKey: ["orders"],
    queryFn: () => ordersApi.list(),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}
