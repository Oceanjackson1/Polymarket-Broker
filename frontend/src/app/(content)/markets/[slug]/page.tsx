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
        <p className="text-text-muted">Market not found.</p>
        <Link
          href="/markets"
          className="mt-4 inline-block text-accent-gold hover:underline"
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

      <div className="min-h-screen bg-bg-base">
        {/* Back nav */}
        <div className="border-b border-border-subtle bg-bg-card">
          <div className="mx-auto max-w-4xl px-6 py-3">
            <Link
              href="/markets"
              className="text-xs text-text-muted transition-colors hover:text-text-secondary"
            >
              ← All Markets
            </Link>
          </div>
        </div>

        <div className="mx-auto max-w-4xl px-6 py-10">
          {/* ── Market Title + Probability ──────────────────── */}
          <div className="mb-8">
            <div className="mb-3 flex items-center gap-2">
              <span className="rounded bg-bg-card px-2 py-0.5 font-mono text-[10px] text-text-muted">
                {detail.category.toUpperCase()}
              </span>
            </div>
            <h1 className="mb-4 text-2xl font-bold leading-snug text-text-primary">
              {market.title}
            </h1>
            <div className="flex flex-wrap items-center gap-4">
              <AnimatedProbability probability={market.probability} yesLabel={market.yesLabel} />
              <div className="h-8 w-px bg-border-subtle" />
              <div>
                <p className="text-[10px] uppercase tracking-wider text-text-muted">
                  Volume
                </p>
                <p className="font-mono text-lg font-semibold text-text-primary">
                  {market.volume}
                </p>
              </div>
              <div className="h-8 w-px bg-border-subtle" />
              <div>
                <p className="text-[10px] uppercase tracking-wider text-text-muted">
                  Last Updated
                </p>
                <p className="font-mono text-sm text-text-secondary">
                  Just now
                </p>
              </div>
            </div>
          </div>

          {/* ── Chart Placeholder ─────────────────────────── */}
          <div className="mb-8 rounded-xl border border-border-subtle bg-bg-card p-5">
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Price History
            </p>
            <div className="relative h-48 rounded border border-border-subtle bg-bg-base p-3">
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
                    stroke="var(--border-subtle)"
                    strokeWidth="0.5"
                  />
                ))}
                {/* Probability line */}
                <polyline
                  fill="none"
                  stroke="var(--accent-gold)"
                  strokeWidth="2.5"
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
                  fill="var(--accent-gold)"
                  fillOpacity="0.08"
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
                      fill="var(--accent-gold)"
                    />
                  );
                })()}
              </svg>
              {/* Y-axis labels */}
              <div className="pointer-events-none absolute inset-y-0 left-3 flex flex-col justify-between py-2">
                <span className="font-mono text-[9px] text-text-muted">
                  {(maxProb * 100).toFixed(0)}%
                </span>
                <span className="font-mono text-[9px] text-text-muted">
                  {(minProb * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-[10px] text-text-muted">
                <span className="inline-block h-0.5 w-4 bg-accent-gold" />{" "}
                YES probability over time
              </span>
            </div>
          </div>

          {/* ── Market Info ───────────────────────────────── */}
          <div className="mb-8 rounded-xl border border-border-subtle bg-bg-card p-5">
            <p className="mb-4 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Market Info
            </p>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="mb-1 text-[10px] text-text-muted">Resolution</p>
                <p className="text-sm text-text-secondary">
                  {detail.resolution}
                </p>
              </div>
              <div>
                <p className="mb-1 text-[10px] text-text-muted">End Date</p>
                <p className="font-mono text-sm text-text-primary">
                  {detail.endDate}
                </p>
              </div>
              <div>
                <p className="mb-1 text-[10px] text-text-muted">Category</p>
                <p className="text-sm text-text-primary">{detail.category}</p>
              </div>
            </div>
            {detail.description && (
              <div className="mt-4 border-t border-border-subtle pt-4">
                <p className="text-sm leading-relaxed text-text-secondary">
                  {detail.description}
                </p>
              </div>
            )}
          </div>

          {/* ── CTA ──────────────────────────────────────── */}
          <div className="rounded-xl border border-accent-gold/20 bg-bg-card p-6">
            <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-text-primary">
                  Ready to trade this market?
                </p>
                <p className="mt-1 text-xs text-text-muted">
                  Current odds:{" "}
                  <span className="font-mono text-accent-gold">
                    {market.probability}% {market.yesLabel}
                  </span>{" "}
                  · Volume{" "}
                  <span className="font-mono text-text-secondary">
                    {market.volume}
                  </span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  href="/dashboard"
                  className="rounded-lg border border-border-default px-5 py-2.5 text-sm font-medium text-text-secondary transition-colors hover:border-accent-gold/40 hover:text-text-primary"
                >
                  Login to Trade
                </Link>
                <Link
                  href="/dashboard"
                  className="btn-premium rounded-lg bg-accent-gold px-5 py-2.5 text-sm font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover"
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
