"use client";

import { useBalance, usePnl, usePositions } from "@/lib/hooks/use-portfolio";
import { Shimmer } from "@/components/ui/shimmer";

function StatCard({
  label,
  children,
  loading,
  error,
}: {
  label: string;
  children: React.ReactNode;
  loading: boolean;
  error: boolean;
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-bg-card p-5">
      <p className="text-xs text-text-muted">{label}</p>
      {loading ? (
        <Shimmer className="mt-2 h-8 w-28" />
      ) : error ? (
        <p className="mt-1 font-mono text-2xl font-semibold text-loss">—</p>
      ) : (
        <div className="mt-1">{children}</div>
      )}
    </div>
  );
}

export default function PortfolioPage() {
  const balance = useBalance();
  const pnl = usePnl();
  const positions = usePositions();

  const totalAssets = balance.data?.balance ?? null;
  const available = balance.data?.available ?? null;
  const locked = balance.data?.locked ?? null;
  const realized = pnl.data?.realized ?? null;
  const unrealized = pnl.data?.unrealized ?? null;
  const positionList = positions.data?.positions ?? [];

  const totalPnl =
    realized != null && unrealized != null
      ? parseFloat(String(realized)) + parseFloat(String(unrealized))
      : null;

  return (
    <div className="flex min-h-full flex-col p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-text-primary">Portfolio</h1>
        <p className="text-xs text-text-muted">
          Positions, balance, and P&L overview
        </p>
      </div>

      {/* Stats Row */}
      <div className="mb-6 grid grid-cols-5 gap-4">
        <StatCard label="Total Balance" loading={balance.isLoading} error={!!balance.error}>
          <p className="font-mono text-2xl font-semibold text-text-primary">
            ${totalAssets != null ? parseFloat(String(totalAssets)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—"}
          </p>
        </StatCard>

        <StatCard label="Available" loading={balance.isLoading} error={!!balance.error}>
          <p className="font-mono text-2xl font-semibold text-profit">
            ${available != null ? parseFloat(String(available)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—"}
          </p>
        </StatCard>

        <StatCard label="Locked in Orders" loading={balance.isLoading} error={!!balance.error}>
          <p className="font-mono text-2xl font-semibold text-accent-gold">
            ${locked != null ? parseFloat(String(locked)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—"}
          </p>
        </StatCard>

        <StatCard label="Realized P&L" loading={pnl.isLoading} error={!!pnl.error}>
          <p className={`font-mono text-2xl font-semibold ${realized != null && parseFloat(String(realized)) >= 0 ? "text-profit" : "text-loss"}`}>
            {realized != null
              ? `${parseFloat(String(realized)) >= 0 ? "+" : ""}$${Math.abs(parseFloat(String(realized))).toFixed(2)}`
              : "—"}
          </p>
        </StatCard>

        <StatCard label="Total P&L" loading={pnl.isLoading} error={!!pnl.error}>
          <p className={`font-mono text-2xl font-semibold ${totalPnl != null && totalPnl >= 0 ? "text-profit" : "text-loss"}`}>
            {totalPnl != null
              ? `${totalPnl >= 0 ? "+" : ""}$${Math.abs(totalPnl).toFixed(2)}`
              : "—"}
          </p>
          {unrealized != null && (
            <p className={`mt-0.5 text-xs ${parseFloat(String(unrealized)) >= 0 ? "text-profit" : "text-loss"}`}>
              unrealized: {parseFloat(String(unrealized)) >= 0 ? "+" : ""}${Math.abs(parseFloat(String(unrealized))).toFixed(2)}
            </p>
          )}
        </StatCard>
      </div>

      {/* Positions Table */}
      <div className="rounded-lg border border-border-subtle bg-bg-card">
        <div className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Active Positions
          </p>
          <span className="text-xs text-text-muted">
            {positionList.length} positions
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle">
                {["Market", "Side", "Size", "Avg Price", "Notional", "Orders"].map((h) => (
                  <th
                    key={h}
                    className="px-5 py-2 text-left text-[10px] font-semibold uppercase tracking-wider text-text-muted"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {positions.isLoading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center">
                    <Shimmer className="mx-auto h-4 w-48" />
                  </td>
                </tr>
              ) : positions.error ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-sm text-loss">
                    Failed to load positions
                  </td>
                </tr>
              ) : positionList.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-sm text-text-muted">
                    No active positions
                  </td>
                </tr>
              ) : (
                positionList.map((pos) => {
                  const notional = parseFloat(String(pos.notional));
                  const isPositive = notional >= 0;
                  return (
                    <tr
                      key={pos.market_id}
                      className="border-b border-border-subtle/50 transition-colors hover:bg-bg-elevated last:border-0"
                    >
                      <td className="max-w-[200px] truncate px-5 py-2.5 font-mono text-sm text-text-primary">
                        {pos.market_id}
                      </td>
                      <td className="px-5 py-2.5">
                        <span
                          className={`rounded px-2 py-0.5 font-mono text-[10px] font-semibold ${
                            pos.side === "BUY"
                              ? "bg-profit-bg text-profit"
                              : "bg-loss-bg text-loss"
                          }`}
                        >
                          {pos.side}
                        </span>
                      </td>
                      <td className="px-5 py-2.5 font-mono text-sm text-text-secondary">
                        {parseFloat(String(pos.size_held)).toFixed(2)}
                      </td>
                      <td className="px-5 py-2.5 font-mono text-sm text-text-secondary">
                        ${parseFloat(String(pos.avg_price)).toFixed(4)}
                      </td>
                      <td className="px-5 py-2.5">
                        <span
                          className={`font-mono text-sm ${
                            isPositive ? "text-profit" : "text-loss"
                          }`}
                        >
                          {isPositive ? "+" : ""}${Math.abs(notional).toFixed(2)}
                        </span>
                      </td>
                      <td className="px-5 py-2.5 font-mono text-sm text-text-muted">
                        {pos.order_count}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
