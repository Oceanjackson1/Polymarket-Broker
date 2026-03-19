"use client";

import Link from "next/link";
import { useSportsCategories } from "@/lib/hooks/use-sports";

function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded bg-bg-elevated ${className}`} />
  );
}

// Map known slugs to display names and icons
const SLUG_META: Record<string, { name: string; icon: string }> = {
  nba: { name: "NBA", icon: "🏀" },
  nfl: { name: "NFL", icon: "🏈" },
  mlb: { name: "MLB", icon: "⚾" },
  nhl: { name: "NHL", icon: "🏒" },
  ufc: { name: "UFC", icon: "🥊" },
  soccer: { name: "Soccer", icon: "⚽" },
  tennis: { name: "Tennis", icon: "🎾" },
  cs2: { name: "CS2", icon: "🎮" },
  dota2: { name: "Dota 2", icon: "🎮" },
  lol: { name: "LoL", icon: "🎮" },
  cricket: { name: "Cricket", icon: "🏏" },
  golf: { name: "Golf", icon: "⛳" },
  boxing: { name: "Boxing", icon: "🥊" },
  mma: { name: "MMA", icon: "🥊" },
  rugby: { name: "Rugby", icon: "🏉" },
  f1: { name: "Formula 1", icon: "🏎️" },
};

function getSlugMeta(slug: string): { name: string; icon: string } {
  if (SLUG_META[slug]) return SLUG_META[slug];
  // Capitalize first letter of slug as fallback
  const name = slug.charAt(0).toUpperCase() + slug.slice(1).replace(/-/g, " ");
  return { name, icon: "🏆" };
}

export default function SportsPage() {
  const { data: categories, isLoading, error } = useSportsCategories();

  const totalActiveEvents = categories
    ? categories.reduce((sum, c) => sum + (c.active_events ?? 0), 0)
    : null;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold text-text-primary">
            Sports Data
          </h1>
          <span className="rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] font-medium text-accent-gold">
            PRO
          </span>
        </div>
        <p className="mt-1 text-sm text-text-secondary">
          Historical orderbooks and real-time event data across sport and
          esports categories.
        </p>
      </div>

      {/* Stats Row */}
      <div className="mb-8 grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-border-subtle bg-bg-card p-5">
          <p className="text-xs text-text-muted">Total Categories</p>
          {isLoading ? (
            <Skeleton className="mt-2 h-8 w-16" />
          ) : (
            <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
              {categories ? categories.length : "—"}
            </p>
          )}
        </div>
        <div className="rounded-lg border border-border-subtle bg-bg-card p-5">
          <p className="text-xs text-text-muted">Active Events</p>
          {isLoading ? (
            <Skeleton className="mt-2 h-8 w-16" />
          ) : (
            <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
              {totalActiveEvents != null ? totalActiveEvents : "—"}
            </p>
          )}
        </div>
        <div className="rounded-lg border border-border-subtle bg-bg-card p-5">
          <p className="text-xs text-text-muted">Markets Tracked</p>
          <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
            —
          </p>
        </div>
      </div>

      {/* Category Grid */}
      <div>
        <h2 className="mb-4 text-sm font-semibold text-text-muted uppercase tracking-wider">
          Categories
        </h2>

        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
              <Skeleton key={i} className="h-36 w-full rounded-lg" />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-lg border border-border-subtle bg-bg-card p-6">
            <p className="text-sm text-loss">Failed to load sports categories</p>
          </div>
        ) : !categories || categories.length === 0 ? (
          <div className="rounded-lg border border-border-subtle bg-bg-card p-6">
            <p className="text-sm text-text-muted">No categories available</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {categories.map((sport) => {
              const meta = getSlugMeta(sport.slug);
              const activeEvents = sport.active_events ?? 0;
              return (
                <Link
                  key={sport.slug}
                  href={`/sports/${sport.slug}`}
                  className="group flex flex-col rounded-lg border border-border-subtle bg-bg-card p-5 transition-colors hover:border-accent-gold/30 hover:bg-bg-elevated"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-2xl">{meta.icon}</span>
                    <span
                      className={`font-mono text-xs font-medium ${
                        activeEvents > 0 ? "text-profit" : "text-text-muted"
                      }`}
                    >
                      {activeEvents > 0 ? `${activeEvents} live` : "no events"}
                    </span>
                  </div>
                  <h3 className="font-semibold text-text-primary group-hover:text-accent-gold">
                    {meta.name}
                  </h3>
                  <p className="mt-1 text-xs text-text-muted">
                    {activeEvents} active events
                  </p>
                  <div className="mt-4 text-xs font-medium text-accent-gold opacity-0 transition-opacity group-hover:opacity-100">
                    View events →
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Note */}
      <div className="mt-8 rounded-lg border border-border-subtle bg-bg-card p-4">
        <p className="text-sm text-text-secondary">
          <span className="font-medium text-text-primary">
            Historical Orderbooks
          </span>{" "}
          — Full orderbook history is available via API for all categories.
          Use the{" "}
          <span className="font-mono text-accent-gold">
            /api/v1/data/sports/:sport/orderbook
          </span>{" "}
          endpoint with your Pro API key.
        </p>
      </div>
    </div>
  );
}
