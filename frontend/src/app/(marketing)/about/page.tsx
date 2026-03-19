import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About — Polymarket Broker",
  description:
    "Polymarket Broker is an institutional-grade prediction market terminal providing exclusive data feeds, AI-powered analysis, and automated convergence arbitrage strategies.",
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
      <section className="bg-bg-base">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="max-w-3xl">
            <h1 className="text-4xl font-bold tracking-tight text-text-primary md:text-5xl">
              About Polymarket Broker
            </h1>
            <p className="mt-6 text-lg leading-relaxed text-text-secondary">
              Polymarket Broker is an institutional-grade prediction market
              terminal built for traders who demand an edge. We aggregate
              proprietary data sources, apply AI-driven analysis, and expose
              everything through a clean REST API — so quantitative traders,
              funds, and serious retail participants can operate at professional
              standards.
            </p>
            <p className="mt-4 text-lg leading-relaxed text-text-secondary">
              Polymarket is the world's largest prediction market exchange. We
              are the infrastructure layer on top of it: the data feeds,
              analytics, and execution tooling that institutions need but the
              exchange itself does not offer.
            </p>
          </div>
        </div>
      </section>

      {/* Pillars */}
      <section className="border-t border-border-subtle bg-bg-card">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <h2 className="mb-12 text-2xl font-bold text-text-primary">
            What We Build
          </h2>
          <div className="grid gap-8 md:grid-cols-2">
            {pillars.map((pillar) => (
              <div
                key={pillar.title}
                className="rounded-xl border border-border-subtle bg-bg-base p-8"
              >
                <h3 className="mb-3 text-base font-semibold text-accent-gold">
                  {pillar.title}
                </h3>
                <p className="text-sm leading-relaxed text-text-secondary">
                  {pillar.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Principles */}
      <section className="border-t border-border-subtle bg-bg-base">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="grid gap-16 md:grid-cols-2">
            <div>
              <h2 className="mb-6 text-2xl font-bold text-text-primary">
                Design Principles
              </h2>
              <ul className="space-y-5">
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
                    <span className="mt-0.5 text-accent-gold">✓</span>
                    <div>
                      <p className="text-sm font-semibold text-text-primary">
                        {item.title}
                      </p>
                      <p className="mt-1 text-sm text-text-secondary">
                        {item.body}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h2 className="mb-6 text-2xl font-bold text-text-primary">
                Get In Touch
              </h2>
              <p className="text-sm leading-relaxed text-text-secondary">
                We're a small, focused team. If you're an institution that needs
                custom data arrangements, white-label access, or co-location,
                reach out directly.
              </p>
              <div className="mt-8 space-y-4">
                <Link
                  href="/docs"
                  className="block rounded-lg border border-border-default px-6 py-3 text-center text-sm font-semibold text-text-primary transition-colors hover:bg-bg-elevated"
                >
                  Read the API Docs
                </Link>
                <Link
                  href="/pricing"
                  className="block rounded-lg bg-accent-gold px-6 py-3 text-center text-sm font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover"
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
