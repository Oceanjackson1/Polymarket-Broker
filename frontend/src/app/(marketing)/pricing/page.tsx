import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Pricing — Free, Pro & Enterprise Plans",
  description:
    "Start free with 500 API calls/day. Upgrade to Pro at $99/mo for unlimited access to exclusive NBA fusion data, AI analysis, and automated strategies.",
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "Product",
  name: "Polymarket Broker",
  description:
    "Institutional-grade prediction market trading platform with exclusive data feeds and AI analysis.",
  offers: [
    {
      "@type": "Offer",
      name: "Free",
      price: "0",
      priceCurrency: "USD",
      description:
        "500 API calls/day, +10 bps broker fee, 10 AI analyses/day, no strategies, no webhooks.",
    },
    {
      "@type": "Offer",
      name: "Pro",
      price: "99",
      priceCurrency: "USD",
      priceSpecification: {
        "@type": "UnitPriceSpecification",
        billingDuration: "P1M",
      },
      description:
        "Unlimited API calls, +5 bps broker fee, unlimited AI analyses, strategies, webhooks.",
    },
    {
      "@type": "Offer",
      name: "Enterprise",
      description:
        "Custom pricing, unlimited API calls, custom broker fee, unlimited AI analyses, strategies, webhooks.",
    },
  ],
};

const tiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Get started with core access and explore the platform.",
    cta: "Get Started",
    ctaHref: "/dashboard",
    highlight: false,
    features: [
      { label: "API Calls / Day", value: "500" },
      { label: "Broker Fee", value: "+10 bps" },
      { label: "AI Analyses", value: "10 / day" },
      { label: "Automated Strategies", value: "No" },
      { label: "Webhooks", value: "No" },
    ],
  },
  {
    name: "Pro",
    price: "$99",
    period: "/ month",
    description:
      "Full access to exclusive data, AI analysis, and strategy automation.",
    cta: "Start Pro",
    ctaHref: "/dashboard",
    highlight: true,
    badge: "Most Popular",
    features: [
      { label: "API Calls / Day", value: "Unlimited" },
      { label: "Broker Fee", value: "+5 bps" },
      { label: "AI Analyses", value: "Unlimited" },
      { label: "Automated Strategies", value: "Yes" },
      { label: "Webhooks", value: "Yes" },
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    description:
      "Tailored infrastructure for institutions and high-volume traders.",
    cta: "Contact Sales",
    ctaHref: "mailto:sales@broker.polymarket.com",
    highlight: false,
    features: [
      { label: "API Calls / Day", value: "Unlimited" },
      { label: "Broker Fee", value: "Custom" },
      { label: "AI Analyses", value: "Unlimited" },
      { label: "Automated Strategies", value: "Yes" },
      { label: "Webhooks", value: "Yes" },
    ],
  },
];

export default function PricingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Header */}
      <section className="bg-black">
        <div className="mx-auto max-w-6xl px-6 py-24 text-center">
          <p className="mb-4 text-xs font-medium uppercase tracking-widest text-white/25">
            Plans
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-white md:text-5xl">
            Simple, transparent pricing
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-white/60">
            Start free — no credit card required. Upgrade when you need
            unlimited data, AI analysis, and strategy automation.
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="border-t border-white/[0.06] bg-black">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="grid gap-6 md:grid-cols-3">
            {tiers.map((tier, i) => (
              <div
                key={tier.name}
                className={`animate-fade-in stagger-${i + 1} relative flex flex-col rounded-2xl border p-8 ${
                  tier.highlight
                    ? "border-white/20 bg-white/[0.04]"
                    : "border-white/[0.08] bg-white/[0.02]"
                }`}
              >
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="rounded-full bg-white px-4 py-1 text-xs font-semibold text-black">
                      {tier.badge}
                    </span>
                  </div>
                )}

                {/* Tier Header */}
                <div className="mb-8">
                  <h2 className="text-lg font-semibold text-white">
                    {tier.name}
                  </h2>
                  <div className="mt-3 flex items-baseline gap-1.5">
                    <span className="text-5xl font-semibold text-white">
                      {tier.price}
                    </span>
                    {tier.period && (
                      <span className="text-sm text-white/40">
                        {tier.period}
                      </span>
                    )}
                  </div>
                  <p className="mt-3 text-[15px] leading-relaxed text-white/60">
                    {tier.description}
                  </p>
                </div>

                {/* Features */}
                <ul className="mb-8 flex-1 space-y-4">
                  {tier.features.map((feature) => (
                    <li
                      key={feature.label}
                      className="flex items-center justify-between border-b border-white/[0.06] pb-4 last:border-0 last:pb-0"
                    >
                      <span className="text-[15px] text-white/60">
                        {feature.label}
                      </span>
                      <span
                        className={`font-mono text-sm font-medium tabular-nums ${
                          feature.value === "No"
                            ? "text-white/25"
                            : "text-white"
                        }`}
                      >
                        {feature.value}
                      </span>
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                <Link
                  href={tier.ctaHref}
                  className={`block rounded-full px-6 py-3 text-center text-[15px] font-medium transition-all active:scale-[0.98] ${
                    tier.highlight
                      ? "bg-white text-black hover:bg-white/90"
                      : "border border-white/15 text-white hover:border-white/30 hover:bg-white/[0.04]"
                  }`}
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>

          {/* Note */}
          <p className="mt-12 text-center text-[15px] text-white/40">
            All plans include REST API access, WebSocket streams, and full
            OpenAPI documentation.{" "}
            <Link
              href="/docs"
              className="text-white/60 transition-colors hover:text-white"
            >
              Read the docs →
            </Link>
          </p>
        </div>
      </section>
    </>
  );
}
