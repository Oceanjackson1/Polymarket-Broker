"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { marketsApi } from "@/lib/api";
import PriceChart from "@/components/charts/price-chart";
import OrderBook from "@/components/trading/orderbook";
import OrderEntry from "@/components/trading/order-entry";
import RecentTrades from "@/components/trading/recent-trades";
import MyOrders from "@/components/trading/my-orders";

export default function TradePage({
  params,
}: {
  params: Promise<{ market_id: string }>;
}) {
  const { market_id } = use(params);

  const { data: market, isLoading } = useQuery({
    queryKey: ["market", market_id],
    queryFn: () => marketsApi.get(market_id),
    staleTime: 30_000,
  });

  const { data: orderbookData } = useQuery({
    queryKey: ["orderbook", market_id],
    queryFn: () => marketsApi.orderbook(market_id),
    refetchInterval: 3_000,
  });

  const { data: midpointData } = useQuery({
    queryKey: ["midpoint", market_id],
    queryFn: () => marketsApi.midpoint(market_id),
    refetchInterval: 3_000,
  });

  const title = String(market?.question ?? market?.["title"] ?? market_id);
  const category = String(market?.["category"] ?? market?.["tags"] ?? "");
  const midPrice = midpointData?.mid
    ? parseFloat(String(midpointData.mid))
    : 0.5;

  // Parse orderbook into component format
  const bids = ((orderbookData?.bids ?? []) as Array<{ price: string; size: string }>)
    .slice(0, 8)
    .map((b) => ({ price: parseFloat(b.price), size: parseFloat(b.size) }));
  const asks = ((orderbookData?.asks ?? []) as Array<{ price: string; size: string }>)
    .slice(0, 8)
    .map((a) => ({ price: parseFloat(a.price), size: parseFloat(a.size) }));

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <span className="text-sm text-text-muted">Loading market…</span>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Top bar */}
      <header className="flex shrink-0 items-center justify-between border-b border-border-subtle bg-bg-card px-4 py-2">
        <div className="flex min-w-0 items-center gap-3">
          {category && (
            <span className="rounded bg-bg-elevated px-2 py-0.5 font-mono text-[10px] text-text-muted">
              {category}
            </span>
          )}
          <h1 className="truncate text-sm font-medium text-text-primary">
            {title}
          </h1>
        </div>
        <div className="flex shrink-0 items-center gap-4 pl-4">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-text-muted">MID</span>
            <span className="font-mono text-base font-semibold text-accent-gold">
              {midPrice.toFixed(3)}
            </span>
          </div>
          <div className="h-4 w-px bg-border-subtle" />
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-profit" />
            <span className="font-mono text-[10px] text-text-muted">LIVE</span>
          </div>
        </div>
      </header>

      {/* Main terminal grid */}
      <div className="flex min-h-0 flex-1 gap-px bg-border-subtle">
        {/* Left column */}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-px">
          {/* Price Chart */}
          <div className="min-h-0 flex-1 overflow-hidden bg-bg-card">
            <PriceChart marketTitle={title} midPrice={midPrice} />
          </div>

          {/* Order Book + Recent Trades */}
          <div className="flex h-52 shrink-0 gap-px">
            <div className="w-1/2 overflow-hidden bg-bg-card">
              <OrderBook bids={bids.length > 0 ? bids : undefined} asks={asks.length > 0 ? asks : undefined} />
            </div>
            <div className="w-1/2 overflow-hidden bg-bg-card">
              <RecentTrades />
            </div>
          </div>
        </div>

        {/* Right column: Order Entry */}
        <div className="w-72 shrink-0 overflow-y-auto bg-bg-card">
          <OrderEntry marketId={market_id} defaultPrice={midPrice} />
        </div>
      </div>

      {/* My Orders */}
      <div className="h-48 shrink-0 border-t border-border-subtle bg-bg-card">
        <MyOrders marketId={market_id} />
      </div>
    </div>
  );
}
