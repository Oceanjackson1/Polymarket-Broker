"use client";

import { formatBps } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

type Props = {
  direction: string;
  bps: number;
};

export default function BiasSignalBadge({ direction, bps }: Props) {
  if (direction === "FORECAST_HIGHER" || direction === "HOME_UNDERPRICED") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-900/40 px-2 py-0.5 text-xs font-medium text-green-400">
        <TrendingUp className="h-3 w-3" />
        {formatBps(bps)}
      </span>
    );
  }

  if (direction === "MARKET_HIGHER" || direction === "AWAY_UNDERPRICED") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-900/40 px-2 py-0.5 text-xs font-medium text-red-400">
        <TrendingDown className="h-3 w-3" />
        {formatBps(bps)}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-zinc-800 px-2 py-0.5 text-xs font-medium text-zinc-400">
      <Minus className="h-3 w-3" />
      {formatBps(bps)}
    </span>
  );
}
