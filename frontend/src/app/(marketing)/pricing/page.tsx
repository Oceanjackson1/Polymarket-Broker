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
      <section className="bg-bg-base">
        <div className="mx-auto max-w-7xl px-6 py-24 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-text-primary md:text-5xl">
            Simple, Transparent Pricing
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-text-secondary">
            Start free with no credit card required. Upgrade when you need
            unlimited data, AI analysis, and strategy automation.
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="border-t border-border-subtle bg-bg-card">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="grid gap-8 md:grid-cols-3">
            {tiers.map((tier) => (
              <div
                key={tier.name}
                className={`relative flex flex-col rounded-xl border p-8 ${
                  tier.highlight
                    ? "border-accent-gold bg-bg-base shadow-lg"
                    : "border-border-subtle bg-bg-base"
                }`}
              >
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="rounded-full bg-accent-gold px-4 py-1 text-xs font-semibold text-bg-base">
                      {tier.badge}
                    </span>
                  </div>
                )}

                {/* Tier Header */}
                <div className="mb-8">
                  <h2 className="text-lg font-semibold text-text-primary">
                    {tier.name}
                  </h2>
                  <div className="mt-3 flex items-baseline gap-1">
                    <span className="font-mono text-4xl font-bold text-text-primary">
                      {tier.price}
                    </span>
                    {tier.period && (
                      <span className="text-sm text-text-muted">
                        {tier.period}
                      </span>
                    )}
                  </div>
                  <p className="mt-3 text-sm text-text-secondary">
                    {tier.description}
                  </p>
                </div>

                {/* Features */}
                <ul className="mb-8 flex-1 space-y-4">
                  {tier.features.map((feature) => (
                    <li
                      key={feature.label}
                      className="flex items-center justify-between border-b border-border-subtle pb-4 last:border-0 last:pb-0"
                    >
                      <span className="text-sm text-text-secondary">
                        {feature.label}
                      </span>
                      <span
                        className={`font-mono text-sm font-medium ${
                          feature.value === "No"
                            ? "text-text-muted"
                            : "text-text-primary"
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
                  className={`block rounded-lg px-6 py-3 text-center text-sm font-semibold transition-colors ${
                    tier.highlight
                      ? "bg-accent-gold text-bg-base hover:bg-accent-gold-hover"
                      : "border border-border-default text-text-primary hover:bg-bg-elevated"
                  }`}
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>

          {/* FAQ / Note */}
          <p className="mt-12 text-center text-sm text-text-muted">
            All plans include REST API access, WebSocket streams, and full
            OpenAPI documentation.{" "}
            <Link
              href="/docs"
              className="text-accent-gold hover:text-accent-gold-hover"
            >
              Read the docs →
            </Link>
          </p>
        </div>
      </section>
    </>
  );
}
