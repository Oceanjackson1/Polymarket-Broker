"use client";

interface OrderBookLevel {
  price: number;
  size: number;
}

interface OrderBookProps {
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
}

const DEFAULT_BIDS: OrderBookLevel[] = [
  { price: 0.745, size: 500 },
  { price: 0.74, size: 800 },
  { price: 0.735, size: 1200 },
  { price: 0.73, size: 650 },
  { price: 0.725, size: 900 },
  { price: 0.72, size: 400 },
];

const DEFAULT_ASKS: OrderBookLevel[] = [
  { price: 0.755, size: 300 },
  { price: 0.76, size: 200 },
  { price: 0.765, size: 150 },
  { price: 0.77, size: 500 },
  { price: 0.775, size: 280 },
  { price: 0.78, size: 120 },
];

function DepthRow({
  price,
  size,
  maxSize,
  side,
}: {
  price: number;
  size: number;
  maxSize: number;
  side: "bid" | "ask";
}) {
  const pct = Math.round((size / maxSize) * 100);
  const isBid = side === "bid";

  return (
    <div className="relative flex items-center px-3 py-[3px] text-xs">
      {/* Depth bar */}
      <div
        className={`absolute inset-y-0 ${isBid ? "left-0" : "right-0"} opacity-20 ${isBid ? "bg-profit" : "bg-loss"}`}
        style={{ width: `${pct}%` }}
      />
      {/* Content */}
      <span
        className={`relative z-10 w-1/2 font-mono ${isBid ? "text-profit" : "text-loss"}`}
      >
        {price.toFixed(3)}
      </span>
      <span className="relative z-10 w-1/2 text-right font-mono text-text-secondary">
        {size.toLocaleString()}
      </span>
    </div>
  );
}

export default function OrderBook({
  bids = DEFAULT_BIDS,
  asks = DEFAULT_ASKS,
}: Partial<OrderBookProps>) {
  const spread =
    asks.length > 0 && bids.length > 0
      ? (asks[0].price - bids[0].price).toFixed(3)
      : "—";

  const maxBidSize = Math.max(...bids.map((b) => b.size));
  const maxAskSize = Math.max(...asks.map((a) => a.size));

  return (
    <div className="flex h-full flex-col">
      {/* Panel header */}
      <div className="border-b border-border-subtle px-4 py-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Order Book
        </span>
      </div>

      {/* Column headers */}
      <div className="flex px-3 py-1 text-[10px] text-text-muted">
        <span className="w-1/2">Price</span>
        <span className="w-1/2 text-right">Size</span>
      </div>

      {/* Asks (reversed so best ask is at bottom, closest to spread) */}
      <div className="flex flex-col-reverse overflow-hidden">
        {asks.slice(0, 6).map((ask) => (
          <DepthRow
            key={ask.price}
            price={ask.price}
            size={ask.size}
            maxSize={maxAskSize}
            side="ask"
          />
        ))}
      </div>

      {/* Spread */}
      <div className="flex items-center justify-center border-y border-border-subtle py-1">
        <span className="font-mono text-[10px] text-text-muted">
          spread: {spread}
        </span>
      </div>

      {/* Bids */}
      <div className="flex flex-col overflow-hidden">
        {bids.slice(0, 6).map((bid) => (
          <DepthRow
            key={bid.price}
            price={bid.price}
            size={bid.size}
            maxSize={maxBidSize}
            side="bid"
          />
        ))}
      </div>
    </div>
  );
}
