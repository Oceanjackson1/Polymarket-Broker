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
    <div className="h-1 w-full rounded-full bg-white/[0.06]">
      <div
        className="h-full rounded-full bg-white/40 transition-all"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function MarketCard({ market, index }: { market: Market; index: number }) {
  const staggerN = Math.min((index % 6) + 1, 6);
  return (
    <div className={`animate-fade-in stagger-${staggerN} flex flex-col rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 transition-all hover:border-white/[0.12] hover:bg-white/[0.04]`}>
      {/* Category badge */}
      <div className="mb-3 flex items-center gap-2">
        <span className="rounded-full bg-white/[0.06] px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-widest text-white/40">
          {market.category}
        </span>
      </div>

      {/* Title */}
      <h2 className="mb-4 flex-1 text-[15px] font-semibold leading-snug text-white">
        {market.title}
      </h2>

      {/* Probability display */}
      <div className="mb-3">
        <div className="mb-2 flex items-end justify-between">
          <span className="font-mono text-2xl font-semibold tabular-nums text-white">
            {market.probability}%
          </span>
          <span className="text-sm text-white/40">
            {market.yesLabel}
          </span>
        </div>
        <ProbabilityBar pct={market.probability} />
      </div>

      {/* Volume + CTA */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-white/40">
          Vol:{" "}
          <span className="font-mono tabular-nums text-white/60">{market.volume}</span>
        </span>
        <Link
          href={market.href}
          className="rounded-full border border-white/15 px-3 py-1.5 text-xs font-medium text-white/60 transition-all hover:border-white/30 hover:text-white"
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
    <div className="mx-auto max-w-6xl px-6 py-8">
      {/* Search bar */}
      <div className="relative mb-5">
        <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-white/25 text-sm">
          ⌕
        </span>
        <input
          type="search"
          placeholder="Search markets..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] py-3 pl-10 pr-4 text-[15px] text-white placeholder:text-white/25 focus:border-white/20 focus:outline-none"
        />
      </div>

      {/* Category filters */}
      <div className="mb-8 flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`rounded-full px-4 py-2 text-[13px] font-medium transition-all ${
              activeCategory === cat
                ? "bg-white text-black"
                : "border border-white/[0.08] bg-white/[0.02] text-white/60 hover:border-white/20 hover:text-white"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Result count */}
      <p className="mb-4 text-xs text-white/25">
        Showing{" "}
        <span className="font-mono tabular-nums text-white/60">{filtered.length}</span>{" "}
        market{filtered.length !== 1 ? "s" : ""}
        {activeCategory !== "All" && ` in ${activeCategory}`}
        {query && ` matching "${query}"`}
      </p>

      {/* Market cards grid — 3 columns */}
      {filtered.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((market, i) => (
            <MarketCard key={market.slug} market={market} index={i} />
          ))}
        </div>
      ) : (
        <div className="flex h-40 items-center justify-center rounded-2xl border border-white/[0.06] bg-white/[0.02]">
          <p className="text-[15px] text-white/40">
            No markets match your search.
          </p>
        </div>
      )}
    </div>
  );
}
