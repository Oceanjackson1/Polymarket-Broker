"use client";

import Link from "next/link";
import type { Market } from "@/lib/api-client";
import { useLocale } from "@/lib/providers";

export default function MarketCard({ market }: { market: Market }) {
  const { t } = useLocale();

  // Handle both Gamma ("question") and Dome ("title") field names
  const displayTitle = market.question || market.title || market.market_slug || "Untitled";
  const marketId = market.id || market.market_slug || "";

  const price = market.lastTradePrice
    ? (market.lastTradePrice * 100).toFixed(0)
    : "—";
  const change = market.oneDayPriceChange;
  const changeStr = change
    ? `${change > 0 ? "+" : ""}${(change * 100).toFixed(1)}%`
    : null;

  // Handle different volume field names
  const vol = market.volume24hr || market.volume_total || market.volume;
  const volume = vol ? `$${(vol / 1000).toFixed(0)}K` : null;

  return (
    <Link
      href={`/trade/${marketId}`}
      className="block rounded-lg border border-zinc-800 bg-zinc-900 p-4 transition-colors hover:border-zinc-600 hover:bg-zinc-800/50"
    >
      <h3 className="mb-2 line-clamp-2 text-sm font-medium text-white">
        {displayTitle}
      </h3>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-green-400">{price}¢</span>
          {changeStr && (
            <span
              className={`text-xs ${
                change && change > 0 ? "text-green-400" : "text-red-400"
              }`}
            >
              {changeStr}
            </span>
          )}
        </div>
        {volume && (
          <span className="text-xs text-zinc-500">
            {t("common.volume")}: {volume}
          </span>
        )}
      </div>
    </Link>
  );
}
