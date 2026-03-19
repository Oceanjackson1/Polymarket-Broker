import type { Metadata } from "next";
import Link from "next/link";
import { HeroSection, ExclusiveFeaturesGrid } from "./_components/hero-section";

export const metadata: Metadata = {
  title: "Polymarket Broker — Institutional Prediction Market Terminal",
  description:
    "Trade prediction markets with institutional-grade tools. Real-time NBA fusion data, 145-sport orderbooks, BTC multi-timeframe predictions, and AI pricing-bias analysis.",
  openGraph: {
    title: "Polymarket Broker — Institutional Prediction Market Terminal",
    description:
      "The only broker providing NBA×Polymarket real-time fusion data, AI pricing-bias analysis, and convergence arbitrage execution.",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Polymarket Broker",
  applicationCategory: "FinanceApplication",
  operatingSystem: "Web",
  description: "Institutional-grade prediction market trading platform.",
  offers: [
    { "@type": "Offer", name: "Free", price: "0", priceCurrency: "USD" },
    { "@type": "Offer", name: "Pro", price: "99", priceCurrency: "USD", billingIncrement: "P1M" },
  ],
};

const features = [
  {
    title: "NBA Live Fusion",
    description: "Real-time ESPN scores fused with Polymarket odds. AI-powered bias signals detect mispricing as it happens.",
    badge: "Exclusive",
    href: "/docs/guides/nba-fusion-trading",
    isAI: false,
  },
  {
    title: "145-Sport Orderbooks",
    description: "Full historical order book data across NBA, NFL, UFC, CS2 and 141 more sport and esport categories.",
    badge: "Exclusive",
    href: "/docs/guides/sports-orderbooks",
    isAI: false,
  },
  {
    title: "BTC Multi-Timeframe",
    description: "Four prediction timeframes from 5 minutes to 4 hours. On-chain trade data with millisecond precision.",
    badge: "Exclusive",
    href: "/docs/guides/btc-multiframe",
    isAI: false,
  },
  {
    title: "AI Pricing Analysis",
    description: "DeepSeek-powered market scanner. Automatically surfaces the highest-magnitude pricing bias opportunities across all markets.",
    badge: "AI",
    href: "/docs/api-reference/analysis",
    isAI: true,
  },
];

const steps = [
  { n: "01", title: "Create API Key", desc: "Register in 30 seconds. Get your API key instantly. Two auth paths: API Key or Ethereum wallet." },
  { n: "02", title: "Access Exclusive Data", desc: "REST API and WebSocket streams for NBA fusion, BTC predictions, and 145 sport orderbooks." },
  { n: "03", title: "Discover Opportunities", desc: "AI engine scans every market for pricing bias. Get alerted when magnitude exceeds your threshold." },
  { n: "04", title: "Execute Trades", desc: "One-click hosted orders or non-custodial local signing. Convergence arbitrage runs automatically." },
];

export default function LandingPage() {
  return (
    <div className="bg-black">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* ═══ Hero + Bento ═══ */}
      <HeroSection />

      {/* ═══ Divider ═══ */}
      <div className="mx-auto h-px max-w-5xl bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      {/* ═══ Features ═══ */}
      <section className="bg-black py-32">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto mb-20 max-w-2xl text-center">
            <p className="mb-4 text-sm font-medium tracking-widest text-white/30">
              WHAT SETS US APART
            </p>
            <h2 className="text-4xl font-semibold tracking-tight text-white md:text-6xl">
              Data Polymarket
              <br />
              <span className="text-white/30">cannot provide</span>
            </h2>
          </div>
          <ExclusiveFeaturesGrid features={features} />
        </div>
      </section>

      {/* ═══ Divider ═══ */}
      <div className="mx-auto h-px max-w-5xl bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      {/* ═══ How it works ═══ */}
      <section className="bg-black py-32">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto mb-20 max-w-2xl text-center">
            <p className="mb-4 text-sm font-medium tracking-widest text-white/30">
              HOW IT WORKS
            </p>
            <h2 className="text-4xl font-semibold tracking-tight text-white md:text-6xl">
              Start in minutes
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-4">
            {steps.map((s, i) => (
              <div
                key={s.n}
                className={`animate-fade-in stagger-${i + 1} rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8`}
              >
                <span className="mb-6 block font-mono text-4xl font-bold text-white/[0.07]">
                  {s.n}
                </span>
                <h3 className="mb-3 text-lg font-semibold text-white">{s.title}</h3>
                <p className="text-sm leading-relaxed text-white/40">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ Divider ═══ */}
      <div className="mx-auto h-px max-w-5xl bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      {/* ═══ Stats ═══ */}
      <section className="bg-black py-24">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 px-6 md:grid-cols-4">
          {[
            { v: "145+", l: "Sports & Esports" },
            { v: "<30ms", l: "API Latency" },
            { v: "24/7", l: "Data Collection" },
            { v: "4", l: "BTC Timeframes" },
          ].map((s) => (
            <div key={s.l} className="text-center">
              <p className="font-mono text-4xl font-semibold text-white">{s.v}</p>
              <p className="mt-2 text-sm text-white/30">{s.l}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ Divider ═══ */}
      <div className="mx-auto h-px max-w-5xl bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      {/* ═══ API / Developer ═══ */}
      <section className="bg-black py-32">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid items-center gap-20 md:grid-cols-2">
            <div>
              <p className="mb-4 text-sm font-medium tracking-widest text-white/30">
                DEVELOPER EXPERIENCE
              </p>
              <h2 className="text-4xl font-semibold tracking-tight text-white md:text-6xl">
                API first
                <br />
                <span className="text-white/30">by design</span>
              </h2>
              <p className="mt-6 text-[17px] leading-relaxed text-white/50">
                Our own dashboard calls the same API you do.
                Every endpoint, every feature, identical access
              </p>
              <ul className="mt-10 space-y-5">
                {[
                  "REST API + WebSocket real-time streams",
                  "API Key + Ethereum wallet authentication",
                  "Hosted and non-custodial order modes",
                  "Full OpenAPI specification",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-4 text-[15px] text-white/50">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white/[0.06] text-xs text-white/60">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
              <div className="mt-10 flex gap-4">
                <Link
                  href="/docs/getting-started/quickstart"
                  className="rounded-full bg-white px-7 py-3 text-[15px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
                >
                  Quick Start
                </Link>
                <Link
                  href="/docs"
                  className="rounded-full border border-white/15 px-7 py-3 text-[15px] font-medium text-white transition-all hover:border-white/30"
                >
                  Full Docs
                </Link>
              </div>
            </div>
            <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a]">
              <div className="flex items-center gap-2 border-b border-white/[0.06] px-5 py-3">
                <div className="flex gap-1.5">
                  <div className="h-3 w-3 rounded-full bg-[#ff5f57]" />
                  <div className="h-3 w-3 rounded-full bg-[#febc2e]" />
                  <div className="h-3 w-3 rounded-full bg-[#28c840]" />
                </div>
                <span className="ml-3 text-xs text-white/30">quickstart.py</span>
              </div>
              <pre className="p-6 text-[13px] leading-7">
                <code>
                  <span className="text-blue-400">import</span> <span className="text-white">requests</span>{"\n\n"}
                  <span className="text-white/25"># One call to get score, odds, bias signal</span>{"\n"}
                  <span className="text-white">r</span> = requests.<span className="text-blue-400">get</span>({"\n"}
                  {"  "}<span className="text-emerald-400">&quot;/api/v1/data/nba/games/gsw-lal/fusion&quot;</span>,{"\n"}
                  {"  "}headers={"{"}<span className="text-emerald-400">&quot;X-API-Key&quot;</span>: key{"}"}{"\n"}
                  ){"\n\n"}
                  <span className="text-white/25"># Bias detected, execute trade</span>{"\n"}
                  <span className="text-blue-400">if</span> r.json()[<span className="text-emerald-400">&quot;magnitude_bps&quot;</span>] &gt; <span className="text-purple-400">300</span>:{"\n"}
                  {"  "}place_order(<span className="text-emerald-400">&quot;BUY&quot;</span>, size=<span className="text-purple-400">100</span>)
                </code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="relative bg-black py-32">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        <div className="mx-auto max-w-2xl px-6 text-center">
          <h2 className="text-4xl font-semibold tracking-tight text-white md:text-6xl">
            Ready to start
          </h2>
          <p className="mt-6 text-[17px] text-white/50">
            Free tier, no credit card, 500 API calls per day
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="rounded-full bg-white px-10 py-4 text-base font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
            >
              Get started free
            </Link>
            <Link
              href="/pricing"
              className="rounded-full border border-white/15 px-10 py-4 text-base font-medium text-white transition-all hover:border-white/30"
            >
              View pricing
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
