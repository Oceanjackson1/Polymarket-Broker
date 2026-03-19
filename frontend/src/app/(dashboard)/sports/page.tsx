"use client";

import Link from "next/link";

const sportCategories = [
  { name: "NBA", slug: "nba", activeEvents: 6, icon: "🏀" },
  { name: "NFL", slug: "nfl", activeEvents: 2, icon: "🏈" },
  { name: "MLB", slug: "mlb", activeEvents: 14, icon: "⚾" },
  { name: "NHL", slug: "nhl", activeEvents: 8, icon: "🏒" },
  { name: "UFC", slug: "ufc", activeEvents: 3, icon: "🥊" },
  { name: "Soccer", slug: "soccer", activeEvents: 22, icon: "⚽" },
  { name: "Tennis", slug: "tennis", activeEvents: 11, icon: "🎾" },
  { name: "CS2", slug: "cs2", activeEvents: 5, icon: "🎮" },
  { name: "Dota 2", slug: "dota2", activeEvents: 4, icon: "🎮" },
  { name: "LoL", slug: "lol", activeEvents: 7, icon: "🎮" },
];

export default function SportsPage() {
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
          Historical orderbooks and real-time event data across 145 sport and
          esports categories.
        </p>
      </div>

      {/* Stats Row */}
      <div className="mb-8 grid grid-cols-3 gap-4">
        {[
          { label: "Total Categories", value: "145" },
          { label: "Active Events", value: "82" },
          { label: "Markets Tracked", value: "1,240" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border border-border-subtle bg-bg-card p-5"
          >
            <p className="text-xs text-text-muted">{stat.label}</p>
            <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* Category Grid */}
      <div>
        <h2 className="mb-4 text-sm font-semibold text-text-muted uppercase tracking-wider">
          Categories
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {sportCategories.map((sport) => (
            <Link
              key={sport.slug}
              href={`/sports/${sport.slug}`}
              className="group flex flex-col rounded-lg border border-border-subtle bg-bg-card p-5 transition-colors hover:border-accent-gold/30 hover:bg-bg-elevated"
            >
              <div className="mb-3 flex items-center justify-between">
                <span className="text-2xl">{sport.icon}</span>
                <span
                  className={`font-mono text-xs font-medium ${
                    sport.activeEvents > 0 ? "text-profit" : "text-text-muted"
                  }`}
                >
                  {sport.activeEvents > 0
                    ? `${sport.activeEvents} live`
                    : "no events"}
                </span>
              </div>
              <h3 className="font-semibold text-text-primary group-hover:text-accent-gold">
                {sport.name}
              </h3>
              <p className="mt-1 text-xs text-text-muted">
                {sport.activeEvents} active events
              </p>
              <div className="mt-4 text-xs font-medium text-accent-gold opacity-0 transition-opacity group-hover:opacity-100">
                View events →
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Footer Note */}
      <div className="mt-8 rounded-lg border border-border-subtle bg-bg-card p-4">
        <p className="text-sm text-text-secondary">
          <span className="font-medium text-text-primary">
            Historical Orderbooks
          </span>{" "}
          — Full orderbook history is available via API for all 145 categories.
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
