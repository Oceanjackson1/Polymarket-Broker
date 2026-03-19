"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthContext, useLocale } from "@/lib/providers";
import { useWebSocket } from "@/lib/hooks/useWebSocket";
import BiasSignalBadge from "@/components/data/BiasSignalBadge";

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";

export default function NbaDataPage() {
  const { api, token } = useAuthContext();
  const { t } = useLocale();

  const { data: gamesResp } = useQuery({
    queryKey: ["nba-games"],
    queryFn: () => api.getNbaGames(),
    enabled: !!token,
  });

  const games = gamesResp?.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("nav.nba")} Fusion</h1>
        <p className="mt-1 text-sm text-zinc-400">Live scores x Polymarket odds x bias signals</p>
      </div>

      {games.length === 0 ? (
        <div className="py-12 text-center text-zinc-500">{t("common.noData")}</div>
      ) : (
        <div className="space-y-3">
          {games.map((game) => (
            <NbaGameCard key={game.game_id} game={game} />
          ))}
        </div>
      )}
    </div>
  );
}

function NbaGameCard({ game }: { game: import("@/lib/api-client").NbaGame }) {
  const { t } = useLocale();

  const statusColors: Record<string, string> = {
    live: "bg-red-500",
    scheduled: "bg-zinc-600",
    final: "bg-zinc-700",
  };

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${statusColors[game.game_status] || "bg-zinc-600"}`} />
          <span className="text-xs font-medium uppercase text-zinc-400">
            {game.game_status === "live"
              ? `${t("data.live")} Q${game.quarter || "?"} ${game.time_remaining || ""}`
              : game.game_status === "final"
              ? t("data.final")
              : t("data.scheduled")}
          </span>
        </div>
        {game.bias_direction && game.bias_magnitude_bps != null && (
          <BiasSignalBadge direction={game.bias_direction} bps={game.bias_magnitude_bps} />
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-white">{game.home_team}</span>
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold text-white">{game.score_home}</span>
            {game.home_win_prob != null && (
              <span className="text-xs text-zinc-400">{(game.home_win_prob * 100).toFixed(0)}%</span>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-white">{game.away_team}</span>
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold text-white">{game.score_away}</span>
            {game.away_win_prob != null && (
              <span className="text-xs text-zinc-400">{(game.away_win_prob * 100).toFixed(0)}%</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
