"use client";

import { useState } from "react";

// ── Mock data ─────────────────────────────────────────────────────────────────

const MOCK_GAME = {
  id: "gsw-lal-20260319",
  homeTeam: "Golden State Warriors",
  homeTeamShort: "GSW",
  awayTeam: "Los Angeles Lakers",
  awayTeamShort: "LAL",
  homeScore: 94,
  awayScore: 87,
  quarter: "Q3",
  clock: "4:22",
  homeWinProb: 0.31,
  awayWinProb: 0.69,
  lastTrade: 0.69,
  biasDirection: "HOME_UNDERPRICED" as const,
  biasMagnitudeBps: 420,
  aiSuggestion: "Buy GSW @ 0.31",
  orderBook: {
    bids: [
      { price: 0.3, size: 800 },
      { price: 0.29, size: 1200 },
      { price: 0.28, size: 600 },
    ],
    asks: [
      { price: 0.32, size: 500 },
      { price: 0.33, size: 900 },
      { price: 0.34, size: 400 },
    ],
  },
};

const TIMELINE_PLACEHOLDER = [
  { time: "Q1 12:00", homeOdds: 0.5, score: "0-0" },
  { time: "Q1 6:00", homeOdds: 0.45, score: "14-18" },
  { time: "Q2 12:00", homeOdds: 0.42, score: "28-35" },
  { time: "Q2 6:00", homeOdds: 0.38, score: "41-52" },
  { time: "Q3 12:00", homeOdds: 0.35, score: "58-67" },
  { time: "Q3 4:22", homeOdds: 0.31, score: "94-87" },
];

// ── Sub-components ────────────────────────────────────────────────────────────

function SignalBar({ magnitude }: { magnitude: number }) {
  // Max meaningful magnitude ~600bps → full bar
  const pct = Math.min((magnitude / 600) * 100, 100);
  const bars = Math.round((pct / 100) * 12);
  const filled = "█".repeat(bars);
  const empty = "░".repeat(12 - bars);
  const label =
    magnitude > 400 ? "Strong" : magnitude > 200 ? "Moderate" : "Weak";
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

// ── Main page ─────────────────────────────────────────────────────────────────

export default function NBAGamePage() {
  const game = MOCK_GAME;
  const [tradeSize, setTradeSize] = useState("100");

  return (
    <div className="flex min-h-full flex-col gap-0">
      {/* ── Score Banner ─────────────────────────────────── */}
      <div className="border-b border-border-subtle bg-bg-card px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-lg">🏀</span>
            <span className="rounded bg-accent-gold-bg px-2 py-0.5 text-[10px] font-semibold text-accent-gold">
              LIVE
            </span>
          </div>
          <div className="flex flex-1 items-center justify-center gap-8">
            <div className="text-right">
              <p className="text-sm text-text-secondary">{game.homeTeam}</p>
              <p className="font-mono text-4xl font-bold text-text-primary">
                {game.homeScore}
              </p>
            </div>
            <div className="text-center">
              <p className="font-mono text-xs text-text-muted">
                {game.quarter}
              </p>
              <p className="font-mono text-2xl font-semibold text-info-cyan">
                {game.clock}
              </p>
            </div>
            <div className="text-left">
              <p className="text-sm text-text-secondary">{game.awayTeam}</p>
              <p className="font-mono text-4xl font-bold text-text-primary">
                {game.awayScore}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-text-muted">Game ID</p>
            <p className="font-mono text-xs text-text-secondary">{game.id}</p>
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
                {game.homeTeamShort} Win
              </span>
              <div className="text-right">
                <span className="font-mono text-xl font-bold text-text-primary">
                  {game.homeWinProb.toFixed(2)}
                </span>
                <span className="ml-2 font-mono text-sm text-text-muted">
                  ({(game.homeWinProb * 100).toFixed(0)}%)
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded border border-border-default bg-bg-card px-4 py-3">
              <span className="text-sm text-text-secondary">
                {game.awayTeamShort} Win
              </span>
              <div className="text-right">
                <span className="font-mono text-xl font-bold text-text-primary">
                  {game.awayWinProb.toFixed(2)}
                </span>
                <span className="ml-2 font-mono text-sm text-text-muted">
                  ({(game.awayWinProb * 100).toFixed(0)}%)
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between px-1 pt-1">
              <span className="text-xs text-text-muted">Last Trade</span>
              <span className="font-mono text-sm text-info-cyan">
                {game.lastTrade.toFixed(2)}
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
                {game.biasDirection}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-muted">Magnitude</span>
              <span className="font-mono text-sm text-accent-gold">
                +{game.biasMagnitudeBps} bps
              </span>
            </div>
            <div>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs text-text-muted">Signal Strength</span>
              </div>
              <SignalBar magnitude={game.biasMagnitudeBps} />
            </div>
            <div className="rounded border border-accent-gold/20 bg-accent-gold-bg/20 p-3">
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-accent-gold">
                AI Recommendation
              </p>
              <p className="font-mono text-sm text-text-primary">
                {game.aiSuggestion}
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
              BTC Price × Prediction Probability
            </p>
            <p className="text-[10px] text-text-muted">
              (dual Y-axis chart placeholder)
            </p>
          </div>
        </div>
        <div className="mt-2 flex items-center justify-end gap-4">
          <span className="flex items-center gap-1.5 text-[10px] text-text-muted">
            <span className="inline-block h-2 w-3 rounded-sm bg-info-blue/60" />
            {game.awayTeamShort} Win Prob
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
                Buy {game.homeTeamShort} Win @{" "}
                <span className="text-accent-gold">
                  {game.homeWinProb.toFixed(2)}
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
                    ((1 - game.homeWinProb) / game.homeWinProb)
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

        {/* Order Book */}
        <div className="bg-bg-base p-5">
          <p className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Order Book — {game.homeTeamShort} Win
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
            {/* Rows */}
            {[0, 1, 2].map((i) => {
              const bid = game.orderBook.bids[i];
              const ask = game.orderBook.asks[i];
              return (
                <div
                  key={i}
                  className="grid grid-cols-4 border-b border-border-subtle/50 px-3 py-1.5 text-xs last:border-0"
                >
                  <span className="font-mono text-profit">
                    {bid.price.toFixed(2)}
                  </span>
                  <span className="font-mono text-text-muted">{bid.size}</span>
                  <span className="text-right font-mono text-loss">
                    {ask.price.toFixed(2)}
                  </span>
                  <span className="text-right font-mono text-text-muted">
                    {ask.size}
                  </span>
                </div>
              );
            })}
            {/* Spread */}
            <div className="flex items-center justify-center px-3 py-2">
              <span className="text-[10px] text-text-muted">
                Spread:{" "}
                <span className="font-mono text-text-secondary">
                  {(
                    game.orderBook.asks[0].price - game.orderBook.bids[0].price
                  ).toFixed(2)}
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
