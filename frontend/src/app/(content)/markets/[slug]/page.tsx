import type { Metadata } from "next";
import Link from "next/link";
import { MOCK_MARKETS } from "../page";
import { AnimatedProbability } from "./_components/animated-probability";

// ── generateStaticParams — build all known market pages at build time ─────────

export function generateStaticParams() {
  return MOCK_MARKETS.map((m) => ({ slug: m.slug }));
}

// ── Mock market detail data (superset of the list data) ──────────────────────

const MARKET_DETAIL: Record<
  string,
  {
    resolution: string;
    endDate: string;
    category: string;
    description: string;
    priceHistory: number[];
  }
> = {
  "will-trump-win-2028": {
    resolution:
      "Resolves YES if Donald Trump wins the 2028 US presidential election.",
    endDate: "Nov 4, 2028",
    category: "Politics",
    description:
      "This market tracks the probability that Donald Trump wins the 2028 US presidential election. Odds update in real time based on Polymarket trading activity.",
    priceHistory: [0.28, 0.3, 0.32, 0.29, 0.31, 0.33, 0.35, 0.34, 0.35],
  },
  "btc-above-100k-july-2026": {
    resolution: "Resolves YES if Bitcoin closes above $100,000 on July 31, 2026.",
    endDate: "Jul 31, 2026",
    category: "Crypto",
    description:
      "Will Bitcoin exceed $100,000 USD by end of July 2026? This market resolves based on the Coinbase BTC-USD closing price on the resolution date.",
    priceHistory: [0.35, 0.38, 0.4, 0.37, 0.39, 0.41, 0.43, 0.42, 0.42],
  },
  "gsw-vs-lal-winner": {
    resolution:
      "Resolves to the team that wins the game played on March 19, 2026.",
    endDate: "Mar 19, 2026",
    category: "Sports",
    description:
      "Tonight's NBA game between the Golden State Warriors and the Los Angeles Lakers. Odds fuse ESPN live score data with Polymarket order flow.",
    priceHistory: [0.5, 0.55, 0.58, 0.6, 0.63, 0.65, 0.67, 0.68, 0.69],
  },
};

// Default detail for markets not in the detail map
const DEFAULT_DETAIL = {
  resolution: "Resolves based on publicly verifiable data at end date.",
  endDate: "TBD",
  category: "General",
  description: "A prediction market tracked on the Polymarket Broker platform.",
  priceHistory: [0.3, 0.35, 0.32, 0.38, 0.4, 0.42, 0.41, 0.43],
};

// ── generateMetadata (dynamic per slug) ──────────────────────────────────────

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const market = MOCK_MARKETS.find((m) => m.slug === slug);

  if (!market) {
    return {
      title: "Market Not Found",
      description: "This prediction market could not be found.",
    };
  }

  return {
    title: `${market.title} — Prediction Market Odds`,
    description: `Current odds for "${market.title}": ${market.probability}% ${market.yesLabel}. Volume: ${market.volume}. Trade now on Polymarket Broker.`,
    openGraph: {
      title: `${market.title} — Prediction Market Odds`,
      description: `${market.probability}% ${market.yesLabel} · Volume ${market.volume}`,
      type: "article",
    },
  };
}

// ── Page (server component — SSG) ────────────────────────────────────────────

