"use client";

import Link from "next/link";
import { useNbaGames } from "@/lib/hooks/use-nba";
import { Shimmer } from "@/components/ui/shimmer";

function StatusBadge({ status }: { status: string }) {
  const s = status?.toLowerCase() ?? "";
  if (s.includes("live") || s.includes("in_progress"))
    return (
      <span className="flex items-center gap-1.5 rounded bg-profit-bg px-2 py-0.5 text-[10px] font-semibold text-profit">
        <span className="live-dot h-1.5 w-1.5 rounded-full bg-profit" />
        LIVE
      </span>
    );
  if (s.includes("final") || s.includes("closed"))
    return (
      <span className="rounded bg-bg-elevated px-2 py-0.5 text-[10px] font-semibold text-text-muted">
        FINAL
      </span>
    );
  return (
    <span className="rounded bg-info-cyan-bg px-2 py-0.5 text-[10px] font-semibold text-info-cyan">
      SCHEDULED
    </span>
  );
}

export default function NbaGamesPage() {
  const { data, isLoading, error } = useNbaGames();
  const games = data?.data ?? [];

  return (
    <div className="flex min-h-full flex-col p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🏀</span>
          <div>
            <h1 className="text-lg font-semibold text-text-primary">
              NBA Live Games
            </h1>
            <p className="text-xs text-text-muted">
              Real-time scores × Polymarket odds × Bias signals
            </p>
          </div>
          <span className="rounded bg-accent-gold-bg px-2 py-0.5 text-[10px] font-semibold text-accent-gold">
            PRO
          </span>
        </div>
        <span className="text-xs text-text-muted">
          {games.length} games
        </span>
      </div>

      {/* Games Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Shimmer key={i} className="h-36 w-full rounded-lg" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg border border-border-subtle bg-bg-card p-6">
          <p className="text-sm text-loss">Failed to load NBA games</p>
        </div>
      ) : games.length === 0 ? (
        <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center">
          <p className="text-sm text-text-muted">No games available</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {games.map((game, i) => (
            <Link
              key={game.game_id}
              href={`/nba/${game.game_id}`}
              className={`animate-fade-in stagger-${Math.min(i + 1, 6)} group rounded-lg border border-border-subtle bg-bg-card p-5 transition-colors hover:border-accent-gold/30`}
            >
              {/* Status + Date */}
              <div className="mb-3 flex items-center justify-between">
                <StatusBadge status={game.game_status} />
                <span className="text-[10px] text-text-muted">
                  {game.quarter != null && game.time_remaining
                    ? `Q${game.quarter} ${game.time_remaining}`
                    : new Date(game.game_date).toLocaleDateString()}
                </span>
              </div>

              {/* Teams */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-medium text-text-primary">
                    {game.home_team}
                  </span>
                  <span className="font-mono text-lg font-bold text-text-primary">
                    {game.score_home ?? "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-medium text-text-secondary">
                    {game.away_team}
                  </span>
                  <span className="font-mono text-lg font-bold text-text-secondary">
                    {game.score_away ?? "—"}
                  </span>
                </div>
              </div>

              {/* Footer */}
              <div className="mt-3 flex items-center justify-between border-t border-border-subtle pt-3">
                <span className="text-[10px] text-text-muted">
                  {game.market_id ? "Market linked" : "No market"}
                </span>
                <span className="text-xs text-accent-gold opacity-0 transition-opacity group-hover:opacity-100">
                  View Fusion →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
