"use client";

import { useState } from "react";
import { useBtcPredictions } from "@/lib/hooks/use-btc";
import { useBtcLive } from "@/lib/hooks/use-btc-live";

// ── Sub-components ────────────────────────────────────────────────────────────

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-bg-elevated ${className}`} />
  );
}

function formatVolume(raw: string): string {
  const n = parseFloat(raw);
  if (isNaN(n)) return raw;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toFixed(0);
}

interface TimeframeCardData {
  timeframe: string;
  price_usd: string;
  prediction_prob: string | null;
  volume: string | null;
  recorded_at: string | null;
}

function TimeframeCard({ tf }: { tf: TimeframeCardData }) {
  const prob = parseFloat(tf.prediction_prob ?? "0.5");
  const isUp = prob > 0.5;
  return (
    <div className="flex flex-col rounded-lg border border-border-subtle bg-bg-card p-4 transition-colors hover:border-accent-gold/30">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-mono text-xs font-semibold text-text-muted">
          {tf.timeframe}
        </span>
        <span className={`text-lg font-bold ${isUp ? "text-profit" : "text-loss"}`}>
          {isUp ? "▲" : "▼"}
        </span>
      </div>
      <p className={`font-mono text-2xl font-bold ${isUp ? "text-profit" : "text-loss"}`}>
        {prob.toFixed(2)}
      </p>
      <p className="mt-0.5 text-sm font-medium text-text-secondary">
        {isUp ? "Bullish" : "Bearish"}
      </p>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-text-muted">
          vol:{" "}
          <span className="font-mono text-text-secondary">{formatVolume(tf.volume ?? "0")}</span>
        </span>
      </div>
      {/* mini bar */}
      <div className="mt-2 h-1.5 rounded-full bg-bg-base">
        <div
          className={`h-full rounded-full transition-all ${isUp ? "bg-profit" : "bg-loss"}`}
          style={{ width: `${prob * 100}%` }}
        />
      </div>
      <button className="mt-3 rounded border border-border-default bg-bg-elevated px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:border-accent-gold/40 hover:text-text-primary">
        Trade →
      </button>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function BTCPage() {
  const { data: restPredictions, isLoading, error } = useBtcPredictions();  // REST fallback
  const { data: livePredictions, isConnected } = useBtcLive();              // WebSocket real-time

  // Prefer WebSocket data when available, fall back to REST
  const predictions = livePredictions.length > 0 ? livePredictions : restPredictions;

  const [activeTimeframe, setActiveTimeframe] = useState("1h");

  // Derive BTC price from the first snapshot
  const btcPrice = predictions && predictions.length > 0
    ? parseFloat(predictions[0].price_usd)
    : null;

  // Build chart points from prediction probs (mapped to price approximation)
  const CHART_POINTS = [67800, 67950, 68100, 68050, 68300, 68250, 68400, 68350, 68500, btcPrice ?? 68420];
  const minPrice = Math.min(...CHART_POINTS);
  const maxPrice = Math.max(...CHART_POINTS);
  const range = maxPrice - minPrice || 1;

  // Timeframe labels for chart tabs
  const timeframeLabels = predictions ? predictions.map((p) => p.timeframe) : ["5m", "15m", "1h", "4h"];

  return (
    <div className="flex min-h-full flex-col gap-0 p-6">
      {/* ── BTC Header ───────────────────────────────────── */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl text-accent-gold">₿</span>
          <div>
            <h1 className="text-lg font-semibold text-text-primary">
              Bitcoin Prediction Markets
            </h1>
            <p className="text-xs text-text-muted">
              Multi-timeframe probability analysis
            </p>
          </div>
          <span className="rounded bg-accent-gold-bg px-2 py-0.5 text-[10px] font-semibold text-accent-gold">
            PRO
          </span>
        </div>
        <div className="flex items-center gap-3">
          {/* WebSocket connection indicator */}
          {isConnected ? (
            <span className="flex items-center gap-1.5 rounded bg-profit-bg px-2 py-0.5 text-[10px] font-semibold text-profit">
              <span className="h-1.5 w-1.5 rounded-full bg-profit" />
              WS LIVE
            </span>
          ) : (
            <span className="flex items-center gap-1.5 rounded bg-bg-elevated px-2 py-0.5 text-[10px] text-text-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-text-muted" />
              polling
            </span>
          )}
          <div className="text-right">
            {isLoading && livePredictions.length === 0 ? (
              <Skeleton className="h-8 w-28" />
            ) : btcPrice != null ? (
              <>
                <p className="font-mono text-2xl font-bold text-text-primary">
                  ${btcPrice.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </p>
                <p className="font-mono text-sm text-text-muted">Live</p>
              </>
            ) : (
              <p className="font-mono text-2xl font-bold text-text-primary">—</p>
            )}
          </div>
        </div>
      </div>

      {/* ── 4 Timeframe Cards ─────────────────────────────── */}
      {isLoading && livePredictions.length === 0 ? (
        <div className="mb-6 grid grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-44 w-full rounded-lg" />
          ))}
        </div>
      ) : error && livePredictions.length === 0 ? (
        <div className="mb-6 rounded-lg border border-border-subtle bg-bg-card p-6">
          <p className="text-sm text-loss">Failed to load BTC predictions</p>
        </div>
      ) : !predictions || predictions.length === 0 ? (
        <div className="mb-6 rounded-lg border border-border-subtle bg-bg-card p-6">
          <p className="text-sm text-text-muted">No data available</p>
        </div>
      ) : (
        <div className="mb-6 grid grid-cols-4 gap-4">
          {predictions.map((tf) => (
            <TimeframeCard key={tf.timeframe} tf={tf} />
          ))}
        </div>
      )}

      {/* ── Chart Placeholder ─────────────────────────────── */}
      <div className="mb-6 rounded-lg border border-border-subtle bg-bg-card p-5">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            BTC Price × Prediction Probability
          </p>
          <div className="flex gap-2">
            {timeframeLabels.map((label) => (
              <button
                key={label}
                onClick={() => setActiveTimeframe(label)}
                className={`rounded px-2 py-0.5 font-mono text-[10px] transition-colors ${
                  activeTimeframe === label
                    ? "bg-accent-gold text-bg-base"
                    : "bg-bg-elevated text-text-muted hover:text-text-primary"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* SVG-based price chart placeholder */}
        <div className="relative h-48 rounded border border-border-subtle bg-bg-base p-3">
          <svg
            className="h-full w-full"
            viewBox="0 0 400 150"
            preserveAspectRatio="none"
          >
            {/* Grid lines */}
            {[0, 1, 2, 3].map((i) => (
              <line
                key={i}
                x1="0"
                y1={i * 37.5}
                x2="400"
                y2={i * 37.5}
                stroke="var(--border-subtle)"
                strokeWidth="0.5"
              />
            ))}
            {/* Price line */}
            <polyline
              fill="none"
              stroke="var(--info-cyan)"
              strokeWidth="2"
              points={CHART_POINTS.map((p, i) => {
                const x = (i / (CHART_POINTS.length - 1)) * 400;
                const y = 150 - ((p - minPrice) / range) * 130 - 10;
                return `${x},${y}`;
              }).join(" ")}
            />
            {/* Area fill */}
            <polyline
              fill="url(#btcGradient)"
              fillOpacity="0.15"
              stroke="none"
              points={[
                ...CHART_POINTS.map((p, i) => {
                  const x = (i / (CHART_POINTS.length - 1)) * 400;
                  const y = 150 - ((p - minPrice) / range) * 130 - 10;
                  return `${x},${y}`;
                }),
                "400,150",
                "0,150",
              ].join(" ")}
            />
            <defs>
              <linearGradient id="btcGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--info-cyan)" />
                <stop offset="100%" stopColor="var(--info-cyan)" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
          {/* Labels */}
          <div className="pointer-events-none absolute inset-0 flex items-end justify-between px-3 pb-2">
            <span className="font-mono text-[10px] text-text-muted">
              ${minPrice.toLocaleString()}
            </span>
            <span className="font-mono text-[10px] text-text-muted">
              ${maxPrice.toLocaleString()}
            </span>
          </div>
          <div className="pointer-events-none absolute right-3 top-3">
            <span className="font-mono text-[10px] text-info-cyan">
              {activeTimeframe} chart
            </span>
          </div>
        </div>

        <div className="mt-2 flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-[10px] text-text-muted">
            <span className="inline-block h-0.5 w-4 bg-info-cyan" /> BTC Price
          </span>
          <span className="flex items-center gap-1.5 text-[10px] text-text-muted">
            <span className="inline-block h-0.5 w-4 bg-accent-gold" />{" "}
            Prediction Prob
          </span>
        </div>
      </div>

      {/* ── Snapshots Table (replaces On-chain Trades with real recorded_at data) */}
      <div className="rounded-lg border border-border-subtle bg-bg-card">
        <div className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Prediction Snapshots
          </p>
          <span className="flex items-center gap-1.5">
            <span className={`h-1.5 w-1.5 rounded-full ${isConnected ? "bg-profit" : "bg-text-muted"}`} />
            <span className="text-[10px] text-text-muted">{isConnected ? "Live" : "Polling"}</span>
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle">
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Timeframe
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Price (USD)
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Prediction
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Direction
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Volume
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Recorded At
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading && livePredictions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center">
                    <Skeleton className="mx-auto h-4 w-48" />
                  </td>
                </tr>
              ) : error && livePredictions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-sm text-loss">
                    Failed to load data
                  </td>
                </tr>
              ) : !predictions || predictions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-sm text-text-muted">
                    No data available
                  </td>
                </tr>
              ) : (
                predictions.map((snap) => {
                  const prob = parseFloat(snap.prediction_prob ?? "0.5");
                  const isUp = prob > 0.5;
                  const price = parseFloat(snap.price_usd);
                  const recordedAt = snap.recorded_at ? new Date(snap.recorded_at) : null;
                  const timeStr = recordedAt && !isNaN(recordedAt.getTime())
                    ? recordedAt.toLocaleTimeString()
                    : (snap.recorded_at ?? "—");
                  return (
                    <tr
                      key={snap.timeframe}
                      className="border-b border-border-subtle/50 transition-colors hover:bg-bg-elevated last:border-0"
                    >
                      <td className="px-5 py-2.5 font-mono text-sm text-text-primary">
                        {snap.timeframe}
                      </td>
                      <td className="px-5 py-2.5 font-mono text-sm text-text-secondary">
                        ${price.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </td>
                      <td className="px-5 py-2.5 font-mono text-sm text-text-primary">
                        {prob.toFixed(2)}
                      </td>
                      <td className="px-5 py-2.5">
                        <span className={`rounded px-2 py-0.5 font-mono text-[10px] font-semibold ${isUp ? "bg-profit-bg text-profit" : "bg-loss-bg text-loss"}`}>
                          {isUp ? "BULL" : "BEAR"}
                        </span>
                      </td>
                      <td className="px-5 py-2.5 font-mono text-sm text-text-secondary">
                        {formatVolume(snap.volume ?? "0")}
                      </td>
                      <td className="px-5 py-2.5 font-mono text-xs text-text-muted">
                        {timeStr}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
