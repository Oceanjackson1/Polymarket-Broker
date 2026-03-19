"use client";

import { useState } from "react";

// ── Mock data ─────────────────────────────────────────────────────────────────

const BTC_PRICE = 68420;
const BTC_CHANGE = "+1.2%";

const TIMEFRAMES = [
  {
    label: "5m",
    prob: 0.61,
    direction: "up" as const,
    volume: "45K",
    marketId: "btc-5m",
  },
  {
    label: "15m",
    prob: 0.48,
    direction: "down" as const,
    volume: "32K",
    marketId: "btc-15m",
  },
  {
    label: "1h",
    prob: 0.55,
    direction: "up" as const,
    volume: "89K",
    marketId: "btc-1h",
  },
  {
    label: "4h",
    prob: 0.62,
    direction: "up" as const,
    volume: "12K",
    marketId: "btc-4h",
  },
];

const ONCHAIN_TRADES = [
  {
    price: 0.62,
    size: 500,
    side: "BUY" as const,
    time: "10:04:22.331",
    txHash: "0x3a4f...8c21",
  },
  {
    price: 0.61,
    size: 200,
    side: "SELL" as const,
    time: "10:04:21.887",
    txHash: "0x7f9b...1d4e",
  },
  {
    price: 0.63,
    size: 1000,
    side: "BUY" as const,
    time: "10:04:20.442",
    txHash: "0xa2c1...5f3b",
  },
  {
    price: 0.60,
    size: 350,
    side: "SELL" as const,
    time: "10:04:19.113",
    txHash: "0xd8e4...9a72",
  },
  {
    price: 0.62,
    size: 800,
    side: "BUY" as const,
    time: "10:04:17.559",
    txHash: "0x51b7...c8f0",
  },
  {
    price: 0.61,
    size: 150,
    side: "BUY" as const,
    time: "10:04:15.204",
    txHash: "0x93d2...7e1a",
  },
];

// Simple price chart placeholder data
const CHART_POINTS = [
  67800, 67950, 68100, 68050, 68300, 68250, 68400, 68350, 68500, 68420,
];

// ── Sub-components ────────────────────────────────────────────────────────────

function TimeframeCard({
  tf,
}: {
  tf: (typeof TIMEFRAMES)[0];
}) {
  const isUp = tf.direction === "up";
  return (
    <div className="flex flex-col rounded-lg border border-border-subtle bg-bg-card p-4 transition-colors hover:border-accent-gold/30">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-mono text-xs font-semibold text-text-muted">
          {tf.label}
        </span>
        <span
          className={`text-lg font-bold ${isUp ? "text-profit" : "text-loss"}`}
        >
          {isUp ? "▲" : "▼"}
        </span>
      </div>
      <p
        className={`font-mono text-2xl font-bold ${isUp ? "text-profit" : "text-loss"}`}
      >
        {tf.prob.toFixed(2)}
      </p>
      <p className="mt-0.5 text-sm font-medium text-text-secondary">
        {isUp ? "Bullish" : "Bearish"}
      </p>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-text-muted">
          vol:{" "}
          <span className="font-mono text-text-secondary">{tf.volume}</span>
        </span>
      </div>
      {/* mini bar */}
      <div className="mt-2 h-1.5 rounded-full bg-bg-base">
        <div
          className={`h-full rounded-full transition-all ${isUp ? "bg-profit" : "bg-loss"}`}
          style={{ width: `${tf.prob * 100}%` }}
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
  const [activeTimeframe, setActiveTimeframe] = useState("1h");

  const minPrice = Math.min(...CHART_POINTS);
  const maxPrice = Math.max(...CHART_POINTS);
  const range = maxPrice - minPrice;

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
        <div className="text-right">
          <p className="font-mono text-2xl font-bold text-text-primary">
            ${BTC_PRICE.toLocaleString()}
          </p>
          <p className="font-mono text-sm text-profit">{BTC_CHANGE}</p>
        </div>
      </div>

      {/* ── 4 Timeframe Cards ─────────────────────────────── */}
      <div className="mb-6 grid grid-cols-4 gap-4">
        {TIMEFRAMES.map((tf) => (
          <TimeframeCard key={tf.label} tf={tf} />
        ))}
      </div>

      {/* ── Chart Placeholder ─────────────────────────────── */}
      <div className="mb-6 rounded-lg border border-border-subtle bg-bg-card p-5">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            BTC Price × Prediction Probability
          </p>
          <div className="flex gap-2">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.label}
                onClick={() => setActiveTimeframe(tf.label)}
                className={`rounded px-2 py-0.5 font-mono text-[10px] transition-colors ${
                  activeTimeframe === tf.label
                    ? "bg-accent-gold text-bg-base"
                    : "bg-bg-elevated text-text-muted hover:text-text-primary"
                }`}
              >
                {tf.label}
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

      {/* ── On-chain Trades Table ─────────────────────────── */}
      <div className="rounded-lg border border-border-subtle bg-bg-card">
        <div className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            On-chain Trades
          </p>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-profit" />
            <span className="text-[10px] text-text-muted">Live</span>
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle">
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Price
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Size
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Side
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  Time
                </th>
                <th className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                  TxHash
                </th>
              </tr>
            </thead>
            <tbody>
              {ONCHAIN_TRADES.map((trade, i) => (
                <tr
                  key={i}
                  className="border-b border-border-subtle/50 transition-colors hover:bg-bg-elevated last:border-0"
                >
                  <td className="px-5 py-2.5 font-mono text-sm text-text-primary">
                    {trade.price.toFixed(2)}
                  </td>
                  <td className="px-5 py-2.5 font-mono text-sm text-text-secondary">
                    {trade.size}
                  </td>
                  <td className="px-5 py-2.5">
                    <span
                      className={`rounded px-2 py-0.5 font-mono text-[10px] font-semibold ${
                        trade.side === "BUY"
                          ? "bg-profit-bg text-profit"
                          : "bg-loss-bg text-loss"
                      }`}
                    >
                      {trade.side}
                    </span>
                  </td>
                  <td className="px-5 py-2.5 font-mono text-xs text-text-muted">
                    {trade.time}
                  </td>
                  <td className="px-5 py-2.5 font-mono text-xs text-info-cyan">
                    {trade.txHash}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
