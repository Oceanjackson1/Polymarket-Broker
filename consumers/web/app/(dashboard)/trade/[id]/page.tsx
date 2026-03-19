"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthContext, useLocale } from "@/lib/providers";
import OrderBook from "@/components/market/OrderBook";
import OrderForm from "@/components/market/OrderForm";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { use } from "react";

export default function TradePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { api } = useAuthContext();
  const { t } = useLocale();
  const [selectedPrice, setSelectedPrice] = useState("");

  const { data: market, isLoading } = useQuery({
    queryKey: ["market", id],
    queryFn: () => api.getMarket(id),
  });

  const { data: trades } = useQuery({
    queryKey: ["trades", id],
    queryFn: () => api.getTrades(id),
  });

  // Use first clobTokenId as token_id for orderbook WS
  const tokenId = id;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-zinc-500">
        {t("common.loading")}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Link
          href="/markets"
          className="mt-1 rounded-md p-1 text-zinc-400 hover:bg-zinc-800 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-lg font-bold">{market?.question || id}</h1>
          <div className="mt-1 flex gap-4 text-xs text-zinc-500">
            {market?.volume24hr && (
              <span>{t("common.volume")}: ${(market.volume24hr / 1000).toFixed(0)}K</span>
            )}
            {market?.endDate && <span>Ends: {new Date(market.endDate).toLocaleDateString()}</span>}
          </div>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Left: OrderBook + Trades */}
        <div className="space-y-4 lg:col-span-2">
          <OrderBook tokenId={tokenId} onPriceClick={setSelectedPrice} />

          {/* Recent trades */}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <h3 className="mb-3 text-sm font-medium text-white">
              {t("trade.recentTrades")}
            </h3>
            <div className="max-h-48 space-y-1 overflow-y-auto">
              {trades && trades.length > 0 ? (
                trades.slice(0, 20).map((trade, i) => (
                  <div key={i} className="grid grid-cols-3 text-xs">
                    <span
                      className={
                        trade.side === "BUY" ? "text-green-400" : "text-red-400"
                      }
                    >
                      {Number(trade.price).toFixed(2)}
                    </span>
                    <span className="text-zinc-400">
                      {Number(trade.size).toFixed(0)}
                    </span>
                    <span className="text-right text-zinc-500">
                      {trade.timestamp}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-zinc-500">{t("common.noData")}</p>
              )}
            </div>
          </div>
        </div>

        {/* Right: OrderForm */}
        <div>
          <OrderForm marketId={id} defaultPrice={selectedPrice} />
        </div>
      </div>
    </div>
  );
}
