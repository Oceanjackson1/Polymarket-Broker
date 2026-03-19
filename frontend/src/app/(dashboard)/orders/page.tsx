"use client";

import { useOrders } from "@/lib/hooks/use-orders";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ordersApi } from "@/lib/api";

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-bg-elevated ${className}`} />
  );
}

type OrderStatus = "OPEN" | "PARTIALLY_FILLED" | "FILLED" | "CANCELLED";

const statusConfig: Record<OrderStatus, { label: string; className: string }> = {
  OPEN: {
    label: "Open",
    className: "bg-info-blue/20 text-info-blue",
  },
  PARTIALLY_FILLED: {
    label: "Partial",
    className: "bg-warning/20 text-warning",
  },
  FILLED: {
    label: "Filled",
    className: "bg-profit-bg text-profit",
  },
  CANCELLED: {
    label: "Cancelled",
    className: "bg-bg-elevated text-text-muted",
  },
};

function getStatusConfig(status: string): { label: string; className: string } {
  return statusConfig[status as OrderStatus] ?? {
    label: status,
    className: "bg-bg-elevated text-text-muted",
  };
}

function canCancel(status: string): boolean {
  return status === "OPEN" || status === "PARTIALLY_FILLED";
}

function formatDate(isoString: string): string {
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return isoString;
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function OrdersPage() {
  const { data, isLoading, error } = useOrders();
  const queryClient = useQueryClient();
  const cancelMutation = useMutation({
    mutationFn: (orderId: string) => ordersApi.cancel(orderId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["orders"] }),
  });

  const orders = data?.data ?? [];
  const openCount = orders.filter((o) => o.status === "OPEN").length;
  const partialCount = orders.filter((o) => o.status === "PARTIALLY_FILLED").length;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Orders</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Order history and active positions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isLoading ? (
            <Skeleton className="h-4 w-32" />
          ) : (
            <span className="font-mono text-xs text-text-muted">
              {openCount} open · {partialCount} partial
            </span>
          )}
        </div>
      </div>

      {/* Orders Table */}
      {isLoading ? (
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <div className="space-y-px bg-bg-card">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full rounded-none" />
            ))}
          </div>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center">
          <p className="text-sm text-loss">Failed to load orders</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center">
          <p className="text-sm text-text-muted">No orders found</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle bg-bg-card">
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">
                  Market
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-text-muted">
                  Side
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Price
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Size
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Filled
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">
                  Created
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">
                  Action
                </th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const statusStyle = getStatusConfig(order.status);
                const sizeFilled = parseFloat(String(order.size_filled ?? 0));
                const sizeTotal = parseFloat(String(order.size ?? 0));
                return (
                  <tr
                    key={order.order_id}
                    className="border-b border-border-subtle bg-bg-base last:border-0"
                  >
                    {/* Status */}
                    <td className="px-4 py-3">
                      <span
                        className={`rounded px-2 py-0.5 font-mono text-[10px] font-medium ${statusStyle.className}`}
                      >
                        {statusStyle.label}
                      </span>
                    </td>

                    {/* Market */}
                    <td className="px-4 py-3 text-sm text-text-primary">
                      <span className="block max-w-[200px] truncate" title={order.market_id}>
                        {order.market_id}
                      </span>
                    </td>

                    {/* Side */}
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-medium ${
                          order.side === "BUY"
                            ? "bg-profit-bg text-profit"
                            : "bg-loss-bg text-loss"
                        }`}
                      >
                        {order.side}
                      </span>
                    </td>

                    {/* Price */}
                    <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                      {parseFloat(String(order.price)).toFixed(2)}
                    </td>

                    {/* Size */}
                    <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                      ${sizeTotal.toFixed(2)}
                    </td>

                    {/* Filled */}
                    <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                      ${sizeFilled.toFixed(2)}
                    </td>

                    {/* Created */}
                    <td className="px-4 py-3 text-sm text-text-muted">
                      {formatDate(String(order.created_at))}
                    </td>

                    {/* Action */}
                    <td className="px-4 py-3 text-right">
                      {canCancel(order.status) ? (
                        <button
                          onClick={() => cancelMutation.mutate(order.order_id)}
                          disabled={cancelMutation.isPending}
                          className="rounded-md border border-border-default px-3 py-1 text-xs font-medium text-text-secondary transition-colors hover:border-loss hover:text-loss disabled:opacity-50"
                        >
                          {cancelMutation.isPending ? "…" : "Cancel"}
                        </button>
                      ) : (
                        <span className="text-xs text-text-muted">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary Row */}
      <div className="mt-4 flex items-center justify-between px-1">
        <p className="text-xs text-text-muted">
          {isLoading ? "Loading…" : `Showing ${orders.length} orders`}
        </p>
        <p className="text-xs text-text-muted">
          Broker fee applies per executed order. See{" "}
          <a href="/pricing" className="text-accent-gold hover:underline">
            Pricing
          </a>{" "}
          for details.
        </p>
      </div>
    </div>
  );
}
