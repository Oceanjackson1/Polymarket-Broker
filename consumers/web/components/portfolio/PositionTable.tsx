"use client";

import { useLocale } from "@/lib/providers";
import { formatUSD } from "@/lib/utils";
import type { Position } from "@/lib/api-client";

export default function PositionTable({ positions }: { positions: Position[] }) {
  const { t } = useLocale();

  if (positions.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-8 text-center text-sm text-zinc-500">
        {t("common.noData")}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-900">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500">
            <th className="px-4 py-3">Market</th>
            <th className="px-4 py-3">Side</th>
            <th className="px-4 py-3 text-right">Size</th>
            <th className="px-4 py-3 text-right">Entry</th>
            <th className="px-4 py-3 text-right">Current</th>
            <th className="px-4 py-3 text-right">{t("portfolio.pnl")}</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((pos, i) => (
            <tr key={i} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
              <td className="max-w-[200px] truncate px-4 py-3 text-white">
                {pos.market_question || pos.market_id}
              </td>
              <td className="px-4 py-3">
                <span className={pos.side === "BUY" ? "text-green-400" : "text-red-400"}>
                  {pos.side}
                </span>
              </td>
              <td className="px-4 py-3 text-right text-zinc-300">{pos.size}</td>
              <td className="px-4 py-3 text-right text-zinc-300">
                {pos.entry_price.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-right text-zinc-300">
                {pos.current_price?.toFixed(2) ?? "—"}
              </td>
              <td className="px-4 py-3 text-right">
                {pos.unrealized_pnl != null ? (
                  <span className={pos.unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"}>
                    {pos.unrealized_pnl >= 0 ? "+" : ""}
                    {formatUSD(pos.unrealized_pnl)}
                  </span>
                ) : (
                  "—"
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
