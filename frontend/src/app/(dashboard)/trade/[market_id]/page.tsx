import type { Metadata } from "next";
import PriceChart from "@/components/charts/price-chart";
import OrderBook from "@/components/trading/orderbook";
import OrderEntry from "@/components/trading/order-entry";
import RecentTrades from "@/components/trading/recent-trades";
import MyOrders from "@/components/trading/my-orders";

// Mock market data — replace with a real API fetch keyed on market_id
const MOCK_MARKETS: Record<
  string,
  { title: string; midPrice: number; category: string }
> = {
  default: {
    title: "Will Donald Trump win the 2028 presidential election?",
    midPrice: 0.75,
    category: "Politics",
  },
  "btc-100k-2026": {
    title: "Will BTC exceed $100,000 before end of 2026?",
    midPrice: 0.61,
    category: "Crypto",
  },
  "gsw-lal-2026-03-19": {
    title: "GSW vs LAL — Golden State Warriors to win?",
    midPrice: 0.43,
    category: "NBA",
  },
};

function getMarket(id: string) {
  return MOCK_MARKETS[id] ?? MOCK_MARKETS["default"];
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ market_id: string }>;
}): Promise<Metadata> {
  const { market_id } = await params;
  const market = getMarket(market_id);
  return {
    title: market.title,
    description: `Trade on: ${market.title}. Mid price: ${market.midPrice.toFixed(3)}.`,
  };
}

export default async function TradePage({
  params,
}: {
  params: Promise<{ market_id: string }>;
}) {
  const { market_id } = await params;
  const market = getMarket(market_id);

  return (
    /*
     * Full-height terminal layout.
     * The dashboard layout already provides `flex-1 overflow-y-auto bg-bg-base`
     * for <main>. We override to get a true fixed-height terminal grid.
     */
    <div className="flex h-full flex-col overflow-hidden">
      {/* ── Top bar ── */}
      <header className="flex shrink-0 items-center justify-between border-b border-border-subtle bg-bg-card px-4 py-2">
        <div className="flex min-w-0 items-center gap-3">
          <span className="rounded bg-bg-elevated px-2 py-0.5 font-mono text-[10px] text-text-muted">
            {market.category}
          </span>
          <h1 className="truncate text-sm font-medium text-text-primary">
            {market.title}
          </h1>
        </div>
        <div className="flex shrink-0 items-center gap-4 pl-4">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-text-muted">MID</span>
            <span className="font-mono text-base font-semibold text-accent-gold">
              {market.midPrice.toFixed(3)}
            </span>
          </div>
          <div className="h-4 w-px bg-border-subtle" />
          <div className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-profit" />
            <span className="font-mono text-[10px] text-text-muted">LIVE</span>
          </div>
        </div>
      </header>

      {/* ── Main terminal grid ── */}
      {/*
       * Layout:
       *   Col 1 (flex-1): Chart top / [OrderBook + RecentTrades] bottom
       *   Col 2 (280px): Order Entry (spans both rows)
       */}
      <div className="flex min-h-0 flex-1 gap-px bg-border-subtle">
        {/* Left column */}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-px">
          {/* Row 1: Price Chart */}
          <div className="min-h-0 flex-1 overflow-hidden bg-bg-card">
            <PriceChart marketTitle={market.title} midPrice={market.midPrice} />
          </div>

          {/* Row 2: Order Book + Recent Trades */}
          <div className="flex h-52 shrink-0 gap-px">
            <div className="w-1/2 overflow-hidden bg-bg-card">
              <OrderBook />
            </div>
            <div className="w-1/2 overflow-hidden bg-bg-card">
              <RecentTrades />
            </div>
          </div>
        </div>

        {/* Right column: Order Entry */}
        <div className="w-72 shrink-0 overflow-y-auto bg-bg-card">
          <OrderEntry marketId={market_id} defaultPrice={market.midPrice} />
        </div>
      </div>

      {/* ── My Orders — full-width bottom panel ── */}
      <div className="h-48 shrink-0 border-t border-border-subtle bg-bg-card">
        <MyOrders marketId={market_id} />
      </div>
    </div>
  );
}
