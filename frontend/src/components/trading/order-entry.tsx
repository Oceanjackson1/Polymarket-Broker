"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { feesApi } from "@/lib/api";

interface OrderEntryProps {
  marketId: string;
  defaultPrice?: number;
  category?: string;
}

export default function OrderEntry({ defaultPrice = 0.75, category = "other" }: OrderEntryProps) {
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [price, setPrice] = useState<string>(defaultPrice.toFixed(3));
  const [size, setSize] = useState<string>("");
  const [submitted, setSubmitted] = useState(false);

  const priceNum = parseFloat(price) || 0;
  const sizeNum = parseFloat(size) || 0;
  const total = priceNum * sizeNum;

  const validPrice = priceNum > 0 && priceNum < 1;

  const { data: feeEstimate } = useQuery({
    queryKey: ["fee-estimate", category, price, total],
    queryFn: () =>
      feesApi.estimate({
        category,
        price: priceNum,
        volume: total > 0 ? total : 100,
      }),
    enabled: validPrice,
    staleTime: 60_000,
  });

  const feeDisplay = useMemo(() => {
    if (!feeEstimate) return { polyBps: 0, brokerBps: 0, totalBps: 0, feeAmount: 0 };
    return {
      polyBps: feeEstimate.polymarket_fee_bps,
      brokerBps: feeEstimate.broker_fee_bps,
      totalBps: feeEstimate.total_fee_bps,
      feeAmount: total > 0 ? total * (feeEstimate.total_fee_bps / 10_000) : 0,
    };
  }, [feeEstimate, total]);

  const isValid = validPrice && sizeNum > 0 && !isNaN(priceNum) && !isNaN(sizeNum);
  const isBuy = side === "BUY";

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 2000);
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border-subtle px-4 py-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          Order Entry
        </span>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4 p-4">
        {/* BUY / SELL toggle */}
        <div className="grid grid-cols-2 gap-1 rounded-md border border-border-default bg-bg-base p-1">
          <button
            type="button"
            onClick={() => setSide("BUY")}
            className={`rounded py-1.5 text-xs font-semibold transition-all duration-200 ${
              isBuy
                ? "bg-profit-bg text-profit"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            BUY
          </button>
          <button
            type="button"
            onClick={() => setSide("SELL")}
            className={`rounded py-1.5 text-xs font-semibold transition-all duration-200 ${
              !isBuy
                ? "bg-loss-bg text-loss"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            SELL
          </button>
        </div>

        {/* Price input */}
        <div>
          <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Price (0–1)
          </label>
          <input
            type="number"
            step="0.001"
            min="0.001"
            max="0.999"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="w-full rounded border border-border-default bg-bg-base px-3 py-2 font-mono text-sm text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent-gold"
            placeholder="0.000"
          />
        </div>

        {/* Size input */}
        <div>
          <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Size (shares)
          </label>
          <input
            type="number"
            step="1"
            min="1"
            value={size}
            onChange={(e) => setSize(e.target.value)}
            className="w-full rounded border border-border-default bg-bg-base px-3 py-2 font-mono text-sm text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent-gold"
            placeholder="0"
          />
        </div>

        {/* Order summary */}
        <div className="rounded border border-border-subtle bg-bg-base p-3 space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="text-text-muted">Total</span>
            <span className="font-mono text-text-primary">
              ${total.toFixed(2)}
            </span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-text-muted">
              Poly Fee ({feeDisplay.polyBps} bps)
            </span>
            <span className="font-mono text-text-muted">
              ${(total * (feeDisplay.polyBps / 10_000)).toFixed(4)}
            </span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-text-muted">
              Broker Fee ({feeDisplay.brokerBps} bps)
            </span>
            <span className="font-mono text-text-muted">
              ${(total * (feeDisplay.brokerBps / 10_000)).toFixed(4)}
            </span>
          </div>
          <div className="flex justify-between border-t border-border-subtle pt-1.5 text-xs">
            <span className="text-text-muted">Net Cost</span>
            <span className="font-mono text-text-primary">
              ${(total + feeDisplay.feeAmount).toFixed(2)}
            </span>
          </div>
          {feeEstimate && total > 0 && (
            <div className="flex justify-between text-xs">
              <span className="text-text-muted">Profit if Win</span>
              <span className={`font-mono ${feeEstimate.net_profit_if_win >= 0 ? "text-profit" : "text-loss"}`}>
                ${feeEstimate.net_profit_if_win.toFixed(2)}
              </span>
            </div>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!isValid}
          className={`btn-premium w-full rounded py-2.5 text-sm font-semibold transition-colors ${
            submitted
              ? "bg-profit text-white"
              : isValid
                ? "bg-accent-gold text-bg-base hover:bg-accent-gold-hover"
                : "cursor-not-allowed bg-bg-elevated text-text-muted"
          }`}
        >
          {submitted
            ? "Order Placed"
            : `Place ${side} Order`}
        </button>

        <p className="text-center text-[10px] text-text-muted">
          Paper trading · No real funds
        </p>
      </form>
    </div>
  );
}
