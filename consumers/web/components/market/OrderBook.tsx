"use client";

import { useWebSocket } from "@/lib/hooks/useWebSocket";
import { useLocale } from "@/lib/providers";

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";

type OrderbookUpdate = {
  type: string;
  token_id: string;
  bids: Array<{ price: string; size: string }>;
  asks: Array<{ price: string; size: string }>;
  midpoint: string | null;
};

type Props = {
  tokenId: string;
  onPriceClick?: (price: string) => void;
};

export default function OrderBook({ tokenId, onPriceClick }: Props) {
  const { t } = useLocale();
  const { data, status } = useWebSocket<OrderbookUpdate>(
    `${WS_BASE}/ws/markets/${tokenId}`,
    { enabled: !!tokenId }
  );

  const bids = data?.bids?.slice(0, 8) ?? [];
  const asks = data?.asks?.slice(0, 8) ?? [];
  const mid = data?.midpoint;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-white">{t("trade.orderbook")}</h3>
        <span className={`h-2 w-2 rounded-full ${status === "connected" ? "bg-green-500" : "bg-zinc-600"}`} />
      </div>

      {/* Header */}
      <div className="mb-1 grid grid-cols-4 text-xs text-zinc-500">
        <span>{t("trade.price")}</span>
        <span className="text-right">{t("trade.size")}</span>
        <span className="text-right">{t("trade.price")}</span>
        <span className="text-right">{t("trade.size")}</span>
      </div>

      <div className="mb-1 grid grid-cols-2 text-xs text-zinc-500">
        <span className="text-green-500">{t("trade.bids")}</span>
        <span className="text-right text-red-500">{t("trade.asks")}</span>
      </div>

      {/* Rows */}
      <div className="space-y-0.5">
        {Array.from({ length: Math.max(bids.length, asks.length, 1) }).map((_, i) => {
          const bid = bids[i];
          const ask = asks[i];
          return (
            <div key={i} className="grid grid-cols-4 text-xs">
              {bid ? (
                <>
                  <span
                    className="cursor-pointer text-green-400 hover:underline"
                    onClick={() => onPriceClick?.(bid.price)}
                  >
                    {Number(bid.price).toFixed(2)}
                  </span>
                  <span className="text-right text-zinc-400">{Number(bid.size).toFixed(0)}</span>
                </>
              ) : (
                <>
                  <span />
                  <span />
                </>
              )}
              {ask ? (
                <>
                  <span
                    className="cursor-pointer text-right text-red-400 hover:underline"
                    onClick={() => onPriceClick?.(ask.price)}
                  >
                    {Number(ask.price).toFixed(2)}
                  </span>
                  <span className="text-right text-zinc-400">{Number(ask.size).toFixed(0)}</span>
                </>
              ) : (
                <>
                  <span />
                  <span />
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Midpoint */}
      {mid && (
        <div className="mt-2 border-t border-zinc-700 pt-2 text-center text-xs">
          <span className="text-zinc-500">{t("trade.midpoint")}:</span>{" "}
          <span className="font-medium text-white">{Number(mid).toFixed(4)}</span>
        </div>
      )}
    </div>
  );
}
