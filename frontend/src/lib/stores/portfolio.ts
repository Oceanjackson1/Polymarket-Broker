"use client";

import { create } from "zustand";
import type { Balance, PnL, Position } from "@/lib/api";
import { portfolioApi } from "@/lib/api";

interface PortfolioState {
  positions: Position[];
  balance: Balance | null;
  pnl: PnL | null;
  isLoading: boolean;
  error: string | null;

  fetchPositions: () => Promise<void>;
  fetchBalance: () => Promise<void>;
  fetchPnl: () => Promise<void>;
  fetchAll: () => Promise<void>;
  reset: () => void;
}

const initialState = {
  positions: [],
  balance: null,
  pnl: null,
  isLoading: false,
  error: null,
};

export const usePortfolioStore = create<PortfolioState>((set) => ({
  ...initialState,

  fetchPositions: async () => {
    set({ isLoading: true, error: null });
    try {
      const positions = await portfolioApi.positions();
      set({ positions, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to fetch positions",
        isLoading: false,
      });
    }
  },

  fetchBalance: async () => {
    set({ isLoading: true, error: null });
    try {
      const balance = await portfolioApi.balance();
      set({ balance, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to fetch balance",
        isLoading: false,
      });
    }
  },

  fetchPnl: async () => {
    set({ isLoading: true, error: null });
    try {
      const pnl = await portfolioApi.pnl();
      set({ pnl, isLoading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to fetch PnL",
        isLoading: false,
      });
    }
  },

  fetchAll: async () => {
    set({ isLoading: true, error: null });
    try {
      const [positions, balance, pnl] = await Promise.all([
        portfolioApi.positions(),
        portfolioApi.balance(),
        portfolioApi.pnl(),
      ]);
      set({ positions, balance, pnl, isLoading: false });
    } catch (err) {
      set({
        error:
          err instanceof Error ? err.message : "Failed to fetch portfolio data",
        isLoading: false,
      });
    }
  },

  reset: () => {
    set(initialState);
  },
}));
