"use client";

import { useState } from "react";

const opportunities = [
  {
    id: "opp-1",
    market: "GSW vs LAL — Home Win",
    probability: "0.31",
    modelProb: "0.43",
    expiry: "Mar 19, 23:30 UTC",
    spread: "+420 bps",
    side: "BUY",
  },
  {
    id: "opp-2",
    market: "BTC >$70k by Mar 21",
    probability: "0.48",
    modelProb: "0.61",
    expiry: "Mar 21, 00:00 UTC",
    spread: "+310 bps",
    side: "BUY",
  },
  {
    id: "opp-3",
    market: "UFC 300 — Main Event KO",
    probability: "0.55",
    modelProb: "0.42",
    expiry: "Mar 20, 04:00 UTC",
    spread: "-260 bps",
    side: "SELL",
  },
  {
    id: "opp-4",
    market: "BOS vs MIA — Away Win",
    probability: "0.38",
    modelProb: "0.51",
    expiry: "Mar 19, 02:00 UTC",
    spread: "+380 bps",
    side: "BUY",
  },
  {
    id: "opp-5",
    market: "ETH >$4k by Mar 22",
    probability: "0.29",
    modelProb: "0.41",
    expiry: "Mar 22, 00:00 UTC",
    spread: "+290 bps",
    side: "BUY",
  },
];

const activePositions = [
  {
    id: "pos-1",
    market: "Trump wins 2028",
    side: "BUY",
    size: "$500",
    entryProb: "0.42",
    currentProb: "0.47",
    pnl: "+$24",
  },
  {
    id: "pos-2",
    market: "BTC >$70k 1h",
    side: "BUY",
    size: "$200",
    entryProb: "0.55",
    currentProb: "0.61",
    pnl: "+$12",
  },
  {
    id: "pos-3",
    market: "GSW vs LAL Home",
    side: "BUY",
    size: "$150",
    entryProb: "0.29",
    currentProb: "0.31",
    pnl: "+$3",
  },
];

export default function StrategiesPage() {
  const [executing, setExecuting] = useState<string | null>(null);
  const [executed, setExecuted] = useState<Set<string>>(new Set());

  function handleExecute(id: string) {
    setExecuting(id);
    setTimeout(() => {
      setExecuting(null);
      setExecuted((prev) => new Set(prev).add(id));
    }, 1200);
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold text-text-primary">
            Convergence Arbitrage
          </h1>
          <span className="rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] font-medium text-accent-gold">
            PRO
          </span>
        </div>
        <p className="mt-1 text-sm text-text-secondary">
          Automated strategy execution when market prices diverge from model
          probabilities.
        </p>
      </div>

      {/* Strategy Explanation Card */}
      <div className="mb-8 rounded-lg border border-accent-gold/20 bg-bg-card p-6">
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-primary">
          <span className="text-accent-gold">◆</span> How It Works
        </h2>
        <div className="grid gap-6 md:grid-cols-3">
          {[
            {
              step: "01",
              title: "Signal Detection",
              body: "Our models continuously compare Polymarket prices against external probability estimates derived from live sports data, on-chain signals, and AI analysis.",
            },
            {
              step: "02",
              title: "Spread Calculation",
              body: "When the gap between market price and model probability exceeds a configurable threshold (default: 250 bps), an opportunity is flagged for execution.",
            },
            {
              step: "03",
              title: "Convergence Capture",
              body: "Positions are sized according to Kelly criterion. As markets correct toward fair value, the spread is captured as profit.",
            },
          ].map((item) => (
            <div key={item.step}>
              <div className="mb-2 font-mono text-xs text-accent-gold">
                {item.step}
              </div>
              <h3 className="mb-1 text-sm font-semibold text-text-primary">
                {item.title}
              </h3>
              <p className="text-xs leading-relaxed text-text-secondary">
                {item.body}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Opportunities Table */}
      <div className="mb-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">
            Live Opportunities
          </h2>
          <span className="font-mono text-xs text-text-muted">
            {opportunities.filter((o) => !executed.has(o.id)).length} available
          </span>
        </div>
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle bg-bg-card">
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">
                  Market
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Market Price
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Model Prob
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Spread
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">
                  Expiry
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {opportunities.map((opp) => (
                <tr
                  key={opp.id}
                  className={`border-b border-border-subtle bg-bg-base last:border-0 ${
                    executed.has(opp.id) ? "opacity-50" : ""
                  }`}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-medium ${
                          opp.side === "BUY"
                            ? "bg-profit-bg text-profit"
                            : "bg-loss-bg text-loss"
                        }`}
                      >
                        {opp.side}
                      </span>
                      <span className="text-sm text-text-primary">
                        {opp.market}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                    {opp.probability}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                    {opp.modelProb}
                  </td>
                  <td
                    className={`px-4 py-3 text-right font-mono text-sm font-medium ${
                      opp.spread.startsWith("+") ? "text-profit" : "text-loss"
                    }`}
                  >
                    {opp.spread}
                  </td>
                  <td className="px-4 py-3 text-sm text-text-muted">
                    {opp.expiry}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {executed.has(opp.id) ? (
                      <span className="text-xs text-profit">Executed ✓</span>
                    ) : (
                      <button
                        onClick={() => handleExecute(opp.id)}
                        disabled={executing === opp.id}
                        className="rounded-md bg-accent-gold px-3 py-1.5 text-xs font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover disabled:opacity-60"
                      >
                        {executing === opp.id ? "Executing…" : "Execute"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Active Positions */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">
            Active Positions
          </h2>
          <span className="font-mono text-xs text-text-muted">
            {activePositions.length} open
          </span>
        </div>
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle bg-bg-card">
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">
                  Market
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Side
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Size
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Entry
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Current
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  P&L
                </th>
              </tr>
            </thead>
            <tbody>
              {activePositions.map((pos) => (
                <tr
                  key={pos.id}
                  className="border-b border-border-subtle bg-bg-base last:border-0"
                >
                  <td className="px-4 py-3 text-sm text-text-primary">
                    {pos.market}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="rounded bg-profit-bg px-1.5 py-0.5 font-mono text-[10px] font-medium text-profit">
                      {pos.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                    {pos.size}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                    {pos.entryProb}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                    {pos.currentProb}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sm font-medium text-profit">
                    {pos.pnl}
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
