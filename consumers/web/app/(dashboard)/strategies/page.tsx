"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthContext, useLocale } from "@/lib/providers";
import { useTrading } from "@/lib/hooks/useTrading";
import { formatBps, formatUSD } from "@/lib/utils";

export default function StrategiesPage() {
  const { api, token } = useAuthContext();
  const { t } = useLocale();
  const { canTrade } = useTrading();
  const queryClient = useQueryClient();

  const { data: opportunities, isLoading } = useQuery({
    queryKey: ["convergence-opportunities"],
    queryFn: () => api.getConvergenceOpportunities(),
    enabled: !!token,
  });

  const { data: positions } = useQuery({
    queryKey: ["convergence-positions"],
    queryFn: () => api.getConvergencePositions(),
    enabled: !!token,
  });

  const executeMutation = useMutation({
    mutationFn: ({ marketId, size }: { marketId: string; size: number }) =>
      api.executeConvergence(marketId, size),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["convergence-opportunities"] });
      queryClient.invalidateQueries({ queryKey: ["convergence-positions"] });
    },
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">{t("nav.strategies")}</h1>
        <p className="mt-1 text-sm text-zinc-400">{t("strategies.convergence")} — automated arbitrage</p>
      </div>

      {/* Opportunities */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">{t("strategies.opportunities")}</h2>
        {isLoading ? (
          <div className="py-8 text-center text-zinc-500">{t("common.loading")}</div>
        ) : !opportunities || opportunities.length === 0 ? (
          <div className="py-8 text-center text-zinc-500">{t("common.noData")}</div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500">
                  <th className="px-4 py-3">Market</th>
                  <th className="px-4 py-3 text-right">Current</th>
                  <th className="px-4 py-3 text-right">{t("strategies.fairValue")}</th>
                  <th className="px-4 py-3 text-right">{t("strategies.profitPotential")}</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {opportunities.map((opp) => (
                  <tr key={opp.market_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                    <td className="max-w-[250px] truncate px-4 py-3 text-white">
                      {opp.question}
                    </td>
                    <td className="px-4 py-3 text-right text-zinc-300">
                      {(opp.current_price * 100).toFixed(1)}¢
                    </td>
                    <td className="px-4 py-3 text-right text-zinc-300">
                      {(opp.fair_value * 100).toFixed(1)}¢
                    </td>
                    <td className="px-4 py-3 text-right text-green-400">
                      +{formatBps(opp.profit_bps)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => executeMutation.mutate({ marketId: opp.market_id, size: 100 })}
                        disabled={!canTrade || executeMutation.isPending}
                        className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        {t("strategies.execute")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Active Positions */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">{t("strategies.activePositions")}</h2>
        {!positions || positions.length === 0 ? (
          <div className="py-8 text-center text-zinc-500">{t("common.noData")}</div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-900">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500">
                  <th className="px-4 py-3">Market</th>
                  <th className="px-4 py-3 text-right">Entry</th>
                  <th className="px-4 py-3 text-right">Current</th>
                  <th className="px-4 py-3 text-right">Size</th>
                  <th className="px-4 py-3 text-right">{t("portfolio.pnl")}</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos) => (
                  <tr key={pos.market_id} className="border-b border-zinc-800/50">
                    <td className="max-w-[250px] truncate px-4 py-3 text-white">{pos.question}</td>
                    <td className="px-4 py-3 text-right text-zinc-300">{pos.entry_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-zinc-300">{pos.current_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-zinc-300">{pos.size}</td>
                    <td className="px-4 py-3 text-right">
                      <span className={pos.pnl >= 0 ? "text-green-400" : "text-red-400"}>
                        {pos.pnl >= 0 ? "+" : ""}{formatUSD(pos.pnl)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
