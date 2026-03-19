"use client";

import { useState, useMemo } from "react";
import Link from "next/link";

type Market = {
  slug: string;
  title: string;
  category: string;
  probability: number;
  volume: string;
  volumeRaw: number;
  yesLabel: string;
  href: string;
};

const CATEGORIES = ["All", "Politics", "Sports", "Crypto", "Science", "Culture"];

function ProbabilityBar({ pct }: { pct: number }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-bg-base">
      <div
        className="h-full rounded-full bg-accent-gold transition-all"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function MarketCard({ market, index }: { market: Market; index: number }) {
  const staggerN = Math.min((index % 6) + 1, 6);
  return (
    <div className={`hover-glow animate-fade-in stagger-${staggerN} flex flex-col rounded-xl border border-border-subtle bg-bg-card p-5 transition-colors hover:border-accent-gold/30`}>
      {/* Category badge */}
      <div className="mb-3 flex items-center gap-2">
        <span className="rounded bg-bg-elevated px-2 py-0.5 font-mono text-[10px] text-text-muted">
          {market.category.toUpperCase()}
        </span>
      </div>

      {/* Title */}
      <h2 className="mb-4 flex-1 text-sm font-semibold leading-snug text-text-primary">
        {market.title}
      </h2>

      {/* Probability display */}
      <div className="mb-3">
        <div className="mb-1.5 flex items-end justify-between">
          <span className="font-mono text-2xl font-bold text-accent-gold">
            {market.probability}%
          </span>
          <span className="text-sm font-medium text-text-secondary">
            {market.yesLabel}
          </span>
        </div>
        <ProbabilityBar pct={market.probability} />
      </div>

      {/* Volume + CTA */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">
          Vol:{" "}
          <span className="font-mono text-text-secondary">{market.volume}</span>
        </span>
        <Link
          href={market.href}
          className="rounded border border-border-default bg-bg-elevated px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:border-accent-gold/40 hover:text-text-primary"
        >
          Trade →
        </Link>
      </div>
    </div>
  );
}

export function MarketsClient({ markets }: { markets: Market[] }) {
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");

  const filtered = useMemo(() => {
    return markets.filter((m) => {
      const matchesCategory =
        activeCategory === "All" || m.category === activeCategory;
      const matchesQuery =
        query === "" ||
        m.title.toLowerCase().includes(query.toLowerCase()) ||
        m.category.toLowerCase().includes(query.toLowerCase());
      return matchesCategory && matchesQuery;
    });
  }, [markets, query, activeCategory]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      {/* Search bar */}
      <div className="mb-5 relative">
        <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-text-muted">
          🔍
        </span>
        <input
          type="search"
          placeholder="Search markets..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-xl border border-border-default bg-bg-card py-3 pl-10 pr-4 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-gold/50 focus:outline-none"
        />
      </div>

      {/* Category filters */}
      <div className="mb-8 flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              activeCategory === cat
                ? "bg-accent-gold text-bg-base"
                : "border border-border-default bg-bg-card text-text-secondary hover:border-accent-gold/40 hover:text-text-primary"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Result count */}
      <p className="mb-4 text-xs text-text-muted">
        Showing{" "}
        <span className="font-mono text-text-secondary">{filtered.length}</span>{" "}
        market{filtered.length !== 1 ? "s" : ""}
        {activeCategory !== "All" && ` in ${activeCategory}`}
        {query && ` matching "${query}"`}
      </p>

      {/* Market cards grid — 3 columns */}
      {filtered.length > 0 ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((market, i) => (
            <MarketCard key={market.slug} market={market} index={i} />
          ))}
        </div>
      ) : (
        <div className="flex h-40 items-center justify-center rounded-xl border border-border-subtle bg-bg-card">
          <p className="text-sm text-text-muted">
            No markets match your search.
          </p>
        </div>
      )}
    </div>
  );
}
