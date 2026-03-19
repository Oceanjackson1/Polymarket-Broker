"use client";

import { useState } from "react";

interface OrderEntryProps {
  marketId: string;
  defaultPrice?: number;
}

const FEE_BPS = 20; // 20 bps platform fee

export default function OrderEntry({ defaultPrice = 0.75 }: OrderEntryProps) {
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [price, setPrice] = useState<string>(defaultPrice.toFixed(3));
  const [size, setSize] = useState<string>("");
  const [submitted, setSubmitted] = useState(false);

  const priceNum = parseFloat(price) || 0;
  const sizeNum = parseFloat(size) || 0;
  const total = priceNum * sizeNum;
  const fee = total * (FEE_BPS / 10000);

  const isBuy = side === "BUY";
  const isValid =
    priceNum > 0 &&
    priceNum < 1 &&
    sizeNum > 0 &&
    !isNaN(priceNum) &&
    !isNaN(sizeNum);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 2000);
  }

  return (
    <div className="flex h-full flex-col">
      {/* Panel header */}
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
            <span className="text-text-muted">Fee ({FEE_BPS} bps)</span>
            <span className="font-mono text-text-muted">
              ${fee.toFixed(4)}
            </span>
          </div>
          <div className="flex justify-between border-t border-border-subtle pt-1.5 text-xs">
            <span className="text-text-muted">Net Cost</span>
            <span className="font-mono text-text-primary">
              ${(total + fee).toFixed(2)}
            </span>
          </div>
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

        {/* Disclaimer */}
        <p className="text-center text-[10px] text-text-muted">
          Paper trading · No real funds
        </p>
      </form>
    </div>
  );
}
