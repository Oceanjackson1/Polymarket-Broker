"use client";

import { useState } from "react";
import Link from "next/link";
import { useMarkets } from "@/lib/hooks/use-markets";
import { Shimmer } from "@/components/ui/shimmer";
import type { MarketResponse } from "@/lib/api";

const CATEGORIES = ["All", "Crypto", "Sports", "Politics", "Science", "Culture"] as const;

function formatVolume(v: unknown): string {
  const n = typeof v === "number" ? v : parseFloat(String(v ?? "0"));
  if (isNaN(n) || n === 0) return "—";
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

function matchesCategory(market: MarketResponse, cat: string): boolean {
  if (cat === "All") return true;
  const tags = (market as Record<string, unknown>).tags;
  if (Array.isArray(tags)) {
    return tags.some((t: unknown) =>
      String(t).toLowerCase().includes(cat.toLowerCase())
    );
  }
  const title = String((market as Record<string, unknown>).title ?? "");
  return title.toLowerCase().includes(cat.toLowerCase());
}

function MarketRow({ market }: { market: MarketResponse }) {
  const m = market as Record<string, unknown>;
  const title = String(m.title ?? m.question ?? "Unknown Market");
  const slug = String(m.market_slug ?? m.condition_id ?? m.id ?? "");
  const volume = m.volume_total ?? m.volume_1_week ?? 0;
  const status = String(m.status ?? "open");
  const sideA = m.side_a as { label?: string } | undefined;
  const sideB = m.side_b as { label?: string } | undefined;
  const tags = Array.isArray(m.tags) ? m.tags.slice(0, 3) : [];

  return (
    <Link
      href={`/trade/${slug}`}
      className="group flex items-center justify-between border-b border-border-subtle/50 px-5 py-3.5 transition-colors hover:bg-bg-elevated last:border-0"
    >
      <div className="flex flex-1 flex-col gap-1 pr-4">
        <span className="text-sm text-text-primary group-hover:text-accent-gold transition-colors">
          {title.length > 80 ? title.slice(0, 80) + "…" : title}
        </span>
        <div className="flex items-center gap-2">
          {tags.map((tag: unknown) => (
            <span
              key={String(tag)}
              className="rounded bg-bg-elevated px-1.5 py-0.5 text-[10px] text-text-muted"
            >
              {String(tag)}
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Sides */}
        {sideA && (
          <div className="flex gap-2">
            <span className="rounded bg-profit-bg px-2 py-0.5 font-mono text-[10px] font-semibold text-profit">
              {sideA.label ?? "A"}
            </span>
            {sideB && (
              <span className="rounded bg-loss-bg px-2 py-0.5 font-mono text-[10px] font-semibold text-loss">
                {sideB.label ?? "B"}
              </span>
            )}
          </div>
        )}

        {/* Volume */}
        <span className="w-16 text-right font-mono text-xs text-text-muted">
          {formatVolume(volume)}
        </span>

        {/* Status */}
        <span
          className={`w-14 text-center rounded px-2 py-0.5 text-[10px] font-semibold ${
            status === "open"
              ? "bg-profit-bg text-profit"
              : "bg-bg-elevated text-text-muted"
          }`}
        >
          {status.toUpperCase()}
        </span>
      </div>
    </Link>
  );
}

export default function MarketsPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("All");
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const { data, isLoading, error } = useMarkets({ limit: 100 });
  const allMarkets = data?.data ?? [];

  // Client-side filter
  const filtered = allMarkets.filter((m) => {
    if (!matchesCategory(m, category)) return false;
    if (search.trim()) {
      const title = String((m as Record<string, unknown>).title ?? "").toLowerCase();
      if (!title.includes(search.toLowerCase())) return false;
    }
    return true;
  });

  const paged = filtered.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(filtered.length / pageSize);

  return (
    <div className="flex min-h-full flex-col p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-text-primary">Markets</h1>
          <p className="text-xs text-text-muted">
            {filtered.length} markets available
          </p>
        </div>
      </div>

      {/* Search + Filter */}
      <div className="mb-4 flex items-center gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          placeholder="Search markets..."
          className="w-64 rounded border border-border-subtle bg-bg-card px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-gold/50 focus:outline-none"
        />
        <div className="flex gap-1">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => {
                setCategory(cat);
                setPage(0);
              }}
              className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                category === cat
                  ? "bg-accent-gold text-bg-base"
                  : "bg-bg-elevated text-text-muted hover:text-text-primary"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border-subtle bg-bg-card">
        {/* Table Header */}
        <div className="flex items-center justify-between border-b border-border-subtle px-5 py-2.5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted">
            Market
          </span>
          <div className="flex items-center gap-6">
            <span className="w-14 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Sides
            </span>
            <span className="w-16 text-right text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Volume
            </span>
            <span className="w-14 text-center text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Status
            </span>
          </div>
        </div>

        {/* Rows */}
        {isLoading ? (
          <div className="space-y-0">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="border-b border-border-subtle/50 px-5 py-4">
                <Shimmer className="h-4 w-3/4" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="px-5 py-8 text-center text-sm text-loss">
            Failed to load markets
          </div>
        ) : paged.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-text-muted">
            {search ? "No markets match your search" : "No markets available"}
          </div>
        ) : (
          paged.map((market, i) => (
            <div key={String((market as Record<string, unknown>).condition_id ?? i)} className={`animate-fade-in stagger-${Math.min(i + 1, 6)}`}>
              <MarketRow market={market} />
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="rounded border border-border-subtle bg-bg-card px-3 py-1.5 text-xs text-text-muted transition-colors hover:text-text-primary disabled:opacity-30"
          >
            ← Prev
          </button>
          <span className="text-xs text-text-muted">
            {page + 1} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="rounded border border-border-subtle bg-bg-card px-3 py-1.5 text-xs text-text-muted transition-colors hover:text-text-primary disabled:opacity-30"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
