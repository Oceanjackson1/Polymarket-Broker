"use client";

import { useLocale } from "@/lib/providers";
import { formatUSD } from "@/lib/utils";
import type { PnL } from "@/lib/api-client";

export default function PnlChart({ pnl }: { pnl: PnL | undefined }) {
  const { t } = useLocale();

  if (!pnl) return null;

  const total = pnl.realized + pnl.unrealized;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <h3 className="mb-3 text-sm font-medium text-zinc-400">{t("portfolio.pnl")}</h3>
      <div className={`text-2xl font-bold ${total >= 0 ? "text-green-400" : "text-red-400"}`}>
        {total >= 0 ? "+" : ""}{formatUSD(total)}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-zinc-500">{t("portfolio.realized")}</span>
          <div className={`font-medium ${pnl.realized >= 0 ? "text-green-400" : "text-red-400"}`}>
            {formatUSD(pnl.realized)}
          </div>
        </div>
        <div>
          <span className="text-zinc-500">{t("portfolio.unrealized")}</span>
          <div className={`font-medium ${pnl.unrealized >= 0 ? "text-green-400" : "text-red-400"}`}>
            {formatUSD(pnl.unrealized)}
          </div>
        </div>
      </div>
      <div className="mt-2 text-xs text-zinc-500">
        Fees: Broker {formatUSD(pnl.fees_paid_broker)} / Polymarket {formatUSD(pnl.fees_paid_polymarket)}
      </div>
    </div>
  );
}