export default async function MarketDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  const market = MOCK_MARKETS.find((m) => m.slug === slug);
  const detail = MARKET_DETAIL[slug] ?? DEFAULT_DETAIL;

  // Handle not found gracefully (generateStaticParams covers known slugs)
  if (!market) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center">
        <p className="text-white/40">Market not found.</p>
        <Link
          href="/markets"
          className="mt-4 inline-block text-white/60 transition-colors hover:text-white"
        >
          ← Back to Markets
        </Link>
      </div>
    );
  }

  // ── JSON-LD Article schema ─────────────────────────────────────────────────
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: market.title,
    description: detail.description,
    dateModified: new Date().toISOString(),
    about: {
      "@type": "Thing",
      name: market.title,
    },
    mainEntity: {
      "@type": "Question",
      name: market.title,
      acceptedAnswer: {
        "@type": "Answer",
        text: `Current probability: ${market.probability}% ${market.yesLabel}. Volume: ${market.volume}. Resolution: ${detail.resolution}`,
      },
    },
    publisher: {
      "@type": "Organization",
      name: "Polymarket Broker",
      url: "https://broker.polymarket.com",
    },
  };

  // ── Chart helpers ──────────────────────────────────────────────────────────
  const history = detail.priceHistory;
  const minProb = Math.min(...history);
  const maxProb = Math.max(...history);
  const probRange = maxProb - minProb || 0.01;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="min-h-screen bg-black">
        {/* Back nav */}
        <div className="border-b border-white/[0.06] bg-black">
          <div className="mx-auto max-w-4xl px-6 py-3">
            <Link
              href="/markets"
              className="text-xs text-white/40 transition-colors hover:text-white/60"
            >
              ← All Markets
            </Link>
          </div>
        </div>

        <div className="mx-auto max-w-4xl px-6 py-10">
          {/* ── Market Title + Probability ──────────────────── */}
          <div className="mb-8">
            <div className="mb-3 flex items-center gap-2">
              <span className="rounded-full bg-white/[0.06] px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-widest text-white/40">
                {detail.category}
              </span>
            </div>
            <h1 className="mb-4 text-2xl font-semibold leading-snug tracking-tight text-white">
              {market.title}
            </h1>
            <div className="flex flex-wrap items-center gap-4">
              <AnimatedProbability probability={market.probability} yesLabel={market.yesLabel} />
              <div className="h-8 w-px bg-white/[0.08]" />
              <div>
                <p className="text-[10px] font-medium uppercase tracking-widest text-white/25">
                  Volume
                </p>
                <p className="font-mono text-lg font-semibold tabular-nums text-white">
                  {market.volume}
                </p>
              </div>
              <div className="h-8 w-px bg-white/[0.08]" />
              <div>
                <p className="text-[10px] font-medium uppercase tracking-widest text-white/25">
                  Last Updated
                </p>
                <p className="font-mono text-sm text-white/60">
                  Just now
                </p>
              </div>
            </div>
          </div>

          {/* ── Chart Placeholder ─────────────────────────── */}
          <div className="mb-8 rounded-2xl border border-white/[0.08] bg-white/[0.02] p-5">
            <p className="mb-3 text-[10px] font-medium uppercase tracking-widest text-white/25">
              Price History
            </p>
            <div className="relative h-48 rounded-xl border border-white/[0.06] bg-black p-3">
              <svg
                className="h-full w-full"
                viewBox="0 0 400 150"
                preserveAspectRatio="none"
              >
                {/* Grid lines */}
                {[0, 1, 2, 3].map((i) => (
                  <line
                    key={i}
                    x1="0"
                    y1={i * 37.5}
                    x2="400"
                    y2={i * 37.5}
                    stroke="rgba(255,255,255,0.05)"
                    strokeWidth="0.5"
                  />
                ))}
                {/* Probability line */}
                <polyline
                  fill="none"
                  stroke="rgba(255,255,255,0.6)"
                  strokeWidth="2"
                  strokeLinejoin="round"
                  points={history
                    .map((p, i) => {
                      const x = (i / (history.length - 1)) * 400;
                      const y =
                        140 - ((p - minProb) / probRange) * 120;
                      return `${x},${y}`;
                    })
                    .join(" ")}
                />
                {/* Area fill */}
                <polyline
                  fill="rgba(255,255,255,0.04)"
                  stroke="none"
                  points={[
                    ...history.map((p, i) => {
                      const x = (i / (history.length - 1)) * 400;
                      const y =
                        140 - ((p - minProb) / probRange) * 120;
                      return `${x},${y}`;
                    }),
                    "400,150",
                    "0,150",
                  ].join(" ")}
                />
                {/* Current dot */}
                {(() => {
                  const last = history[history.length - 1];
                  const y = 140 - ((last - minProb) / probRange) * 120;
                  return (
                    <circle
                      cx="400"
                      cy={y}
                      r="4"
                      fill="white"
                    />
                  );
                })()}
              </svg>
              {/* Y-axis labels */}
              <div className="pointer-events-none absolute inset-y-0 left-3 flex flex-col justify-between py-2">
                <span className="font-mono text-[9px] text-white/30">
                  {(maxProb * 100).toFixed(0)}%
                </span>
                <span className="font-mono text-[9px] text-white/30">
                  {(minProb * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-[10px] text-white/25">
                <span className="inline-block h-0.5 w-4 bg-white/40" />{" "}
                YES probability over time
              </span>
            </div>
          </div>

          {/* ── Market Info ───────────────────────────────── */}
          <div className="mb-8 rounded-2xl border border-white/[0.08] bg-white/[0.02] p-5">
            <p className="mb-4 text-[10px] font-medium uppercase tracking-widest text-white/25">
              Market Info
            </p>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="mb-1 text-[10px] text-white/25">Resolution</p>
                <p className="text-[15px] leading-relaxed text-white/60">
                  {detail.resolution}
                </p>
              </div>
              <div>
                <p className="mb-1 text-[10px] text-white/25">End Date</p>
                <p className="font-mono text-[15px] tabular-nums text-white">
                  {detail.endDate}
                </p>
              </div>
              <div>
                <p className="mb-1 text-[10px] text-white/25">Category</p>
                <p className="text-[15px] text-white">{detail.category}</p>
              </div>
            </div>
            {detail.description && (
              <div className="mt-4 border-t border-white/[0.06] pt-4">
                <p className="text-[15px] leading-relaxed text-white/60">
                  {detail.description}
                </p>
              </div>
            )}
          </div>

          {/* ── CTA ──────────────────────────────────────── */}
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6">
            <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-[15px] font-semibold text-white">
                  Ready to trade this market?
                </p>
                <p className="mt-1 text-xs text-white/40">
                  Current odds:{" "}
                  <span className="font-mono tabular-nums text-white/60">
                    {market.probability}% {market.yesLabel}
                  </span>{" "}
                  · Volume{" "}
                  <span className="font-mono tabular-nums text-white/60">
                    {market.volume}
                  </span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  href="/login"
                  className="rounded-full border border-white/15 px-5 py-2.5 text-[15px] font-medium text-white/60 transition-all hover:border-white/30 hover:text-white"
                >
                  Login to Trade
                </Link>
                <Link
                  href="/register"
                  className="rounded-full bg-white px-5 py-2.5 text-[15px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
                >
                  Trade Now →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
