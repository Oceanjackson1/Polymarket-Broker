"use client";

import { useState, useCallback } from "react";
import { useWebSocket } from "./use-websocket";

export interface BtcLiveSnapshot {
  timeframe: string;
  price_usd: string;
  prediction_prob: string | null;
  volume: string | null;
  recorded_at: string | null;
}

interface BtcLiveMessage {
  type: string;
  data: BtcLiveSnapshot[];
}

export function useBtcLive() {
  const [data, setData] = useState<BtcLiveSnapshot[]>([]);

  const onMessage = useCallback((msg: unknown) => {
    const d = msg as BtcLiveMessage;
    if (d.type === "btc_update") {
      setData(d.data);
    }
  }, []);

  const { isConnected } = useWebSocket({
    url: "/ws/btc/live",
    onMessage,
  });

  return { data, isConnected };
}
