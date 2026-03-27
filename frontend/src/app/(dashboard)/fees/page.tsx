"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { feesApi } from "@/lib/api";
import type { FeeEstimateResponse } from "@/lib/api";

export default function FeesPage() {
  const [category, setCategory] = useState("crypto");
  const [price, setPrice] = useState("0.95");
  const [volume, setVolume] = useState("100");

  const priceNum = parseFloat(price) || 0;
  const volumeNum = parseFloat(volume) || 0;
  const validCalc = priceNum > 0 && priceNum < 1 && volumeNum > 0;

  const { data: schedule, isLoading } = useQuery({
    queryKey: ["fee-schedule"],
    queryFn: () => feesApi.schedule(),
    staleTime: 300_000,
  });

  const { data: estimate } = useQuery({
    queryKey: ["fee-calc", category, price, volume],
    queryFn: () =>
      feesApi.estimate({ category, price: priceNum, volume: volumeNum }),
    enabled: validCalc,
    staleTime: 10_000,
  });

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">Fee Schedule</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Polymarket platform fees by market category.{" "}
          <span className="font-mono text-text-muted">
            {schedule?.formula ?? ""}
          </span>
        </p>
      </div>

      {/* Fee Schedule Table */}
      {isLoading ? (
        <div className="space-y-px rounded-lg border border-border-subtle bg-bg-card">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-12 animate-pulse bg-bg-elevated" />
          ))}
        </div>
      ) : schedule ? (
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle bg-bg-card">
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">Category</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">feeRate</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Exponent</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Maker Rebate</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">@ p=0.50</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">@ p=0.80</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">@ p=0.95</th>
              </tr>
            </thead>
            <tbody>
              {schedule.categories.map((cat) => (
                <tr key={cat.category} className="border-b border-border-subtle bg-bg-base last:border-0">
                  <td className="px-4 py-2.5 text-sm font-medium capitalize text-text-primary">
                    {cat.category}
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-sm text-text-secondary">
                    {cat.fee_rate}
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-sm text-text-secondary">
                    {cat.exponent}
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-sm text-text-secondary">
                    {(cat.maker_rebate * 100).toFixed(0)}%
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-sm text-text-secondary">
                    <FeeCell rate={cat.fee_at_p50} />
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-sm text-text-secondary">
                    <FeeCell rate={cat.fee_at_p80} />
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-sm text-text-secondary">
                    <FeeCell rate={cat.fee_at_p95} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {/* Interactive Calculator */}
      <div className="rounded-lg border border-border-subtle bg-bg-card p-6">
        <h2 className="mb-4 text-sm font-semibold text-text-primary">Fee Calculator</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded border border-border-default bg-bg-base px-3 py-2 text-sm text-text-primary outline-none focus:border-accent-gold"
            >
              {(schedule?.categories ?? []).map((c) => (
                <option key={c.category} value={c.category}>
                  {c.category}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Price (0–1)
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="0.99"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full rounded border border-border-default bg-bg-base px-3 py-2 font-mono text-sm text-text-primary outline-none focus:border-accent-gold"
            />
          </div>
          <div>
            <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Volume (USDC)
            </label>
            <input
              type="number"
              step="10"
              min="1"
              value={volume}
              onChange={(e) => setVolume(e.target.value)}
              className="w-full rounded border border-border-default bg-bg-base px-3 py-2 font-mono text-sm text-text-primary outline-none focus:border-accent-gold"
            />
          </div>
        </div>

        {estimate && (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-4">
            <CalcCard label="Poly Fee Rate" value={`${estimate.polymarket_fee_bps} bps`} sub={`${(estimate.polymarket_fee_rate * 100).toFixed(3)}%`} />
            <CalcCard label="Poly Fee" value={`$${estimate.polymarket_fee_amount.toFixed(4)}`} />
            <CalcCard label="Total Fee" value={`$${estimate.total_fee_amount.toFixed(4)}`} sub={`${estimate.total_fee_bps} bps`} />
            <CalcCard
              label="Net Profit if Win"
              value={`$${estimate.net_profit_if_win.toFixed(2)}`}
              highlight={estimate.net_profit_if_win >= 0 ? "profit" : "loss"}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function FeeCell({ rate }: { rate: number }) {
  const bps = Math.round(rate * 10_000);
  const color =
    rate === 0
      ? "text-profit"
      : bps >= 100
        ? "text-loss"
        : bps >= 50
          ? "text-accent-gold"
          : "text-text-secondary";
  return <span className={color}>{(rate * 100).toFixed(2)}%</span>;
}

function CalcCard({
  label,
  value,
  sub,
  highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: "profit" | "loss";
}) {
  return (
    <div className="rounded border border-border-subtle bg-bg-base p-3">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
        {label}
      </div>
      <div
        className={`mt-1 font-mono text-lg font-semibold ${
          highlight === "profit"
            ? "text-profit"
            : highlight === "loss"
              ? "text-loss"
              : "text-text-primary"
        }`}
      >
        {value}
      </div>
      {sub && <div className="mt-0.5 font-mono text-xs text-text-muted">{sub}</div>}
    </div>
  );
}
