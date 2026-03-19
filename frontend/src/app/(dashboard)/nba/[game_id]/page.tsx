"use client";

import { use, useState } from "react";
import { useNbaFusion } from "@/lib/hooks/use-nba";
import { useNbaLive } from "@/lib/hooks/use-nba-live";

// ── Sub-components ────────────────────────────────────────────────────────────

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-bg-elevated ${className}`} />
  );
}

function SignalBar({ magnitude }: { magnitude: number | null }) {
  // Max meaningful magnitude ~600bps → full bar
  const pct = Math.min(((magnitude ?? 0) / 600) * 100, 100);
  const bars = Math.round((pct / 100) * 12);
  const filled = "█".repeat(bars);
  const empty = "░".repeat(12 - bars);
  const m = magnitude ?? 0;
  const label = m > 400 ? "Strong" : m > 200 ? "Moderate" : "Weak";
  return (
    <div className="flex items-center gap-2">
      <span className="font-mono text-sm text-accent-gold">
        {filled}
        <span className="text-border-default">{empty}</span>
      </span>
      <span className="text-xs text-text-muted">{label}</span>
    </div>
  );
}

function LiveBadge({ connected }: { connected: boolean }) {
  return connected ? (
    <span className="flex items-center gap-1 rounded bg-profit-bg px-2 py-0.5 text-[10px] font-semibold text-profit">
      <span className="h-1.5 w-1.5 rounded-full bg-profit" />
      LIVE
    </span>
  ) : (
    <span className="rounded bg-accent-gold-bg px-2 py-0.5 text-[10px] font-semibold text-accent-gold">
      LIVE
    </span>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function NBAGamePage({
  params,
}: {
  params: Promise<{ game_id: string }>;
}) {
  const { game_id: gameId } = use(params);
  const fusion = useNbaFusion(gameId);  // REST fallback — polled every 5s
  const live = useNbaLive(gameId);      // WebSocket real-time push
  const [tradeSize, setTradeSize] = useState("100");

  const { data, isLoading, error } = fusion;

  if (isLoading && !live.data) {
    return (
      <div className="flex min-h-full flex-col gap-0">
        <div className="border-b border-border-subtle bg-bg-card px-6 py-4">
          <Skeleton className="h-16 w-full" />
        </div>
        <div className="grid grid-cols-2 gap-0 border-b border-border-subtle">
          <div className="border-r border-border-subtle bg-bg-base p-5">
            <Skeleton className="h-32 w-full" />
          </div>
          <div className="bg-bg-base p-5">
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if ((error || !data) && !live.data) {
    return (
      <div className="flex min-h-full items-center justify-center p-6">
        <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center">
          <p className="text-sm text-loss">
            {error ? "Failed to load game data" : "Game not found"}
          </p>
          <p className="mt-1 font-mono text-xs text-text-muted">{gameId}</p>
        </div>
      </div>
    );
  }

  // Prefer WebSocket data when available, fall back to REST
  const score = live.data
    ? {
        home: live.data.score_home,
        away: live.data.score_away,
        quarter: live.data.quarter,
        time_remaining: live.data.time_remaining,
      }
    : data?.score ?? { home: null, away: null, quarter: null, time_remaining: null };

  const homeWinProb = live.data?.home_win_prob
    ?? (data ? parseFloat(String(data.polymarket.home_win_prob)) : 0);
  const awayWinProb = live.data?.away_win_prob
    ?? (data ? parseFloat(String(data.polymarket.away_win_prob)) : 0);
  const lastTrade = data ? parseFloat(String(data.polymarket.last_trade_price)) : 0;

  const biasDirection = live.data?.bias_direction ?? data?.bias_signal.direction;
  const magnitudeBps = live.data?.bias_magnitude_bps ?? data?.bias_signal.magnitude_bps;

  const isStale = !live.isConnected && (data?.stale ?? false);

  // Derive team abbreviations from game_id (fallback: HOME/AWAY)
  const parts = gameId.split("-");
  const homeShort = (parts[0] ?? "HOME").toUpperCase();
  const awayShort = (parts[1] ?? "AWAY").toUpperCase();

  const TIMELINE_PLACEHOLDER = [
    { time: "Q1 12:00", homeOdds: 0.5, score: "0-0" },
    { time: "Q1 6:00", homeOdds: 0.45, score: "14-18" },
    { time: "Q2 12:00", homeOdds: 0.42, score: "28-35" },
    { time: "Q2 6:00", homeOdds: 0.38, score: "41-52" },
    { time: "Q3 12:00", homeOdds: 0.35, score: "58-67" },
    { time: "Q4 4:22", homeOdds: homeWinProb, score: `${score.home}-${score.away}` },
  ];

  return (
    <div className="flex min-h-full flex-col gap-0">
      {/* ── Stale Warning Banner ─────────────────────────── */}
      {isStale && (
        <div className="border-b border-loss/30 bg-loss/10 px-6 py-2">
          <p className="text-xs text-loss">
            ⚠ Data may be stale — live feed connection interrupted
          </p>
        </div>
      )}

      {/* ── Score Banner ─────────────────────────────────── */}
      <div className="border-b border-border-subtle bg-bg-card px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-lg">🏀</span>
            <LiveBadge connected={live.isConnected} />
          </div>
          <div className="flex flex-1 items-center justify-center gap-8">
            <div className="text-right">
              <p className="text-sm text-text-secondary">{homeShort}</p>
              <p className="font-mono text-4xl font-bold text-text-primary">
                {score.home}
              </p>
            </div>
            <div className="text-center">
              <p className="font-mono text-xs text-text-muted">
                {score.quarter}
              </p>
              <p className="font-mono text-2xl font-semibold text-info-cyan">
                {score.time_remaining}
              </p>
            </div>
            <div className="text-left">
              <p className="text-sm text-text-secondary">{awayShort}</p>
              <p className="font-mono text-4xl font-bold text-text-primary">
                {score.away}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-text-muted">Game ID</p>
            <p className="font-mono text-xs text-text-secondary">{gameId}</p>
          </div>
        </div>
      </div>

      {/* ── Odds Panel + Bias Signal ──────────────────────── */}
      <div className="grid grid-cols-2 gap-0 border-b border-border-subtle">
        {/* Odds Panel */}
        <div className="border-r border-border-subtle bg-bg-base p-5">
          <p className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Polymarket Odds
          </p>
          <div className="space-y-3">
            <div className="flex items-center justify-between rounded border border-border-subtle bg-bg-card px-4 py-3">
              <span className="text-sm text-text-secondary">
                {homeShort} Win
              </span>
              <div className="text-right">
                <span className="font-mono text-xl font-bold text-text-primary">
                  {homeWinProb.toFixed(2)}
                </span>
                <span className="ml-2 font-mono text-sm text-text-muted">
                  ({(homeWinProb * 100).toFixed(0)}%)
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded border border-border-default bg-bg-card px-4 py-3">
              <span className="text-sm text-text-secondary">
                {awayShort} Win
              </span>
              <div className="text-right">
                <span className="font-mono text-xl font-bold text-text-primary">
                  {awayWinProb.toFixed(2)}
                </span>
                <span className="ml-2 font-mono text-sm text-text-muted">
                  ({(awayWinProb * 100).toFixed(0)}%)
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between px-1 pt-1">
              <span className="text-xs text-text-muted">Last Trade</span>
              <span className="font-mono text-sm text-info-cyan">
                {lastTrade.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Bias Signal */}
        <div className="bg-bg-base p-5">
          <p className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            AI Bias Signal
          </p>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-muted">Direction</span>
              <span className="rounded bg-profit-bg px-2 py-0.5 font-mono text-xs font-semibold text-profit">
                {biasDirection}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-muted">Magnitude</span>
              <span className="font-mono text-sm text-accent-gold">
                +{magnitudeBps} bps
              </span>
            </div>
            <div>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs text-text-muted">Signal Strength</span>
              </div>
              <SignalBar magnitude={magnitudeBps ?? null} />
            </div>
            <div className="rounded border border-accent-gold/20 bg-accent-gold-bg/20 p-3">
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-accent-gold">
                AI Recommendation
              </p>
              <p className="font-mono text-sm text-text-primary">
                {biasDirection === "HOME_UNDERPRICED"
                  ? `Buy ${homeShort} @ ${homeWinProb.toFixed(2)}`
                  : biasDirection === "AWAY_UNDERPRICED"
                  ? `Buy ${awayShort} @ ${awayWinProb.toFixed(2)}`
                  : "No clear trade signal"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Odds × Score Timeline placeholder ────────────── */}
      <div className="border-b border-border-subtle bg-bg-card p-5">
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
          Odds × Score Timeline
        </p>
        {/* Chart placeholder — no library */}
        <div className="flex h-40 items-end gap-1 rounded border border-border-subtle bg-bg-base px-4 py-3">
          {TIMELINE_PLACEHOLDER.map((point, i) => {
            const barH = Math.round((1 - point.homeOdds) * 100);
            return (
              <div
                key={i}
                className="group relative flex flex-1 flex-col items-center justify-end"
              >
                <div
                  className="w-full rounded-t bg-info-blue/40 transition-all group-hover:bg-info-blue/70"
                  style={{ height: `${barH}%` }}
                />
                <p className="mt-1 rotate-45 text-[9px] text-text-muted">
                  {point.time.split(" ")[1]}
                </p>
              </div>
            );
          })}
          <div className="absolute right-6 top-1/2 -translate-y-1/2 text-center">
            <p className="text-[10px] text-text-muted">
              Away Win Prob × Score Differential
            </p>
            <p className="text-[10px] text-text-muted">
              (dual Y-axis chart placeholder)
            </p>
          </div>
        </div>
        <div className="mt-2 flex items-center justify-end gap-4">
          <span className="flex items-center gap-1.5 text-[10px] text-text-muted">
            <span className="inline-block h-2 w-3 rounded-sm bg-info-blue/60" />
            {awayShort} Win Prob
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-text-muted">
            <span className="inline-block h-2 w-3 rounded-sm bg-accent-gold/60" />
            Score Differential
          </span>
        </div>
      </div>

      {/* ── Quick Trade + Order Book ──────────────────────── */}
      <div className="grid flex-1 grid-cols-2 gap-0">
        {/* Quick Trade */}
        <div className="border-r border-border-subtle bg-bg-base p-5">
          <p className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Quick Trade
          </p>
          <div className="rounded border border-accent-gold/20 bg-bg-card p-4">
            <div className="mb-4">
              <p className="mb-1 text-xs text-text-muted">Market</p>
              <p className="font-mono text-sm text-text-primary">
                Buy {homeShort} Win @{" "}
                <span className="text-accent-gold">
                  {homeWinProb.toFixed(2)}
                </span>
              </p>
            </div>
            <div className="mb-4">
              <label className="mb-1 block text-xs text-text-muted">
                Size (USDC)
              </label>
              <input
                type="number"
                value={tradeSize}
                onChange={(e) => setTradeSize(e.target.value)}
                className="w-full rounded border border-border-default bg-bg-elevated px-3 py-2 font-mono text-sm text-text-primary focus:border-accent-gold/50 focus:outline-none"
                min="1"
              />
            </div>
            <div className="mb-4 rounded bg-bg-base px-3 py-2">
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">Potential return</span>
                <span className="font-mono text-profit">
                  +$
                  {(
                    (parseFloat(tradeSize) || 0) *
                    ((1 - homeWinProb) / homeWinProb)
                  ).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-text-muted">Max loss</span>
                <span className="font-mono text-loss">
                  -${tradeSize || "0"}
                </span>
              </div>
            </div>
            <button className="w-full rounded bg-accent-gold px-4 py-2.5 text-sm font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover">
              Trade →
            </button>
          </div>
        </div>

        {/* Order Book — placeholder since no real order book data in fusion */}
        <div className="bg-bg-base p-5">
          <p className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Order Book — {homeShort} Win
          </p>
          <div className="rounded border border-border-subtle bg-bg-card">
            {/* Header */}
            <div className="grid grid-cols-4 border-b border-border-subtle px-3 py-2">
              <span className="col-span-2 text-[10px] font-semibold text-profit">
                BID
              </span>
              <span className="col-span-2 text-right text-[10px] font-semibold text-loss">
                ASK
              </span>
            </div>
            {/* Synthetic rows from win prob */}
            {[0, 1, 2].map((i) => {
              const bid = homeWinProb - (i + 1) * 0.01;
              const ask = homeWinProb + (i + 1) * 0.01;
              return (
                <div
                  key={i}
                  className="grid grid-cols-4 border-b border-border-subtle/50 px-3 py-1.5 text-xs last:border-0"
                >
                  <span className="font-mono text-profit">
                    {bid.toFixed(2)}
                  </span>
                  <span className="font-mono text-text-muted">—</span>
                  <span className="text-right font-mono text-loss">
                    {ask.toFixed(2)}
                  </span>
                  <span className="text-right font-mono text-text-muted">—</span>
                </div>
              );
            })}
            {/* Spread */}
            <div className="flex items-center justify-center px-3 py-2">
              <span className="text-[10px] text-text-muted">
                Spread:{" "}
                <span className="font-mono text-text-secondary">
                  0.02
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
