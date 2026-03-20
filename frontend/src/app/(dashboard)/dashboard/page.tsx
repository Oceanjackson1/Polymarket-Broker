"use client";

import { useBalance, usePnl, usePositions } from "@/lib/hooks/use-portfolio";
import { useNbaGames } from "@/lib/hooks/use-nba";
import { useBtcPredictions } from "@/lib/hooks/use-btc";
import { useQuery } from "@tanstack/react-query";
import { analysisApi, type ScanOpportunity } from "@/lib/api";
import { Shimmer } from "@/components/ui/shimmer";

export default function DashboardPage() {
  const balance = useBalance();
  const pnl = usePnl();
  const positions = usePositions();
  const nbaGames = useNbaGames();
  const btcPredictions = useBtcPredictions();
  const aiScan = useQuery({
    queryKey: ["analysis", "scan"],
    queryFn: () => analysisApi.scan(),
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
  const discoveries: ScanOpportunity[] = aiScan.data?.opportunities ?? [];

  const totalAssets = balance.data?.balance ?? null;
  const todayPnl = pnl.data?.realized ?? null;
  const unrealizedPnl = pnl.data?.unrealized ?? null;
  const activePositions = positions.data?.positions ?? [];
  const games = nbaGames.data?.data ?? [];
  const predictions = btcPredictions.data ?? [];

  // Derive a representative BTC price from the first snapshot
  const btcPrice = predictions.length > 0
    ? parseFloat(predictions[0].price_usd)
    : null;

  return (
    <div className="p-6">
      {/* Top Stats Row */}
      <div className="mb-8 grid grid-cols-4 gap-4">
        {/* Total Balance */}
        <div className="animate-fade-in stagger-1 rounded-lg border border-border-subtle bg-bg-card p-5">
          <p className="text-xs text-text-muted">总资产</p>
          {balance.isLoading ? (
            <Shimmer className="mt-2 h-8 w-28" />
          ) : balance.error ? (
            <p className="mt-1 font-mono text-2xl font-semibold text-loss">—</p>
          ) : (
            <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
              ${totalAssets != null ? parseFloat(String(totalAssets)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—"}
            </p>
          )}
        </div>

        {/* PnL */}
        <div className="animate-fade-in stagger-2 rounded-lg border border-border-subtle bg-bg-card p-5">
          <p className="text-xs text-text-muted">今日盈亏</p>
          {pnl.isLoading ? (
            <Shimmer className="mt-2 h-8 w-28" />
          ) : pnl.error ? (
            <p className="mt-1 font-mono text-2xl font-semibold text-loss">—</p>
          ) : (
            <>
              <p className={`mt-1 font-mono text-2xl font-semibold ${todayPnl != null && parseFloat(String(todayPnl)) >= 0 ? "text-profit" : "text-loss"}`}>
                {todayPnl != null
                  ? `${parseFloat(String(todayPnl)) >= 0 ? "+" : ""}$${Math.abs(parseFloat(String(todayPnl))).toFixed(2)}`
                  : "—"}
              </p>
              {unrealizedPnl != null && (
                <p className={`mt-1 text-sm ${parseFloat(String(unrealizedPnl)) >= 0 ? "text-profit" : "text-loss"}`}>
                  unrealized: {parseFloat(String(unrealizedPnl)) >= 0 ? "+" : ""}${Math.abs(parseFloat(String(unrealizedPnl))).toFixed(2)}
                </p>
              )}
            </>
          )}
        </div>

        {/* Active Positions count */}
        <div className="animate-fade-in stagger-3 rounded-lg border border-border-subtle bg-bg-card p-5">
          <p className="text-xs text-text-muted">活跃仓位</p>
          {positions.isLoading ? (
            <Shimmer className="mt-2 h-8 w-16" />
          ) : positions.error ? (
            <p className="mt-1 font-mono text-2xl font-semibold text-loss">—</p>
          ) : (
            <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
              {activePositions.length}
            </p>
          )}
        </div>

        {/* Available / Locked */}
        <div className="animate-fade-in stagger-4 rounded-lg border border-border-subtle bg-bg-card p-5">
          <p className="text-xs text-text-muted">可用 / 锁定</p>
          {balance.isLoading ? (
            <Shimmer className="mt-2 h-8 w-28" />
          ) : balance.error ? (
            <p className="mt-1 font-mono text-2xl font-semibold text-loss">—</p>
          ) : (
            <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
              ${balance.data?.available != null ? parseFloat(String(balance.data.available)).toFixed(0) : "—"}{" "}
              <span className="text-sm font-normal text-text-muted">
                / ${balance.data?.locked != null ? parseFloat(String(balance.data.locked)).toFixed(0) : "—"}
              </span>
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* AI Discoveries — live from /analysis/scan */}
        <div className="gradient-border-gold col-span-3 rounded-lg border border-accent-gold/20 bg-bg-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-text-primary">
              <span className="text-accent-gold">◆</span> AI 发现
              <span className="rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] text-accent-gold">
                独家
              </span>
            </h2>
            <span className="text-xs text-text-muted">
              {aiScan.isLoading ? "Scanning…" : `${discoveries.length} 个定价偏差机会`}
            </span>
          </div>
          <div className="space-y-3">
            {aiScan.isLoading ? (
              <>
                <Shimmer className="h-12 w-full" />
                <Shimmer className="h-12 w-full" />
              </>
            ) : aiScan.error ? (
              <div className="rounded border border-border-subtle bg-bg-base p-3 text-sm text-text-muted">
                AI scan unavailable
              </div>
            ) : discoveries.length === 0 ? (
              <div className="rounded border border-border-subtle bg-bg-base p-3 text-sm text-text-muted">
                No bias opportunities detected
              </div>
            ) : (
              discoveries.slice(0, 5).map((item) => (
                <div
                  key={item.market_id}
                  className="flex items-center justify-between rounded border border-border-subtle bg-bg-base p-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="rounded bg-bg-elevated px-2 py-0.5 font-mono text-[10px] text-text-muted">
                      {item.bias_direction}
                    </span>
                    <span className="text-sm text-text-primary">
                      {item.question
                        ? item.question.length > 50
                          ? item.question.slice(0, 50) + "…"
                          : item.question
                        : item.market_id}
                    </span>
                  </div>
                  <span className="font-mono text-sm text-accent-gold">
                    {item.bias_bps > 0 ? "+" : ""}{item.bias_bps}bps
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* NBA Live */}
        <div className="animate-fade-in stagger-1 col-span-1 rounded-lg border border-border-subtle bg-bg-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-text-primary">
            🏀 NBA 实况
            <span className="rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] text-accent-gold">
              PRO
            </span>
            <span className="live-dot ml-1 h-1.5 w-1.5 rounded-full bg-profit" />
          </h2>
          {nbaGames.isLoading ? (
            <div className="space-y-4">
              <Shimmer className="h-16 w-full" />
              <Shimmer className="h-16 w-full" />
            </div>
          ) : nbaGames.error ? (
            <p className="text-sm text-loss">Failed to load games</p>
          ) : games.length === 0 ? (
            <p className="text-sm text-text-muted">No games available</p>
          ) : (
            <div className="space-y-4">
              {games.slice(0, 3).map((game) => (
                <div
                  key={game.game_id}
                  className="rounded border border-border-subtle bg-bg-base p-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm text-text-primary">
                      {game.home_team} {game.score_home} - {game.score_away} {game.away_team}
                    </span>
                    <span className="text-xs text-info-cyan">
                      {game.quarter} {game.time_remaining}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-text-muted">
                    ID: {game.game_id}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* BTC Predictions */}
        <div className="animate-fade-in stagger-2 col-span-1 rounded-lg border border-border-subtle bg-bg-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-text-primary">
            ₿ BTC 预测
            <span className="rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] text-accent-gold">
              PRO
            </span>
            <span className="live-dot ml-1 h-1.5 w-1.5 rounded-full bg-profit" />
          </h2>
          {btcPredictions.isLoading ? (
            <>
              <Shimmer className="mb-4 h-7 w-32" />
              <div className="space-y-2">
                {[0, 1, 2, 3].map((i) => <Shimmer key={i} className="h-8 w-full" />)}
              </div>
            </>
          ) : btcPredictions.error ? (
            <p className="text-sm text-loss">Failed to load BTC predictions</p>
          ) : (
            <>
              <p className="mb-4 font-mono text-xl text-text-primary">
                {btcPrice != null ? `$${btcPrice.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : "—"}
              </p>
              <div className="space-y-2">
                {predictions.length === 0 ? (
                  <p className="text-sm text-text-muted">No data available</p>
                ) : (
                  predictions.map((snap) => {
                    const prob = parseFloat(snap.prediction_prob ?? "0.5");
                    const isUp = prob > 0.5;
                    return (
                      <div
                        key={snap.timeframe}
                        className="flex items-center justify-between rounded border border-border-subtle bg-bg-base p-2"
                      >
                        <span className="font-mono text-xs text-text-muted">
                          {snap.timeframe}
                        </span>
                        <span className={`font-mono text-sm ${isUp ? "text-profit" : "text-loss"}`}>
                          {isUp ? "▲" : "▼"} {prob.toFixed(2)}
                        </span>
                      </div>
                    );
                  })
                )}
              </div>
            </>
          )}
        </div>

        {/* Active Positions */}
        <div className="animate-fade-in stagger-3 col-span-1 rounded-lg border border-border-subtle bg-bg-card p-6">
          <h2 className="mb-4 text-sm font-semibold text-text-primary">
            活跃仓位
          </h2>
          {positions.isLoading ? (
            <div className="space-y-2">
              {[0, 1, 2].map((i) => <Shimmer key={i} className="h-8 w-full" />)}
            </div>
          ) : positions.error ? (
            <p className="text-sm text-loss">Failed to load positions</p>
          ) : activePositions.length === 0 ? (
            <p className="text-sm text-text-muted">No active positions</p>
          ) : (
            <div className="space-y-2">
              {activePositions.slice(0, 5).map((pos) => {
                const notional = parseFloat(String(pos.notional));
                const isPositive = notional >= 0;
                return (
                  <div
                    key={pos.market_id}
                    className="flex items-center justify-between rounded border border-border-subtle bg-bg-base p-2"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`rounded px-1.5 py-0.5 font-mono text-[10px] ${pos.side === "BUY" ? "bg-profit-bg text-profit" : "bg-loss-bg text-loss"}`}>
                        {pos.side}
                      </span>
                      <span className="truncate text-sm text-text-primary max-w-[100px]">
                        {pos.market_id}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className={`font-mono text-sm ${isPositive ? "text-profit" : "text-loss"}`}>
                        {isPositive ? "+" : ""}${Math.abs(notional).toFixed(2)}
                      </span>
                      <p className="font-mono text-[10px] text-text-muted">
                        {parseFloat(String(pos.size_held)).toFixed(0)} @ {parseFloat(String(pos.avg_price)).toFixed(2)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
