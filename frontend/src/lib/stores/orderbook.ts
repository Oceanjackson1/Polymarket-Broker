"use client";

import { create } from "zustand";
import { marketsApi } from "@/lib/api";

interface OrderbookData {
  bids?: { price: string; size: string }[];
  asks?: { price: string; size: string }[];
  [key: string]: unknown;
}

interface OrderbookState {
  marketId: string | null;
  orderbook: OrderbookData | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;

  fetchOrderbook: (marketId: string) => Promise<void>;
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
      const orderbook = await marketsApi.orderbook(marketId) as OrderbookData;
      set({ orderbook, isLoading: false, lastUpdated: Date.now() });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to fetch orderbook",
        isLoading: false,
      });
    }
  },

  clear: () => {
    set({ marketId: null, orderbook: null, isLoading: false, error: null, lastUpdated: null });
  },
}));
