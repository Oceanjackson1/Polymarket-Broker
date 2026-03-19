import type { Metadata } from "next";
import { MarketsClient } from "./_components/markets-client";

// ── Metadata (SSG) ────────────────────────────────────────────────────────────

export const metadata: Metadata = {
  title: "Prediction Markets — Browse All Markets",
  description:
    "Browse prediction markets across politics, sports, crypto, and more. Real-time odds updated every minute.",
  openGraph: {
    title: "Prediction Markets — Browse All Markets",
    description:
      "Browse prediction markets across politics, sports, crypto, and more.",
  },
};

// ── Mock data (would come from generateStaticParams / fetch at build time) ────

export const MOCK_MARKETS = [
  {
    slug: "will-trump-win-2028",
    title: "Will Trump win the 2028 presidential election?",
    category: "Politics",
    probability: 35,
    volume: "$1.2M",
    volumeRaw: 1200000,
    yesLabel: "YES",
    href: "/markets/will-trump-win-2028",
  },
  {
    slug: "btc-above-100k-july-2026",
    title: "BTC above $100K by July 2026?",
    category: "Crypto",
    probability: 42,
    volume: "$890K",
    volumeRaw: 890000,
    yesLabel: "YES",
    href: "/markets/btc-above-100k-july-2026",
  },
  {
    slug: "gsw-vs-lal-winner",
    title: "GSW vs LAL — tonight's winner",
    category: "Sports",
    probability: 69,
    volume: "$340K",
    volumeRaw: 340000,
    yesLabel: "LAL",
    href: "/markets/gsw-vs-lal-winner",
  },
  {
    slug: "fed-rate-cut-q1-2026",
    title: "Fed rate cut in Q1 2026?",
    category: "Politics",
    probability: 58,
    volume: "$2.1M",
    volumeRaw: 2100000,
    yesLabel: "YES",
    href: "/markets/fed-rate-cut-q1-2026",
  },
  {
    slug: "eth-above-5k-2026",
    title: "ETH above $5K in 2026?",
    category: "Crypto",
    probability: 31,
    volume: "$675K",
    volumeRaw: 675000,
    yesLabel: "YES",
    href: "/markets/eth-above-5k-2026",
  },
  {
    slug: "superbowl-lxi-winner",
    title: "Super Bowl LXI winner — Kansas City Chiefs?",
    category: "Sports",
    probability: 22,
    volume: "$4.5M",
    volumeRaw: 4500000,
    yesLabel: "YES",
    href: "/markets/superbowl-lxi-winner",
  },
  {
    slug: "ai-agi-before-2030",
    title: "AGI achieved before 2030?",
    category: "Science",
    probability: 18,
    volume: "$3.2M",
    volumeRaw: 3200000,
    yesLabel: "YES",
    href: "/markets/ai-agi-before-2030",
  },
  {
    slug: "oscar-best-picture-2027",
    title: "Which film wins Best Picture at Oscars 2027?",
    category: "Culture",
    probability: 12,
    volume: "$210K",
    volumeRaw: 210000,
    yesLabel: "Frontrunner",
    href: "/markets/oscar-best-picture-2027",
  },
  {
    slug: "ufc-309-main-event",
    title: "UFC 309 — Main event winner",
    category: "Sports",
    probability: 65,
    volume: "$890K",
    volumeRaw: 890000,
    yesLabel: "Favourite",
    href: "/markets/ufc-309-main-event",
  },
];

// ── JSON-LD ItemList schema ───────────────────────────────────────────────────

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "ItemList",
  name: "Prediction Markets",
  description:
    "Browse all prediction markets across politics, sports, crypto, science, and culture.",
  numberOfItems: MOCK_MARKETS.length,
  itemListElement: MOCK_MARKETS.map((market, index) => ({
    "@type": "ListItem",
    position: index + 1,
    name: market.title,
    url: `https://broker.polymarket.com${market.href}`,
    description: `Current probability: ${market.probability}% ${market.yesLabel}. Volume: ${market.volume}.`,
  })),
};

// ── Page (server component — SSG) ────────────────────────────────────────────

export default function MarketsPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="min-h-screen bg-black">
        {/* Page header */}
        <div className="border-b border-white/[0.06] bg-black px-6 py-10">
          <div className="mx-auto max-w-6xl">
            <p className="mb-3 text-xs font-medium uppercase tracking-widest text-white/25">
              Markets
            </p>
            <h1 className="text-3xl font-semibold tracking-tight text-white">
              Prediction Markets
            </h1>
            <p className="mt-2 text-[15px] text-white/60">
              Browse{" "}
              <span className="font-mono tabular-nums text-white">
                {MOCK_MARKETS.length}
              </span>{" "}
              markets across politics, sports, crypto, science, and culture.
              Odds updated every minute.
            </p>
          </div>
        </div>

        {/* Client component handles search + filter interactivity */}
        <MarketsClient markets={MOCK_MARKETS} />
      </div>
    </>
  );
}
