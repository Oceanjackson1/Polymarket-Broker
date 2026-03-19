"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthContext, useLocale } from "@/lib/providers";
import { useWebSocket } from "@/lib/hooks/useWebSocket";

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";

type BtcWsUpdate = {
  type: string;
  data: Array<{
    timeframe: string;
    price_usd: string;
    prediction_prob: string | null;
    volume: string | null;
    recorded_at: string | null;
  }>;
};

export default function BtcDataPage() {
  const { api, token } = useAuthContext();
  const { t } = useLocale();

  const { data: wsData } = useWebSocket<BtcWsUpdate>(`${WS_BASE}/ws/btc/live`, {
    enabled: !!token,
  });

  const { data: restData } = useQuery({
    queryKey: ["btc-predictions"],
    queryFn: () => api.getBtcPredictions(),
    enabled: !!token,
  });

  // Prefer WebSocket data, fallback to REST
  const predictions = wsData?.data ?? restData ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("nav.btc")} Predictions</h1>
        <p className="mt-1 text-sm text-zinc-400">Multi-timeframe BTC price predictions</p>
      </div>

      {predictions.length === 0 ? (
        <div className="py-12 text-center text-zinc-500">{t("common.noData")}</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {predictions.map((pred) => (
            <div
              key={pred.timeframe}
              className="rounded-lg border border-zinc-800 bg-zinc-900 p-4"
            >
              <div className="mb-2 flex items-center justify-between">
                <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs font-medium text-zinc-300">
                  {pred.timeframe}
                </span>
                <span className="h-2 w-2 rounded-full bg-green-500" title="Live" />
              </div>

              <div className="text-xl font-bold text-white">
                ${Number(pred.price_usd).toLocaleString()}
              </div>

              {pred.prediction_prob && (
                <div className="mt-2">
                  <div className="mb-1 flex justify-between text-xs">
                    <span className="text-zinc-500">UP probability</span>
                    <span className="text-green-400">
                      {(Number(pred.prediction_prob) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
                    <div
                      className="h-full rounded-full bg-green-500"
                      style={{ width: `${Number(pred.prediction_prob) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {pred.volume && (
                <div className="mt-2 text-xs text-zinc-500">
                  {t("common.volume")}: ${Number(pred.volume).toLocaleString()}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
