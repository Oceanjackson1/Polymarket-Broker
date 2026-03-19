"use client";

import { useState, useCallback } from "react";
import { Search } from "lucide-react";
import { useLocale } from "@/lib/providers";

const CATEGORIES = [
  { key: "all", label: "All" },
  { key: "Sports", label: "Sports" },
  { key: "Crypto", label: "Crypto" },
  { key: "Politics", label: "Politics" },
  { key: "Weather", label: "Weather" },
  { key: "Tech", label: "Tech" },
  { key: "Economics", label: "Economics" },
];

type Props = {
  onSearch: (query: string) => void;
  onCategoryChange: (category: string) => void;
  activeCategory: string;
};

export default function MarketSearch({
  onSearch,
  onCategoryChange,
  activeCategory,
}: Props) {
  const [query, setQuery] = useState("");
  const { t } = useLocale();

  const handleSearch = useCallback(
    (value: string) => {
      setQuery(value);
      onSearch(value);
    },
    [onSearch]
  );

  return (
    <div className="space-y-3">
      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search markets..."
          className="w-full rounded-md border border-zinc-700 bg-zinc-800 py-2 pl-10 pr-4 text-sm text-white placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
        />
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            onClick={() => onCategoryChange(cat.key)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              activeCategory === cat.key
                ? "bg-blue-600 text-white"
                : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>
    </div>
  );
}
