"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { sportsApi } from "@/lib/api";
import Link from "next/link";

export default function SportEventsPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);

  const { data, isLoading, error } = useQuery({
    queryKey: ["sports-events", slug],
    queryFn: () => sportsApi.events(slug),
    staleTime: 30_000,
  });

  const events = data?.data ?? [];

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center gap-3">
        <Link href="/sports" className="text-xs text-accent-gold hover:underline">
          ← Sports
        </Link>
        <h1 className="text-xl font-semibold capitalize text-text-primary">{slug.replace(/-/g, " ")}</h1>
        {data && (
          <span className="font-mono text-xs text-text-muted">{events.length} events</span>
        )}
      </div>

      {data?.stale && (
        <div className="mb-4 rounded-md bg-warning/10 px-4 py-2 text-xs text-warning">
          ⚠ Data may be stale
        </div>
      )}

      {isLoading ? (
        <div className="space-y-px rounded-lg border border-border-subtle">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 animate-pulse bg-bg-elevated" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-sm text-loss">
          Failed to load events
        </div>
      ) : events.length === 0 ? (
        <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-sm text-text-muted">
          No active events for this sport
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle bg-bg-card">
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">Event</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-text-muted">Status</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">Volume</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-text-muted">End Date</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.market_id} className="border-b border-border-subtle bg-bg-base last:border-0 hover:bg-bg-elevated/50">
                  <td className="px-4 py-3">
                    <Link
                      href={`/trade/${event.market_id}`}
                      className="text-sm text-text-primary hover:text-accent-gold"
                    >
                      {event.question}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-medium ${
                      event.status === "active"
                        ? "bg-profit-bg text-profit"
                        : "bg-bg-elevated text-text-muted"
                    }`}>
                      {event.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sm text-text-secondary">
                    {event.volume ? `$${(event.volume / 1000).toFixed(0)}K` : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-text-muted">
                    {event.end_date ? new Date(event.end_date).toLocaleDateString() : "—"}
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
