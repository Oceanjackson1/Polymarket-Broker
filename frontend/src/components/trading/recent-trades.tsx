"use client";

interface Trade {
  price: number;
  size: number;
  time: string;
  side: "BUY" | "SELL";
}

const MOCK_TRADES: Trade[] = [
  { price: 0.751, size: 100, time: "10:04:32", side: "BUY" },
  { price: 0.748, size: 250, time: "10:03:58", side: "SELL" },
  { price: 0.75, size: 50, time: "10:03:41", side: "BUY" },
  { price: 0.749, size: 400, time: "10:02:17", side: "BUY" },
  { price: 0.746, size: 75, time: "10:01:55", side: "SELL" },
  { price: 0.748, size: 180, time: "10:01:22", side: "BUY" },
  { price: 0.745, size: 320, time: "10:00:48", side: "SELL" },
  { price: 0.747, size: 60, time: "09:59:33", side: "BUY" },
];

interface RecentTradesProps {
  trades?: Trade[];
}

export default function RecentTrades({
  trades = MOCK_TRADES,
}: RecentTradesProps) {
  return (
    <div className="flex h-full flex-col">
      {/* Panel header */}
      <div className="border-b border-border-subtle px-4 py-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Recent Trades
        </span>
      </div>

      {/* Column headers */}
      <div className="grid grid-cols-3 px-3 py-1 text-[10px] text-text-muted">
        <span>Price</span>
        <span className="text-right">Size</span>
        <span className="text-right">Time</span>
      </div>

      {/* Trade rows */}
      <div className="flex-1 overflow-y-auto">
        {trades.map((trade, idx) => (
          <div
            key={idx}
            className="grid grid-cols-3 px-3 py-[3px] text-xs hover:bg-bg-elevated"
          >
            <span
              className={`font-mono ${trade.side === "BUY" ? "text-profit" : "text-loss"}`}
            >
              {trade.price.toFixed(3)}
            </span>
            <span className="text-right font-mono text-text-secondary">
              {trade.size.toLocaleString()}
            </span>
            <span className="text-right font-mono text-text-muted">
              {trade.time}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
