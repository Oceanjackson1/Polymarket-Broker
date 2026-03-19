"use client";

import { useState } from "react";

type OrderStatus = "OPEN" | "PARTIAL" | "FILLED" | "CANCELLED";

interface Order {
  id: string;
  status: OrderStatus;
  side: "BUY" | "SELL";
  price: number;
  size: number;
  filled: number;
}

const MOCK_ORDERS: Order[] = [
  { id: "ord-001", status: "OPEN", side: "BUY", price: 0.73, size: 200, filled: 0 },
  { id: "ord-002", status: "PARTIAL", side: "BUY", price: 0.74, size: 500, filled: 200 },
  { id: "ord-003", status: "FILLED", side: "SELL", price: 0.76, size: 300, filled: 300 },
];

const STATUS_CLASSES: Record<OrderStatus, string> = {
  OPEN: "text-info-cyan bg-bg-elevated",
  PARTIAL: "text-warning bg-bg-elevated",
  FILLED: "text-profit bg-profit-bg",
  CANCELLED: "text-text-muted bg-bg-elevated",
};

interface MyOrdersProps {
  marketId: string;
}

export default function MyOrders({ marketId: _marketId }: MyOrdersProps) {
  const [orders, setOrders] = useState<Order[]>(MOCK_ORDERS);

  function cancelOrder(id: string) {
    setOrders((prev) =>
      prev.map((o) => (o.id === id ? { ...o, status: "CANCELLED" as OrderStatus } : o))
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Panel header */}
      <div className="border-b border-border-subtle px-4 py-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
          My Orders
        </span>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-x-auto overflow-y-auto">
        <table className="w-full min-w-[500px] text-xs">
          <thead>
            <tr className="border-b border-border-subtle">
              {["Status", "Side", "Price", "Size", "Filled", "Remaining", "Action"].map(
                (h) => (
                  <th
                    key={h}
                    className="px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted"
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => {
              const canCancel =
                order.status === "OPEN" || order.status === "PARTIAL";
              return (
                <tr
                  key={order.id}
                  className="border-b border-border-subtle hover:bg-bg-elevated"
                >
                  <td className="px-3 py-2">
                    <span
                      className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-semibold ${STATUS_CLASSES[order.status]}`}
                    >
                      {order.status}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`font-mono font-semibold ${order.side === "BUY" ? "text-profit" : "text-loss"}`}
                    >
                      {order.side}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-text-primary">
                    {order.price.toFixed(3)}
                  </td>
                  <td className="px-3 py-2 font-mono text-text-primary">
                    {order.size.toLocaleString()}
                  </td>
                  <td className="px-3 py-2 font-mono text-text-secondary">
                    {order.filled.toLocaleString()}
                  </td>
                  <td className="px-3 py-2 font-mono text-text-secondary">
                    {(order.size - order.filled).toLocaleString()}
                  </td>
                  <td className="px-3 py-2">
                    {canCancel ? (
                      <button
                        onClick={() => cancelOrder(order.id)}
                        className="rounded border border-loss/40 px-2 py-0.5 text-[10px] text-loss transition-colors hover:bg-loss-bg"
                      >
                        Cancel
                      </button>
                    ) : (
                      <span className="text-text-muted">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {orders.length === 0 && (
          <div className="px-4 py-8 text-center text-sm text-text-muted">
            No orders for this market
          </div>
        )}
      </div>
    </div>
  );
}
