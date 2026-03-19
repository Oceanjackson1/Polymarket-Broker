"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthContext, useLocale } from "@/lib/providers";
import { formatUSD } from "@/lib/utils";

const STATUSES = ["ALL", "OPEN", "PARTIALLY_FILLED", "FILLED", "CANCELLED"];

export default function OrdersPage() {
  const { api, token } = useAuthContext();
  const { t } = useLocale();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("ALL");

  const { data: ordersResp, isLoading } = useQuery({
    queryKey: ["orders", statusFilter],
    queryFn: () =>
      api.getOrders({
        status: statusFilter === "ALL" ? undefined : statusFilter,
        limit: 50,
      }),
    enabled: !!token,
  });

  const cancelMutation = useMutation({
    mutationFn: (orderId: string) => api.cancelOrder(orderId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["orders"] }),
  });

  const orders = ordersResp?.data ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("nav.orders")}</h1>

      {/* Status filter tabs */}
      <div className="flex flex-wrap gap-2">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === s
                ? "bg-blue-600 text-white"
                : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
            }`}
          >
            {s === "ALL" ? "All" : s.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Orders table */}
      {isLoading ? (
        <div className="py-12 text-center text-zinc-500">{t("common.loading")}</div>
      ) : orders.length === 0 ? (
        <div className="py-12 text-center text-zinc-500">{t("common.noData")}</div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-900">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500">
                <th className="px-4 py-3">Market</th>
                <th className="px-4 py-3">Side</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3 text-right">Price</th>
                <th className="px-4 py-3 text-right">Size</th>
                <th className="px-4 py-3 text-right">Filled</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.order_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                  <td className="max-w-[150px] truncate px-4 py-3 text-white">
                    {order.market_id.slice(0, 10)}...
                  </td>
                  <td className="px-4 py-3">
                    <span className={order.side === "BUY" ? "text-green-400" : "text-red-400"}>
                      {order.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-400">{order.type}</td>
                  <td className="px-4 py-3 text-right text-zinc-300">{order.price.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-zinc-300">{order.size}</td>
                  <td className="px-4 py-3 text-right text-zinc-300">{order.size_filled}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        order.status === "FILLED"
                          ? "bg-green-900/50 text-green-400"
                          : order.status === "CANCELLED"
                          ? "bg-zinc-800 text-zinc-500"
                          : order.status === "OPEN" || order.status === "PARTIALLY_FILLED"
                          ? "bg-blue-900/50 text-blue-400"
                          : "bg-zinc-800 text-zinc-400"
                      }`}
                    >
                      {order.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-xs text-zinc-500">
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {(order.status === "OPEN" || order.status === "PARTIALLY_FILLED") && (
                      <button
                        onClick={() => cancelMutation.mutate(order.order_id)}
                        disabled={cancelMutation.isPending}
                        className="rounded-md px-2 py-1 text-xs text-red-400 hover:bg-red-900/30"
                      >
                        {t("common.cancel")}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
