"use client";

import { useState, useCallback } from "react";
import { useTrading } from "@/lib/hooks/useTrading";
import { useLocale } from "@/lib/providers";

type Props = {
  marketId: string;
  defaultPrice?: string;
};

export default function OrderForm({ marketId, defaultPrice }: Props) {
  const { t } = useLocale();
  const { buildAndSubmitOrder, loading, error, canTrade } = useTrading();
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [price, setPrice] = useState(defaultPrice || "");
  const [size, setSize] = useState("");
  const [orderType, setOrderType] = useState<"LIMIT" | "MARKET">("LIMIT");
  const [success, setSuccess] = useState(false);

  // Update price when OrderBook sends a click
  const updatePrice = useCallback((p: string) => setPrice(p), []);

  const total = price && size ? (Number(price) * Number(size)).toFixed(2) : "0.00";
  const fee = price && size ? (Number(price) * Number(size) * 0.001).toFixed(4) : "0.0000";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(false);
    try {
      await buildAndSubmitOrder({
        market_id: marketId,
        side,
        price: Number(price),
        size: Number(size),
      });
      setSuccess(true);
      setSize("");
    } catch {
      // error is set in useTrading
    }
  };

  // Expose updatePrice to parent via ref pattern (or just use as prop)
  // Parent can call OrderForm's defaultPrice prop
  if (defaultPrice && defaultPrice !== price && !size) {
    setPrice(defaultPrice);
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <h3 className="mb-3 text-sm font-medium text-white">Order</h3>

      {/* Side toggle */}
      <div className="mb-4 grid grid-cols-2 gap-1 rounded-md bg-zinc-800 p-1">
        <button
          type="button"
          onClick={() => setSide("BUY")}
          className={`rounded-md py-1.5 text-sm font-medium ${
            side === "BUY" ? "bg-green-600 text-white" : "text-zinc-400"
          }`}
        >
          {t("trade.buy")}
        </button>
        <button
          type="button"
          onClick={() => setSide("SELL")}
          className={`rounded-md py-1.5 text-sm font-medium ${
            side === "SELL" ? "bg-red-600 text-white" : "text-zinc-400"
          }`}
        >
          {t("trade.sell")}
        </button>
      </div>

      {/* Order type */}
      <div className="mb-3">
        <select
          value={orderType}
          onChange={(e) => setOrderType(e.target.value as "LIMIT" | "MARKET")}
          className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white"
        >
          <option value="LIMIT">{t("trade.limit")}</option>
          <option value="MARKET">{t("trade.market")}</option>
        </select>
      </div>

      {/* Price */}
      {orderType === "LIMIT" && (
        <div className="mb-3">
          <label className="mb-1 block text-xs text-zinc-500">{t("trade.price")}</label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            max="0.99"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white"
            placeholder="0.50"
            required
          />
        </div>
      )}

      {/* Size */}
      <div className="mb-4">
        <label className="mb-1 block text-xs text-zinc-500">{t("trade.size")}</label>
        <input
          type="number"
          step="1"
          min="1"
          value={size}
          onChange={(e) => setSize(e.target.value)}
          className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white"
          placeholder="100"
          required
        />
      </div>

      {/* Summary */}
      <div className="mb-4 space-y-1 text-xs text-zinc-400">
        <div className="flex justify-between">
          <span>{t("trade.estimatedFee")}</span>
          <span>${fee}</span>
        </div>
        <div className="flex justify-between font-medium text-white">
          <span>{t("trade.total")}</span>
          <span>${total}</span>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-3 rounded-md bg-red-900/50 px-3 py-2 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Success */}
      {success && (
        <div className="mb-3 rounded-md bg-green-900/50 px-3 py-2 text-xs text-green-300">
          Order placed successfully!
        </div>
      )}

      {/* Submit */}
      {canTrade ? (
        <button
          type="submit"
          disabled={loading}
          className={`w-full rounded-md px-4 py-2.5 text-sm font-medium text-white ${
            side === "BUY"
              ? "bg-green-600 hover:bg-green-700"
              : "bg-red-600 hover:bg-red-700"
          } disabled:opacity-50`}
        >
          {loading ? t("common.loading") : t("trade.placeOrder")}
        </button>
      ) : (
        <button
          type="button"
          className="w-full rounded-md bg-zinc-700 px-4 py-2.5 text-sm font-medium text-zinc-300"
          disabled
        >
          {t("trade.connectToTrade")}
        </button>
      )}
    </form>
  );
}
