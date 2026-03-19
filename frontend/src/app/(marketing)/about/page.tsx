import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About — Polydesk",
  description:
    "Polydesk is an institutional-grade prediction market terminal providing exclusive data feeds, AI-powered analysis, and automated convergence arbitrage strategies.",
};

const pillars = [
  {
    title: "Exclusive Data Feeds",
    description:
      "We source data that Polymarket itself does not provide: real-time NBA game scores fused with live market odds, 145-sport historical orderbooks, and BTC multi-timeframe prediction market probabilities combined with on-chain transaction data.",
  },
  {
    title: "AI Pricing-Bias Analysis",
    description:
      "Our DeepSeek-powered scanner continuously monitors all active markets for statistical pricing discrepancies. When a bias signal exceeds threshold, traders are notified immediately and can execute directly from the dashboard.",
  },
  {
    title: "Unified REST API",
    description:
      "Every feature available in the web terminal is also available via API. The same endpoints power our own dashboard and your custom systems — no hidden capabilities, no separate SDK required.",
  },
  {
    title: "Convergence Arbitrage",
    description:
      "Our strategies module identifies divergence between prediction market prices and real-world probability signals, then provides one-click execution to capture the spread as markets converge.",
  },
];

export default function AboutPage() {
  return (
    <>
      {/* Hero */}
      <section className="bg-black">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="max-w-3xl">
            <p className="mb-4 text-xs font-medium uppercase tracking-widest text-white/25">
              About
            </p>
            <h1 className="text-3xl font-semibold tracking-tight text-white md:text-5xl">
              Polydesk
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-white/60">
              An institutional-grade prediction market terminal built for
              traders who demand an edge. We aggregate proprietary data sources,
              apply AI-driven analysis, and expose everything through a clean
              REST API — so quantitative traders, funds, and serious retail
              participants can operate at professional standards.
            </p>
            <p className="mt-4 text-lg leading-relaxed text-white/60">
              Polymarket is the world&apos;s largest prediction market exchange.
              We are the infrastructure layer on top of it: the data feeds,
              analytics, and execution tooling that institutions need but the
              exchange itself does not offer.
            </p>
          </div>
        </div>
      </section>

      {/* Pillars */}
      <section className="border-t border-white/[0.06] bg-black">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <p className="mb-4 text-xs font-medium uppercase tracking-widest text-white/25">
            What We Build
          </p>
          <h2 className="mb-12 text-3xl font-semibold tracking-tight text-white md:text-5xl">
            Four pillars
          </h2>
          <div className="grid gap-6 md:grid-cols-2">
            {pillars.map((pillar) => (
              <div
                key={pillar.title}
                className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-8"
              >
                <h3 className="mb-3 text-xl font-semibold text-white">
                  {pillar.title}
                </h3>
                <p className="text-[15px] leading-relaxed text-white/60">
                  {pillar.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Principles + Contact */}
      <section className="border-t border-white/[0.06] bg-black">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="grid gap-16 md:grid-cols-2">
            <div>
              <p className="mb-4 text-xs font-medium uppercase tracking-widest text-white/25">
                Principles
              </p>
              <h2 className="mb-8 text-3xl font-semibold tracking-tight text-white">
                How we build
              </h2>
              <ul className="space-y-6">
                {[
                  {
                    title: "API-First",
                    body: "Every feature ships as an API endpoint before it ships as UI. We eat our own API.",
                  },
                  {
                    title: "No Hidden Fees",
                    body: "Broker fees are declared upfront in basis points. Free plan is +10 bps. Pro is +5 bps. Enterprise is negotiated.",
                  },
                  {
                    title: "Transparent Data Provenance",
                    body: "Every data point documents its source, refresh rate, and latency characteristics in the API response.",
                  },
                  {
                    title: "Terminal Aesthetic",
                    body: "Dark, dense, monospace where it matters. Designed for traders who work in it all day, not for marketing screenshots.",
                  },
                ].map((item) => (
                  <li key={item.title} className="flex gap-4">
                    <span className="mt-0.5 text-white/40">✓</span>
                    <div>
                      <p className="text-[15px] font-semibold text-white">
                        {item.title}
                      </p>
                      <p className="mt-1 text-[15px] leading-relaxed text-white/60">
                        {item.body}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="mb-4 text-xs font-medium uppercase tracking-widest text-white/25">
                Contact
              </p>
              <h2 className="mb-6 text-3xl font-semibold tracking-tight text-white">
                Get in touch
              </h2>
              <p className="text-[15px] leading-relaxed text-white/60">
                We&apos;re a small, focused team. If you&apos;re an institution
                that needs custom data arrangements, white-label access, or
                co-location, reach out directly.
              </p>
              <div className="mt-10 space-y-4">
                <Link
                  href="/docs"
                  className="block rounded-full border border-white/15 px-6 py-3 text-center text-[15px] font-medium text-white transition-all hover:border-white/30 hover:bg-white/[0.04]"
                >
                  Read the API Docs
                </Link>
                <Link
                  href="/pricing"
                  className="block rounded-full bg-white px-6 py-3 text-center text-[15px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
                >
                  View Pricing Plans
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
