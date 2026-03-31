import type { Metadata } from "next";
import Link from "next/link";
import { HeroSection, ExclusiveFeaturesGrid } from "./_components/hero-section";

export const metadata: Metadata = {
  title: "Polydesk — The Data Layer for Prediction Markets",
  description:
    "80+ API endpoints for prediction market data. Cross-platform arbitrage, real-time NBA fusion, BTC multi-timeframe predictions, 40+ bookmaker odds, weather ensemble forecasts, and AI pricing-bias analysis.",
  openGraph: {
    title: "Polydesk — The Data Layer for Prediction Markets",
    description:
      "The only API providing cross-platform arbitrage signals, NBA live fusion data, and AI pricing-bias analysis for Polymarket.",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Polydesk",
  applicationCategory: "FinanceApplication",
  operatingSystem: "Web",
  description: "API-first prediction market data platform for traders and developers.",
  offers: [
    { "@type": "Offer", name: "Free", price: "0", priceCurrency: "USD" },
    { "@type": "Offer", name: "Pro", price: "99", priceCurrency: "USD", billingIncrement: "P1M" },
  ],
};

const features = [
  {
    title: "Cross-Platform Arbitrage",
    description: "Real-time price spreads between Polymarket and Kalshi. Auto-detected opportunities with spread magnitude in basis points.",
    badge: "Exclusive",
    href: "/docs",
    isAI: false,
  },
  {
    title: "NBA Live Fusion",
    description: "ESPN live scores fused with Polymarket odds every 30 seconds. Bias signals detect mispricing as games unfold.",
    badge: "Exclusive",
    href: "/docs",
    isAI: false,
  },
  {
    title: "40+ Bookmaker Odds",
    description: "Aggregated odds from 40+ bookmakers across 12 sports. Compare implied probabilities against Polymarket prices to find edge.",
    badge: "Exclusive",
    href: "/docs",
    isAI: false,
  },
  {
    title: "BTC Multi-Timeframe",
    description: "Four prediction windows from 5 minutes to 4 hours. Fused with CoinGlass derivatives: funding rates, OI, liquidations.",
    badge: "Exclusive",
    href: "/docs",
    isAI: false,
  },
  {
    title: "Weather Ensemble Forecasts",
    description: "51-member ensemble forecasts for 20+ cities. Per-temperature-bin probability vs market price with bias signals.",
    badge: "Exclusive",
    href: "/docs",
    isAI: false,
  },
  {
    title: "AI Pricing Analysis",
    description: "DeepSeek-powered scanner finds the highest-magnitude mispricing across all markets. Ask questions in natural language.",
    badge: "AI",
    href: "/docs",
    isAI: true,
  },
];

const steps = [
  { n: "01", title: "Get Your API Key", desc: "Sign in with Google or connect your wallet. Get your API key in 30 seconds, start calling endpoints immediately." },
  { n: "02", title: "Access Exclusive Data", desc: "REST API and WebSocket streams for cross-platform spreads, live sports fusion, BTC predictions, and weather forecasts." },
  { n: "03", title: "Find Mispricing", desc: "Every data point comes with a bias signal in basis points. Filter by magnitude to focus on the highest-edge opportunities." },
  { n: "04", title: "Execute or Build", desc: "Trade directly via hosted or non-custodial orders. Or feed the data into your own models and execution systems." },
];

const useCases = [
  {
    persona: "Quant Traders",
    description: "Build automated strategies on cross-platform arbitrage signals. Backtest with historical spreads, execute via API.",
    example: "Polymarket vs Kalshi spread > 200bps \u2192 auto-execute convergence trade",
  },
  {
    persona: "Sports Bettors",
    description: "Compare 40+ bookmaker odds against Polymarket in real-time. Find mispriced events before the market corrects.",
    example: "Bookmaker consensus 72% vs Polymarket 65% \u2192 +700bps bias detected",
  },
  {
    persona: "Developers",
    description: "80+ endpoints, full OpenAPI spec, WebSocket streams. Build dashboards, bots, or analytics tools on top of our data.",
    example: "One API call returns score + odds + bias signal \u2192 build your own alerts",
  },
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
              <span className="text-white/30">Cannot Provide</span>
            </h2>
            <p className="mt-6 text-[17px] text-white/40">
              We fuse multiple external sources with Polymarket prices to compute bias signals you can&apos;t get anywhere else.
            </p>
          </div>
          <ExclusiveFeaturesGrid features={features} />
        </div>
      </section>

      {/* ═══ Divider ═══ */}
      <div className="mx-auto h-px max-w-5xl bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      {/* ═══ Who is this for ═══ */}
      <section className="bg-black py-32">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mx-auto mb-20 max-w-2xl text-center">
            <p className="mb-4 text-sm font-medium tracking-widest text-white/30">
              BUILT FOR
            </p>
            <h2 className="text-4xl font-semibold tracking-tight text-white md:text-6xl">
              Traders, Bettors
              <br />
              <span className="text-white/30">& Developers</span>
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {useCases.map((uc) => (
              <div
                key={uc.persona}
                className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8"
              >
                <h3 className="mb-3 text-lg font-semibold text-white">{uc.persona}</h3>
                <p className="text-[15px] leading-relaxed text-white/40">{uc.description}</p>
                <div className="mt-6 rounded-xl bg-white/[0.03] px-4 py-3">
                  <p className="font-mono text-[13px] leading-relaxed text-white/30">{uc.example}</p>
                </div>
              </div>
            ))}
          </div>
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
              Start In Minutes
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
        <div className="mx-auto grid max-w-5xl grid-cols-2 gap-8 px-6 md:grid-cols-5">
          {[
            { v: "80+", l: "API Endpoints" },
            { v: "40+", l: "Bookmakers" },
            { v: "12", l: "Sports Covered" },
            { v: "20+", l: "Weather Cities" },
            { v: "24/7", l: "Data Collection" },
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
                API First
                <br />
                <span className="text-white/30">By Design</span>
              </h2>
              <p className="mt-6 text-[17px] leading-relaxed text-white/50">
                Our own console calls the same API you do.
                Every endpoint, every feature, identical access.
              </p>
              <ul className="mt-10 space-y-5">
                {[
                  "REST API + WebSocket real-time streams",
                  "Google + MetaMask + OKX Wallet authentication",
                  "Hosted and non-custodial order modes",
                  "Full OpenAPI specification",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-4 text-[15px] text-white/50">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white/[0.06] text-xs text-white/60">{"\u2713"}</span>
                    {item}
                  </li>
                ))}
              </ul>
              <div className="mt-10 flex gap-4">
                <Link
                  href="/docs"
                  className="rounded-full bg-white px-7 py-3 text-[15px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
                >
                  API Docs
                </Link>
                <Link
                  href="/login"
                  className="rounded-full border border-white/15 px-7 py-3 text-[15px] font-medium text-white transition-all hover:border-white/30"
                >
                  Get API Key
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
                  <span className="text-white/25"># Cross-platform arbitrage scan</span>{"\n"}
                  <span className="text-white">spreads</span> = requests.<span className="text-blue-400">get</span>({"\n"}
                  {"  "}<span className="text-emerald-400">&quot;/api/v1/data/dome/arbitrage/spreads&quot;</span>,{"\n"}
                  {"  "}headers={"{"}<span className="text-emerald-400">&quot;X-API-Key&quot;</span>: key{"}"},{"\n"}
                  {"  "}params={"{"}<span className="text-emerald-400">&quot;min_spread_bps&quot;</span>: <span className="text-purple-400">100</span>{"}"}{"\n"}
                  ).json(){"\n\n"}
                  <span className="text-white/25"># High spread found, execute trade</span>{"\n"}
                  <span className="text-blue-400">for</span> opp <span className="text-blue-400">in</span> spreads[<span className="text-emerald-400">&quot;data&quot;</span>]:{"\n"}
                  {"  "}<span className="text-blue-400">if</span> opp[<span className="text-emerald-400">&quot;spread_bps&quot;</span>] &gt; <span className="text-purple-400">200</span>:{"\n"}
                  {"    "}place_order(opp[<span className="text-emerald-400">&quot;polymarket_slug&quot;</span>])
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
            Find Edge Others Miss
          </h2>
          <p className="mt-6 text-[17px] text-white/50">
            Free tier, no credit card, 500 API calls per day.
            <br />
            Start receiving cross-platform arbitrage signals in minutes.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/login"
              className="rounded-full bg-white px-10 py-4 text-base font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
            >
              Get Started Free
            </Link>
            <Link
              href="/docs"
              className="rounded-full border border-white/15 px-10 py-4 text-base font-medium text-white transition-all hover:border-white/30"
            >
              View API Docs
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
