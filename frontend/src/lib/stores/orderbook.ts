"use client";

import { create } from "zustand";
import type { Orderbook } from "@/lib/api";
import { marketsApi } from "@/lib/api";

interface OrderbookState {
  marketId: string | null;
  orderbook: Orderbook | null;
  isLoading: boolean;
  error: string | null;
  /** Timestamp of the last successful fetch */
  lastUpdated: number | null;

  fetchOrderbook: (marketId: string) => Promise<void>;
  /** Clear orderbook when navigating away from a market */
  clear: () => void;
}

export const useOrderbookStore = create<OrderbookState>((set) => ({
  marketId: null,
  orderbook: null,
  isLoading: false,
  error: null,
  lastUpdated: null,

  fetchOrderbook: async (marketId: string) => {
    set({ isLoading: true, error: null, marketId });
    try {
      const orderbook = await marketsApi.orderbook(marketId);
      set({ orderbook, isLoading: false, lastUpdated: Date.now() });
    } catch (err) {
      set({
        error:
          err instanceof Error ? err.message : "Failed to fetch orderbook",
        isLoading: false,
      });
    }
  },

  clear: () => {
    set({
      marketId: null,
      orderbook: null,
      isLoading: false,
      error: null,
      lastUpdated: null,
    });
  },
}));
