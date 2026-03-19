"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { strategiesApi } from "@/lib/api";

export default function StrategiesPage() {
  const queryClient = useQueryClient();

  const { data: opportunities, isLoading: oppsLoading } = useQuery({
    queryKey: ["convergence-opportunities"],
    queryFn: () => strategiesApi.opportunities(),
    staleTime: 30_000,
  });

  const { data: positions, isLoading: posLoading } = useQuery({
    queryKey: ["convergence-positions"],
    queryFn: () => strategiesApi.positions(),
    staleTime: 30_000,
  });

  const executeMutation = useMutation({
    mutationFn: ({ marketId, size }: { marketId: string; size: number }) =>
      strategiesApi.execute(marketId, size),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["convergence-opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["convergence-positions"] });
    },
  });

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
          Automated strategy execution when market prices diverge from model probabilities.
        </p>
      </div>

      {/* Strategy Explanation */}
      <div className="mb-8 rounded-lg border border-accent-gold/20 bg-bg-card p-6">
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-primary">
          <span className="text-accent-gold">◆</span> How It Works
        </h2>
        <div className="grid gap-6 md:grid-cols-3">
          {[
            { step: "01", title: "Signal Detection", body: "Models compare Polymarket prices against external probability estimates from live sports data, on-chain signals, and AI analysis." },
            { step: "02", title: "Spread Calculation", body: "When the gap exceeds a threshold (default: 250 bps), an opportunity is flagged." },
            { step: "03", title: "Convergence Capture", body: "Positions are sized via Kelly criterion. As markets correct toward fair value, the spread is captured as profit." },
          ].map((item) => (
            <div key={item.step}>
              <div className="mb-2 font-mono text-xs text-accent-gold">{item.step}</div>
              <h3 className="mb-1 text-sm font-semibold text-text-primary">{item.title}</h3>
              <p className="text-xs leading-relaxed text-text-secondary">{item.body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Opportunities Table */}
      <div className="mb-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">Live Opportunities</h2>
          <span className="font-mono text-xs text-text-muted">
            {oppsLoading ? "…" : `${opportunities?.length ?? 0} available`}
          </span>
        </div>

        {oppsLoading ? (
          <div className="space-y-px rounded-lg border border-border-subtle bg-bg-card">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-14 animate-pulse bg-bg-elevated" />
            ))}
          </div>
        ) : !opportunities || opportunities.length === 0 ? (
          <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-sm text-text-muted">
            No convergence opportunities detected. Markets are efficiently priced.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border-subtle">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-subtle bg-bg-card">
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">Market</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Current</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Fair Value</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Profit</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Action</th>
                </tr>
              </thead>
              <tbody>
                {opportunities.map((opp) => (
                  <tr key={opp.market_id} className="border-b border-border-subtle bg-bg-base last:border-0">
                    <td className="max-w-[250px] truncate px-4 py-3 text-sm text-text-primary">{opp.question}</td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                      {(opp.current_price * 100).toFixed(1)}¢
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                      {(opp.fair_value * 100).toFixed(1)}¢
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm font-medium text-profit">
                      +{(opp.profit_bps / 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => executeMutation.mutate({ marketId: opp.market_id, size: 100 })}
                        disabled={executeMutation.isPending}
                        className="rounded-md bg-accent-gold px-3 py-1.5 text-xs font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover disabled:opacity-60"
                      >
                        {executeMutation.isPending ? "…" : "Execute"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Active Positions */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">Active Positions</h2>
          <span className="font-mono text-xs text-text-muted">
            {posLoading ? "…" : `${positions?.length ?? 0} open`}
          </span>
        </div>

        {!positions || positions.length === 0 ? (
          <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-sm text-text-muted">
            No active convergence positions.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border-subtle">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-subtle bg-bg-card">
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">Market</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Entry</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Current</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Size</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos) => (
                  <tr key={pos.market_id} className="border-b border-border-subtle bg-bg-base last:border-0">
                    <td className="max-w-[250px] truncate px-4 py-3 text-sm text-text-primary">{pos.question}</td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">{pos.entry_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">{pos.current_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">{pos.size}</td>
                    <td className={`px-4 py-3 text-right font-mono text-sm font-medium ${pos.pnl >= 0 ? "text-profit" : "text-loss"}`}>
                      {pos.pnl >= 0 ? "+" : ""}${pos.pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
