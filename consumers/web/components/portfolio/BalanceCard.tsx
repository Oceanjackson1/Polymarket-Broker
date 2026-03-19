"use client";

import { useLocale } from "@/lib/providers";
import { formatUSD } from "@/lib/utils";
import type { Balance } from "@/lib/api-client";

export default function BalanceCard({ balance }: { balance: Balance | undefined }) {
  const { t } = useLocale();

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <h3 className="mb-3 text-sm font-medium text-zinc-400">{t("portfolio.balance")}</h3>
      <div className="text-2xl font-bold text-white">
        {balance ? formatUSD(balance.balance) : "—"}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-zinc-500">{t("portfolio.available")}</span>
          <div className="font-medium text-green-400">
            {balance ? formatUSD(balance.available) : "—"}
          </div>
        </div>
        <div>
          <span className="text-zinc-500">{t("portfolio.locked")}</span>
          <div className="font-medium text-yellow-400">
            {balance ? formatUSD(balance.locked) : "—"}
          </div>
        </div>
      </div>
    </div>
  );
}
