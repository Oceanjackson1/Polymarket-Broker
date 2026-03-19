"use client";

import { useState, useCallback } from "react";
import { useSignTypedData } from "wagmi";
import { useAuthContext } from "@/lib/providers";
import { useWallet } from "./useWallet";

export function useTrading() {
  const { api } = useAuthContext();
  const { canTrade } = useWallet();
  const { signTypedDataAsync } = useSignTypedData();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const buildAndSubmitOrder = useCallback(
    async (params: {
      market_id: string;
      side: string;
      price: number;
      size: number;
    }) => {
      if (!canTrade) throw new Error("Wallet not connected");

      setLoading(true);
      setError(null);

      try {
        // 1. Build EIP-712 payload
        const { eip712_payload, payload_hash } = await api.buildOrder(params);

        // 2. Sign with wallet
        const payload = eip712_payload as {
          domain: Record<string, unknown>;
          types: Record<string, Array<{ name: string; type: string }>>;
          primaryType: string;
          message: Record<string, unknown>;
        };

        const signature = await signTypedDataAsync({
          domain: payload.domain as Record<string, unknown>,
          types: payload.types,
          primaryType: payload.primaryType,
          message: payload.message,
        });

        // 3. Submit signed order
        const order = await api.submitOrder(payload_hash, signature);
        return order;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Order failed";
        setError(msg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [api, canTrade, signTypedDataAsync]
  );

  return { buildAndSubmitOrder, loading, error, canTrade };
}
