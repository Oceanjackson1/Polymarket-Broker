"use client";

import { useState, useCallback, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import MarketCard from "@/components/market/MarketCard";
import MarketSearch from "@/components/market/MarketSearch";
import { useAuthContext, useLocale } from "@/lib/providers";
import type { Market } from "@/lib/api-client";

export default function MarketsClient({
  initialMarkets,
}: {
  initialMarkets: Market[];
}) {
  const { api } = useAuthContext();
  const { t } = useLocale();
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState("all");

  // Search query (client-side, triggers when user types)
  const { data: searchResults } = useQuery({
    queryKey: ["markets-search", searchQuery],
    queryFn: () => api.searchMarkets(searchQuery),
    enabled: searchQuery.length >= 2,
    select: (res) => res.data,
  });

  // Filtered markets by category
  const { data: categoryMarkets } = useQuery({
    queryKey: ["markets", category],
    queryFn: () =>
      api.getMarkets({
        limit: 30,
        category: category === "all" ? undefined : category,
      }),
    enabled: category !== "all" && !searchQuery,
    select: (res) => res.data,
  });

  const markets = useMemo(() => {
    if (searchQuery.length >= 2 && searchResults) return searchResults;
    if (category !== "all" && categoryMarkets) return categoryMarkets;
    return initialMarkets;
  }, [searchQuery, searchResults, category, categoryMarkets, initialMarkets]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("nav.markets")}</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Browse and trade prediction markets
        </p>
      </div>

      <MarketSearch
        onSearch={setSearchQuery}
        onCategoryChange={setCategory}
        activeCategory={category}
      />

      {markets.length === 0 ? (
        <div className="py-12 text-center text-zinc-500">
          {t("common.noData")}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {markets.map((market) => (
            <MarketCard key={market.id} market={market} />
          ))}
        </div>
      )}
    </div>
  );
}
