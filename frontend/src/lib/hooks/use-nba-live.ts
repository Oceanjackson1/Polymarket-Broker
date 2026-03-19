"use client";

import { useState, useCallback } from "react";
import { useWebSocket } from "./use-websocket";

export interface NbaLiveData {
  type: string;
  game_id: string;
  home_team: string;
  away_team: string;
  score_home: number | null;
  score_away: number | null;
  quarter: number | null;
  time_remaining: string | null;
  game_status: string;
  home_win_prob: number | null;
  away_win_prob: number | null;
  bias_direction: string | null;
  bias_magnitude_bps: number | null;
  data_updated_at: string | null;
}

export function useNbaLive(gameId: string | null) {
  const [data, setData] = useState<NbaLiveData | null>(null);

  const onMessage = useCallback((msg: unknown) => {
    const d = msg as NbaLiveData;
    if (d.type === "nba_update") {
      setData(d);
    }
  }, []);

  const { isConnected } = useWebSocket({
    url: gameId ? `/ws/nba/${gameId}/live` : "",
    onMessage,
    enabled: !!gameId,
  });

  return { data, isConnected };
}
