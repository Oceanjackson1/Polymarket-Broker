"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthContext, useLocale } from "@/lib/providers";
import { useWebSocket } from "@/lib/hooks/useWebSocket";
import BalanceCard from "@/components/portfolio/BalanceCard";
import PositionTable from "@/components/portfolio/PositionTable";
import PnlChart from "@/components/portfolio/PnlChart";

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";

export default function PortfolioPage() {
  const { api, token } = useAuthContext();
  const { t } = useLocale();

  const { data: positions } = useQuery({
    queryKey: ["positions"],
    queryFn: () => api.getPositions(),
    enabled: !!token,
  });

  const { data: balance } = useQuery({
    queryKey: ["balance"],
    queryFn: () => api.getBalance(),
    enabled: !!token,
  });

  const { data: pnl } = useQuery({
    queryKey: ["pnl"],
    queryFn: () => api.getPnl(),
    enabled: !!token,
  });

  // Real-time portfolio updates
  useWebSocket(`${WS_BASE}/ws/portfolio/live`, { enabled: !!token });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("nav.portfolio")}</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <BalanceCard balance={balance} />
        <PnlChart pnl={pnl} />
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">{t("portfolio.positions")}</h2>
        <PositionTable positions={positions ?? []} />
      </div>
    </div>
  );
}
