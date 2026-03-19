"use client";

import { useState } from "react";

type OrderStatus = "OPEN" | "PARTIALLY_FILLED" | "FILLED" | "CANCELLED";

interface Order {
  id: string;
  status: OrderStatus;
  market: string;
  side: "BUY" | "SELL";
  price: string;
  size: string;
  filled: string;
  created: string;
}

const initialOrders: Order[] = [
  {
    id: "ord-001",
    status: "OPEN",
    market: "GSW vs LAL — Home Win",
    side: "BUY",
    price: "0.31",
    size: "$200",
    filled: "$0",
    created: "Mar 19, 14:22",
  },
  {
    id: "ord-002",
    status: "PARTIALLY_FILLED",
    market: "BTC >$70k by Mar 21",
    side: "BUY",
    price: "0.48",
    size: "$500",
    filled: "$180",
    created: "Mar 19, 12:05",
  },
  {
    id: "ord-003",
    status: "FILLED",
    market: "Trump wins 2028",
    side: "BUY",
    price: "0.42",
    size: "$300",
    filled: "$300",
    created: "Mar 18, 09:14",
  },
  {
    id: "ord-004",
    status: "FILLED",
    market: "ETH >$4k by Mar 22",
    side: "SELL",
    price: "0.55",
    size: "$150",
    filled: "$150",
    created: "Mar 18, 07:48",
  },
  {
    id: "ord-005",
    status: "CANCELLED",
    market: "UFC 300 — KO in Round 1",
    side: "BUY",
    price: "0.18",
    size: "$100",
    filled: "$0",
    created: "Mar 17, 22:30",
  },
  {
    id: "ord-006",
    status: "OPEN",
    market: "BOS vs MIA — Away Win",
    side: "BUY",
    price: "0.38",
    size: "$250",
    filled: "$0",
    created: "Mar 17, 19:55",
  },
];

const statusConfig: Record<
  OrderStatus,
  { label: string; className: string }
> = {
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

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>(initialOrders);
  const [cancelling, setCancelling] = useState<string | null>(null);

  function handleCancel(id: string) {
    setCancelling(id);
    setTimeout(() => {
      setOrders((prev) =>
        prev.map((o) => (o.id === id ? { ...o, status: "CANCELLED" } : o))
      );
      setCancelling(null);
    }, 800);
  }

  const canCancel = (status: OrderStatus) =>
    status === "OPEN" || status === "PARTIALLY_FILLED";

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
          <span className="font-mono text-xs text-text-muted">
            {orders.filter((o) => o.status === "OPEN").length} open ·{" "}
            {orders.filter((o) => o.status === "PARTIALLY_FILLED").length}{" "}
            partial
          </span>
        </div>
      </div>

      {/* Orders Table */}
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
              const statusStyle = statusConfig[order.status];
              return (
                <tr
                  key={order.id}
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
                    {order.market}
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
                    {order.price}
                  </td>

                  {/* Size */}
                  <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                    {order.size}
                  </td>

                  {/* Filled */}
                  <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                    {order.filled}
                  </td>

                  {/* Created */}
                  <td className="px-4 py-3 text-sm text-text-muted">
                    {order.created}
                  </td>

                  {/* Action */}
                  <td className="px-4 py-3 text-right">
                    {canCancel(order.status) ? (
                      <button
                        onClick={() => handleCancel(order.id)}
                        disabled={cancelling === order.id}
                        className="rounded-md border border-border-default px-3 py-1 text-xs font-medium text-text-secondary transition-colors hover:border-loss hover:text-loss disabled:opacity-50"
                      >
                        {cancelling === order.id ? "Cancelling…" : "Cancel"}
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

      {/* Summary Row */}
      <div className="mt-4 flex items-center justify-between px-1">
        <p className="text-xs text-text-muted">
          Showing {orders.length} orders
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
